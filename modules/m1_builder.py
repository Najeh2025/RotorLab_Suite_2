# modules/m1_builder.py — Constructeur de Rotor (Module M1)
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
# =============================================================================

import streamlit as st
import numpy as np
import pandas as pd
import json

try:
    import ross as rs
    ROSS_OK = True
except ImportError:
    ROSS_OK = False

from config import MATERIALS_DB, BEARING_PRESETS


# =============================================================================
# POINT D'ENTRÉE PRINCIPAL
# =============================================================================
def render_m1(col_settings, col_graphics):
    """Rendu du module M1 dans le layout 3 panneaux."""

    active_node = st.session_state.get("active_node", "shaft")

    with col_settings:
        _render_settings(active_node)

    with col_graphics:
        _render_graphics(active_node)


# =============================================================================
# PANNEAU SETTINGS (centre)
# =============================================================================
def _render_settings(active_node: str):
    st.markdown(
        '<div class="rl-settings-title">🏗️ Model Builder — Rotor Definition</div>',
        unsafe_allow_html=True
    )

    # ── Gestion fichiers ──────────────────────────────────────────────────
    with st.expander("📁 Fichiers — Charger / Sauvegarder", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📄 Nouveau modèle", use_container_width=True, key="m1_new"):
                _init_tables()
                st.rerun()
        with c2:
            current_data = {
                "shaft":    st.session_state["df_shaft"].to_dict(orient="records"),
                "disks":    st.session_state["df_disk"].to_dict(orient="records"),
                "bearings": st.session_state["df_bear"].to_dict(orient="records"),
                "material": st.session_state.get("mat_name",
                            "Acier standard (AISI 1045)"),
            }
            st.download_button(
                "💾 Sauvegarder (.json)",
                data=json.dumps(current_data, indent=2),
                file_name="rotor_model.json",
                mime="application/json",
                use_container_width=True,
                key="m1_save"
            )
        uploaded = st.file_uploader(
            "Charger un modele (.json)",
            type=["json"],
            label_visibility="collapsed",
            key="m1_upload"
        )
        if uploaded is not None:
            # Calcul d'un identifiant unique pour ce fichier
            file_id = "{}_{}".format(uploaded.name, uploaded.size)
            # Charger seulement si c'est un nouveau fichier
            if st.session_state.get("m1_last_file_id") != file_id:
                try:
                    import io
                    content = uploaded.read()
                    data    = json.loads(content.decode("utf-8"))

                    # Validation de la structure
                    if "shaft" not in data:
                        st.error("Fichier JSON invalide : clé 'shaft' manquante.")
                    else:
                        # 1. VIDER LE CACHE DES WIDGETS DATA_EDITOR
                        # Cela force les tableaux à oublier l'ancien modèle
                        for editor_key in ["m1_shaft_editor", "m1_disk_editor", "m1_bear_editor"]:
                            if editor_key in st.session_state:
                                del st.session_state[editor_key]

                        # 2. METTRE À JOUR LES DONNÉES
                        st.session_state["df_shaft"] = pd.DataFrame(data["shaft"])
                        st.session_state["df_disk"]  = pd.DataFrame(
                            data.get("disks", data.get("disk", [])))
                        st.session_state["df_bear"]  = pd.DataFrame(
                            data.get("bearings", data.get("bearing", [])))
                        st.session_state["mat_name"] = data.get(
                            "material", "Acier standard (AISI 1045)")
                        
                        # Invalider le rotor et les résultats
                        st.session_state["rotor"]      = None
                        st.session_state["rotor_name"] = data.get(
                            "name", uploaded.name.replace(".json", ""))
                        for key in ["res_static","res_modal","res_campbell",
                                    "res_ucs","res_unbalance","res_freq",
                                    "res_temporal"]:
                            st.session_state[key] = None
                            
                        # Marquer ce fichier comme déjà chargé
                        st.session_state["m1_last_file_id"] = file_id
                        st.success("Modèle '{}' chargé avec succès !".format(
                            st.session_state["rotor_name"]))
                        
                        # 3. FORCER L'ACTUALISATION DE L'INTERFACE
                        st.rerun()

                except json.JSONDecodeError as e:
                    st.error("Fichier JSON malformé : {}".format(e))
                except Exception as e:
                    st.error("Erreur lecture : {}".format(e))
            else:
                st.info("Fichier '{}' déjà chargé.".format(uploaded.name))

    st.markdown("---")

    # ── Onglets de paramétrage ────────────────────────────────────────────
    tab_mat, tab_shaft, tab_disk, tab_bear = st.tabs(
        ["🧱 Matériau", "📏 Arbre", "💿 Disques", "⚙️ Paliers"]
    )

    # ── MATÉRIAU ──────────────────────────────────────────────────────────
    with tab_mat:
        mat_name = st.selectbox(
            "Matériau :",
            list(MATERIALS_DB.keys()),
            index=list(MATERIALS_DB.keys()).index(
                st.session_state.get("mat_name",
                "Acier standard (AISI 1045)")
            ),
            key="m1_mat_select"
        )
        st.session_state["mat_name"] = mat_name
        props = MATERIALS_DB[mat_name]

        if mat_name == "Personnalisé":
            c1, c2, c3 = st.columns(3)
            with c1:
                props["rho"] = st.number_input(
                    "ρ (kg/m³)", 500.0, 20000.0,
                    float(props["rho"]), key="m1_rho")
            with c2:
                props["E"] = st.number_input(
                    "E (GPa)", 1.0, 500.0,
                    float(props["E"]) / 1e9, key="m1_E") * 1e9
            with c3:
                props["G_s"] = st.number_input(
                    "G_s (GPa)", 1.0, 200.0,
                    float(props["G_s"]) / 1e9, key="m1_Gs") * 1e9
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("ρ (kg/m³)", f"{props['rho']:.0f}")
            c2.metric("E (GPa)",   f"{props['E']/1e9:.1f}")
            c3.metric("G_s (GPa)", f"{props['G_s']/1e9:.1f}")

    # ── ARBRE ─────────────────────────────────────────────────────────────
    with tab_shaft:
        st.caption(
            "Éléments de poutre Timoshenko — L : longueur, id : Ø interne, "
            "od : Ø externe. _L = côté gauche, _R = côté droit (arbre conique)."
        )
        st.session_state["df_shaft"] = st.data_editor(
            st.session_state["df_shaft"],
            num_rows="dynamic",
            key="m1_shaft_editor",
            use_container_width=True,
            column_config={
                "L (m)":    st.column_config.NumberColumn(
                    "L (m)", min_value=0.001, format="%.4f"),
                "id_L (m)": st.column_config.NumberColumn(
                    "id_L (m)", min_value=0.0, format="%.4f"),
                "od_L (m)": st.column_config.NumberColumn(
                    "od_L (m)", min_value=0.001, format="%.4f"),
                "id_R (m)": st.column_config.NumberColumn(
                    "id_R (m)", min_value=0.0, format="%.4f"),
                "od_R (m)": st.column_config.NumberColumn(
                    "od_R (m)", min_value=0.001, format="%.4f"),
            }
        )
        n_el = len(st.session_state["df_shaft"])
        st.caption(f"→ {n_el} éléments · {n_el + 1} nœuds (0 → {n_el})")

    # ── DISQUES ───────────────────────────────────────────────────────────
    with tab_disk:
        st.caption(
            "Masses concentrées — saisie directe de masse et inerties "
            "(données CAO ou catalogue constructeur)."
        )
        st.session_state["df_disk"] = st.data_editor(
            st.session_state["df_disk"],
            num_rows="dynamic",
            key="m1_disk_editor",
            use_container_width=True,
            column_config={
                "nœud":       st.column_config.NumberColumn(
                    "Nœud", min_value=0, step=1),
                "Masse (kg)": st.column_config.NumberColumn(
                    "Masse (kg)", min_value=0.0, format="%.4f"),
                "Id (kg.m²)": st.column_config.NumberColumn(
                    "Id (kg.m²)", min_value=0.0, format="%.6f"),
                "Ip (kg.m²)": st.column_config.NumberColumn(
                    "Ip (kg.m²)", min_value=0.0, format="%.6f"),
            }
        )

    # ── PALIERS ───────────────────────────────────────────────────────────
    with tab_bear:
        c_pre, _ = st.columns([3, 5])
        with c_pre:
            preset = st.selectbox(
                "Preset :",
                ["-"] + list(BEARING_PRESETS.keys()),
                key="m1_preset"
            )
            if preset != "-":
                p    = BEARING_PRESETS[preset]
                n_el = max(1, len(st.session_state["df_shaft"]))
                st.session_state["df_bear"] = pd.DataFrame([
                    {"nœud": 0,   "Type": "Palier",
                     "kxx": p["kxx"], "kyy": p["kyy"], "kxy": p["kxy"],
                     "cxx": p["cxx"], "cyy": p["cyy"]},
                    {"nœud": n_el, "Type": "Palier",
                     "kxx": p["kxx"], "kyy": p["kyy"], "kxy": p["kxy"],
                     "cxx": p["cxx"], "cyy": p["cyy"]},
                ])

        st.session_state["df_bear"] = st.data_editor(
            st.session_state["df_bear"].fillna(0.0),
            num_rows="dynamic",
            key="m1_bear_editor",
            use_container_width=True,
            column_config={
                "Type": st.column_config.SelectboxColumn(
                    "Type",
                    options=["Palier", "Joint", "Roulement", "Masse"],
                    required=True
                ),
                "kxx": st.column_config.NumberColumn("kxx (N/m)",  format="%.2e"),
                "kyy": st.column_config.NumberColumn("kyy (N/m)",  format="%.2e"),
                "kxy": st.column_config.NumberColumn("kxy (N/m)",  format="%.2e"),
                "cxx": st.column_config.NumberColumn("cxx (N·s/m)",format="%.1f"),
                "cyy": st.column_config.NumberColumn("cyy (N·s/m)",format="%.1f"),
            }
        )
        st.caption(
            "💡 Type 'Masse' : ajoute une masse ponctuelle sans rigidité "
            "(capteur, demi-accouplement)."
        )

    st.markdown("---")

    # ── BOUTON ASSEMBLER ──────────────────────────────────────────────────
    if st.button("🚀 Assembler le rotor", type="primary",
                 key="m1_build", use_container_width=True):
        _assemble_rotor()


# =============================================================================
# PANNEAU GRAPHICS (droite)
# =============================================================================
def _render_graphics(active_node: str):
    st.markdown(
        '<div class="rl-graphics-title">'
        '🏗️ Rotor Geometry — 3D View'
        '</div>',
        unsafe_allow_html=True
    )

    rotor = st.session_state.get("rotor")

    if rotor is None:
        # ── État vide : guide de démarrage ──────────────────────────────
        st.markdown("""
        <div class="rl-card-info">
          <strong>🚀 Démarrage rapide</strong><br>
          <ol style="margin:6px 0 0 16px; font-size:0.9em;">
            <li>Sélectionnez un <strong>matériau</strong> (onglet Matériau)</li>
            <li>Définissez les <strong>éléments d'arbre</strong> (onglet Arbre)</li>
            <li>Ajoutez les <strong>disques</strong> (onglet Disques)</li>
            <li>Configurez les <strong>paliers</strong> (onglet Paliers)</li>
            <li>Cliquez sur <strong>🚀 Assembler le rotor</strong></li>
          </ol>
        </div>
        <div class="rl-card-info" style="margin-top:8px;">
          <strong>📂 Ou chargez directement :</strong><br>
          <small>Utilisez le bouton <em>📂 Charger compresseur</em> dans l'arbre
          de navigation (panneau gauche) pour charger le cas d'étude industriel
          de référence ROSS.</small>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Métriques globales ───────────────────────────────────────────────
    n_el = len(st.session_state["df_shaft"])
    L_total = sum(
        float(r.get("L (m)", 0))
        for r in st.session_state["df_shaft"].to_dict("records")
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"""
    <div class="rl-metric-card">
      <div class="rl-metric-label">Masse totale</div>
      <div class="rl-metric-value">{rotor.m:.2f}</div>
      <div class="rl-metric-unit">kg</div>
    </div>""", unsafe_allow_html=True)
    c2.markdown(f"""
    <div class="rl-metric-card">
      <div class="rl-metric-label">Nœuds</div>
      <div class="rl-metric-value">{len(rotor.nodes)}</div>
      <div class="rl-metric-unit">{n_el} éléments</div>
    </div>""", unsafe_allow_html=True)
    c3.markdown(f"""
    <div class="rl-metric-card">
      <div class="rl-metric-label">Longueur</div>
      <div class="rl-metric-value">{L_total:.3f}</div>
      <div class="rl-metric-unit">m</div>
    </div>""", unsafe_allow_html=True)
    
    # Récupération exacte des DDL depuis le moteur ROSS
    n_noeuds = len(rotor.nodes)
    ddl_total = rotor.ndof

    # Récupération exacte des DDL depuis le moteur ROSS
    ddl_total = rotor.ndof 

    c4.markdown("""
    <div class="rl-metric-card">
      <div class="rl-metric-label">DDL total</div>
      <div class="rl-metric-value">{}</div>
      <div class="rl-metric-unit">Valeur calculée par ROSS</div>
    </div>""".format(ddl_total), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Visualisation 3D ─────────────────────────────────────────────────
    try:
        fig = rotor.plot_rotor()
        fig.update_layout(height=420, margin=dict(l=0, r=0, t=30, b=0))
        
        # 1. Utilisation d'une clé dynamique pour forcer le rafraîchissement visuel
        plot_key = f"m1_3d_plot_{id(rotor)}"
        st.plotly_chart(fig, use_container_width=True, key=plot_key)
        
    except Exception as e:
        # 2. Message d'erreur explicite si la géométrie plante
        st.error(f"❌ Impossible d'afficher le modèle 3D. Vérifiez la cohérence de vos nœuds (ex: un disque/palier placé sur un nœud inexistant). Détail technique : {e}")

    # 3. On sépare l'export Kaleido (qui est fragile) pour qu'il ne bloque pas l'affichage
    try:
        if 'fig' in locals():
            import kaleido  # noqa
            st.session_state["img_rotor"] = fig.to_image(
                format="png", width=700, height=400)
    except Exception:
        pass
    # ── Tableau récapitulatif des éléments ───────────────────────────────
    with st.expander("📋 Récapitulatif du modèle", expanded=False):
        tab_s, tab_d, tab_b = st.tabs(["Arbre", "Disques", "Paliers"])
        with tab_s:
            st.dataframe(st.session_state["df_shaft"],
                         use_container_width=True, hide_index=True)
        with tab_d:
            st.dataframe(st.session_state["df_disk"],
                         use_container_width=True, hide_index=True)
        with tab_b:
            st.dataframe(st.session_state["df_bear"],
                         use_container_width=True, hide_index=True)

    # ── Export Excel ─────────────────────────────────────────────────────
    try:
        import io
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            st.session_state["df_shaft"].to_excel(
                writer, sheet_name="Arbre",   index=False)
            st.session_state["df_disk"].to_excel(
                writer, sheet_name="Disques", index=False)
            st.session_state["df_bear"].to_excel(
                writer, sheet_name="Paliers", index=False)
        st.download_button(
            "📥 Export Excel (.xlsx)",
            data=buf.getvalue(),
            file_name="rotor_parameters.xlsx",
            mime="application/vnd.openxmlformats-officedocument"
                 ".spreadsheetml.sheet",
            key="m1_excel"
        )
    except ModuleNotFoundError:
        st.caption("⚠️ xlsxwriter manquant — export Excel désactivé.")


# =============================================================================
# ASSEMBLAGE DU ROTOR (logique métier)
# =============================================================================
def _assemble_rotor():
    """Construit l'objet rs.Rotor depuis les tableaux de session."""
    if not ROSS_OK:
        st.error("❌ ROSS n'est pas installé.")
        return

    errors = []

    try:
        # ── Matériau ──────────────────────────────────────────────────────
        mat_name = st.session_state.get("mat_name", "Acier standard (AISI 1045)")
        props    = MATERIALS_DB[mat_name]
        mat = rs.Material(
            name  = mat_name.replace(" ", "_"),
            rho   = props["rho"],
            E     = props["E"],
            G_s   = props["G_s"]
        )

        # ── Arbre ─────────────────────────────────────────────────────────
        shaft = []
        for i, row in st.session_state["df_shaft"].iterrows():
            L   = float(row.get("L (m)",   0.2))
            idl = float(row.get("id_L (m)", 0.0))
            odl = float(row.get("od_L (m)", 0.05))
            idr = float(row.get("id_R (m)", idl))
            odr = float(row.get("od_R (m)", odl))
            if L <= 0:
                errors.append(f"Arbre élément {i+1} : L doit être > 0")
                continue
            if idl >= odl or idr >= odr:
                errors.append(f"Arbre élément {i+1} : id doit être < od")
                continue
            shaft.append(rs.ShaftElement(
                L=L, idl=idl, odl=odl, idr=idr, odr=odr, material=mat))

        if not shaft:
            errors.append("Aucun élément d'arbre valide.")

        # ── Disques ───────────────────────────────────────────────────────
        disks = []
        for i, row in st.session_state["df_disk"].iterrows():
            try:
                disks.append(rs.DiskElement(
                    n  = int(row["nœud"]),
                    m  = float(row["Masse (kg)"]),
                    Id = float(row["Id (kg.m²)"]),
                    Ip = float(row["Ip (kg.m²)"])
                ))
            except Exception as e:
                errors.append(f"Disque ligne {i+1} : {e}")

        # ── Paliers ───────────────────────────────────────────────────────
        bears = []
        for i, row in st.session_state["df_bear"].fillna(0.0).iterrows():
            try:
                n      = int(row["nœud"])
                e_type = str(row.get("Type", "Palier")).strip()

                def sv(v):
                    try:
                        return float(v) if v not in (None, "") else 0.0
                    except Exception:
                        return 0.0

                kxx = sv(row.get("kxx", 0))
                kyy = sv(row.get("kyy", 0))
                kxy = sv(row.get("kxy", 0))
                cxx = sv(row.get("cxx", 0))
                cyy = sv(row.get("cyy", 0))

                if e_type == "Masse":
                    m_val = sv(row.get("m (kg)", 0))
                    if m_val > 0:
                        disks.append(rs.DiskElement(
                            n=n, m=m_val, Id=0.0, Ip=0.0))
                elif e_type == "Joint":
                    bears.append(rs.SealElement(
                        n=n, kxx=kxx, kyy=kyy,
                        kxy=kxy, kyx=-kxy, cxx=cxx, cyy=cyy))
                elif e_type == "Roulement":
                    bears.append(rs.RollerBearingElement(
                        n=n, kxx=kxx, kyy=kyy,
                        kxy=kxy, kyx=-kxy, cxx=cxx, cyy=cyy))
                else:
                    bears.append(rs.BearingElement(
                        n=n, kxx=kxx, kyy=kyy,
                        kxy=kxy, kyx=-kxy, cxx=cxx, cyy=cyy))
            except Exception as e:
                errors.append(f"Palier ligne {i+1} : {e}")

        if not bears:
            errors.append("Aucun palier défini.")

        # ── Rapport d'erreurs ─────────────────────────────────────────────
        if errors:
            for err in errors:
                st.error(f"❌ {err}")
            return

        # ── Assemblage final ──────────────────────────────────────────────
        with st.spinner("Assemblage du modèle éléments finis…"):
            rotor = rs.Rotor(shaft, disks, bears)

        st.session_state["rotor"]        = rotor
        st.session_state["rotor_name"]   = "Rotor personnalisé"
        st.session_state["rotor_source"] = "custom"

        # Invalider les résultats précédents
        for key in ["res_static", "res_modal", "res_campbell",
                    "res_ucs", "res_unbalance", "res_freq", "res_temporal"]:
            st.session_state[key] = None

        # Log
        try:
            from app import add_log
            add_log(
                f"Rotor assemblé : {len(rotor.nodes)} nœuds, "
                f"{rotor.m:.2f} kg, {rotor.ndof} DDL", "ok")
        except ImportError:
            pass

        st.success(
            f"✅ Rotor assemblé — {len(rotor.nodes)} nœuds | "
            f"{rotor.m:.2f} kg | {rotor.ndof} DDL"
        )
        st.rerun()

    except Exception as e:
        st.error(f"❌ Erreur d'assemblage : {e}")
        import traceback
        st.code(traceback.format_exc(), language="python")


# =============================================================================
# INITIALISATION DES TABLEAUX PAR DÉFAUT
# =============================================================================
def _init_tables():
    """Réinitialise les tableaux M1 à leurs valeurs par défaut."""
    st.session_state["df_shaft"] = pd.DataFrame([
        {"L (m)": 0.20, "id_L (m)": 0.0, "od_L (m)": 0.05,
         "id_R (m)": 0.0, "od_R (m)": 0.05}
        for _ in range(5)
    ])
    st.session_state["df_disk"] = pd.DataFrame([
        {"nœud": 2, "Masse (kg)": 15.12,
         "Id (kg.m²)": 0.025, "Ip (kg.m²)": 0.047}
    ])
    st.session_state["df_bear"] = pd.DataFrame([
        {"nœud": 0, "Type": "Palier",
         "kxx": 1e6, "kyy": 1e6, "kxy": 0.0, "cxx": 0.0, "cyy": 0.0},
        {"nœud": 5, "Type": "Palier",
         "kxx": 1e6, "kyy": 1e6, "kxy": 0.0, "cxx": 0.0, "cyy": 0.0},
    ])
    st.session_state["rotor"]      = None
    st.session_state["rotor_name"] = "Nouveau rotor"
    for key in ["res_static", "res_modal", "res_campbell",
                "res_ucs", "res_unbalance", "res_freq", "res_temporal"]:
        st.session_state[key] = None
