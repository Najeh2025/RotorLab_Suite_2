# modules/m1_builder.py — Constructeur de Rotor (Module M1)
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
# v3.2 — Boutons taille uniforme + Popover pour templates
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
    active_node = st.session_state.get("active_node", "shaft")
    
    # Initialisation des flags UX
    if "m1_has_unsaved_changes" not in st.session_state:
        st.session_state["m1_has_unsaved_changes"] = False
    if "m1_show_template_selector" not in st.session_state:
        st.session_state["m1_show_template_selector"] = False
    if "m1_show_unsaved_dialog" not in st.session_state:
        st.session_state["m1_show_unsaved_dialog"] = False
    if "m1_pending_action" not in st.session_state:
        st.session_state["m1_pending_action"] = None
    
    with col_settings:
        _render_settings(active_node)
    with col_graphics:
        _render_graphics(active_node)
    
    # Gestion des dialogs/popover après le rendu principal
    _handle_modals()


# =============================================================================
# GESTION DES DIALOGS / POPOVER
# =============================================================================
def _handle_modals():
    """Gère l'affichage des confirmations et sélecteurs de template."""
    
    # ── Dialog : Confirmation modifications non sauvegardées ──────────────
    if st.session_state.get("m1_show_unsaved_dialog"):
        with st.expander("⚠️ Modifications non sauvegardées", expanded=True):
            st.warning("Le modèle actuel contient des modifications non enregistrées.")
            st.info("💡 Conseil : Exportez votre travail avant de créer un nouveau modèle.")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("💾 Sauvegarder", use_container_width=True, key="dlg_save"):
                    _trigger_save()
                    st.session_state["m1_show_unsaved_dialog"] = False
                    st.session_state["m1_show_template_selector"] = True
                    st.rerun()
            with c2:
                if st.button("❌ Abandonner & Appliquer", use_container_width=True, type="primary", key="dlg_abandon"):
                    action = st.session_state.get("m1_pending_action", "new_model")
                    st.session_state["m1_show_unsaved_dialog"] = False
                    st.session_state["m1_has_unsaved_changes"] = False
                    
                    if action == "apply_template":
                        _init_tables(template=st.session_state["m1_template_selector_main"])
                        st.toast("🎯 Template appliqué !", icon="✅")
                    else:
                        st.session_state["m1_show_template_selector"] = True
                        
                    st.session_state["m1_pending_action"] = None
                    st.rerun()
            with c3:
                if st.button("↩️ Annuler", use_container_width=True, key="dlg_cancel"):
                    st.session_state["m1_show_unsaved_dialog"] = False
                    st.rerun()
    
    # ── POPOVER : Sélecteur de template (fenêtre popup) ───────────────────
    if st.session_state.get("m1_show_template_selector"):
        # Utilisation de st.popover pour une fenêtre popup
        with st.popover("🆕 Nouveau modèle — Sélectionnez un template", use_container_width=True):
            st.markdown("### Choisissez une configuration de départ :")
            
            template = st.radio(
                "Template :",
                options=["empty", "simple", "industrial", "api684"],
                format_func=lambda x: {
                    "empty": "🔹 **Vide** — Arbre nu (construction from scratch)",
                    "simple": "🔹 **Simple** — Exemple pédagogique (5 éléments + 1 disque)",
                    "industrial": "🔹 **Industriel** — Rotor multi-étages (paramètres réalistes)",
                    "api684": "🔹 **API 684** — Rotor de référence pour validation normative"
                }[x],
                key="m1_template_choice_radio",
                index=1  # "simple" par défaut
            )
            
            # Aperçu du template sélectionné
            preview = _get_template_preview(template)
            st.markdown(f"""
            <div style="background:#F8F9FA;border-left:4px solid #1F5C8B;
                        padding:12px 16px;margin:16px 0;border-radius:0 8px 8px 0;">
                <strong>📋 Aperçu :</strong><br>
                {preview}
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Créer ce modèle", use_container_width=True, type="primary", key="dlg_create"):
                    _init_tables(template=st.session_state["m1_template_choice_radio"])
                    st.session_state["m1_show_template_selector"] = False
                    st.session_state["m1_has_unsaved_changes"] = False
                    st.toast(f"🎯 Template '{template}' chargé avec succès !", icon="✅")
                    st.rerun()
            with c2:
                if st.button("↩️ Annuler", use_container_width=True, key="dlg_cancel_t"):
                    st.session_state["m1_show_template_selector"] = False
                    st.rerun()


# =============================================================================
# PANNEAU SETTINGS
# =============================================================================

# =============================================================================
# REMPLACEZ dans modules/m1_builder.py :
#   • _render_settings
#   • _load_model_from_dict  (fonction helper à ajouter si absente)
#   • _init_tables           (version avec paramètre template=)
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
# _render_settings
# =============================================================================
def _render_settings(active_node: str):
    import streamlit.components.v1 as components

    # ── Script JS via iframe same-origin → accès DOM parent garanti ───────
    # window.parent.document pointe sur l'app Streamlit (même origine).
    # MutationObserver + debounce : styles persistants après chaque rerun.
    components.html("""
    <script>
    (function () {
        var PD;
        try { PD = window.parent.document; } catch (e) { return; }
        if (!PD) return;

        /* ── Style cible commun aux 3 boutons ─────────────────────────── */
        var S = {
            height:          '40px',
            minHeight:       '40px',
            padding:         '0 14px',
            border:          '1.5px solid #D1D5DB',
            borderRadius:    '8px',
            background:      '#FFFFFF',
            fontSize:        '14px',
            fontWeight:      '600',
            color:           '#1A1A2E',
            justifyContent:  'flex-start',
            boxShadow:       'none',
            display:         'flex',
            alignItems:      'center',
            width:           '100%',
            cursor:          'pointer',
            boxSizing:       'border-box',
            transition:      'border-color .15s, background .15s, color .15s'
        };

        /* ── Applique le style + hover sur un élément ─────────────────── */
        function style(el, extra, hoverContainer) {
            if (!el) return;
            Object.assign(el.style, S, extra || {});
            var tgt = hoverContainer || el;
            el.onmouseenter = function () {
                tgt.style.borderColor = '#1F5C8B';
                tgt.style.background  = '#EBF4FB';
                el.style.color        = '#1F5C8B';
                if (extra && extra.background !== undefined)
                    el.style.background = extra.background;
            };
            el.onmouseleave = function () {
                tgt.style.borderColor = '#D1D5DB';
                tgt.style.background  = '#FFFFFF';
                el.style.color        = '#1A1A2E';
                if (extra && extra.background !== undefined)
                    el.style.background = extra.background;
            };
        }

        /* ── Passe principale ─────────────────────────────────────────── */
        function run() {

            /* [A] st.button — "Appliquer ce template" */
            PD.querySelectorAll('[data-testid="stButton"] button').forEach(function (b) {
                if ((b.textContent || '').indexOf('Appliquer') !== -1) style(b);
            });

            /* [B] st.download_button — "Sauvegarder" */
            PD.querySelectorAll('[data-testid="stDownloadButton"] button').forEach(function (b) {
                if ((b.textContent || '').indexOf('Sauvegarder') !== -1) style(b);
            });

            /* [C] st.file_uploader — transformer en bouton identique */
            var dz = PD.querySelector('[data-testid="stFileUploaderDropzone"]');
            if (dz) {
                /* Masquer les instructions drag-and-drop */
                var instr = dz.querySelector('[data-testid="stFileUploaderDropzoneInstructions"]');
                if (instr) instr.style.display = 'none';

                /* Styler le conteneur dropzone */
                Object.assign(dz.style, {
                    height: '40px', minHeight: '40px', padding: '0',
                    border: '1.5px solid #D1D5DB', borderRadius: '8px',
                    background: '#FFFFFF', display: 'flex', alignItems: 'center',
                    boxSizing: 'border-box'
                });

                /* Bouton Browse interne */
                var btn = dz.querySelector('button');
                if (btn) {
                    /* Remplacer le texte "Browse files" */
                    var p = btn.querySelector('p');
                    if (p && p.textContent.indexOf('Charger') === -1) {
                        p.textContent = '📂  Charger un modèle (.json)';
                    }
                    /* Styler le bouton (transparent pour laisser dz gérer la bordure) */
                    style(btn, { border: 'none', background: 'transparent' }, dz);
                }
            }
        }

        /* ── Exécutions initiales (laisse le temps à Streamlit de rendre) */
        run();
        setTimeout(run, 150);
        setTimeout(run, 400);
        setTimeout(run, 800);

        /* ── Observer permanent : réappliquer après chaque rerun Streamlit */
        var debTimer;
        new MutationObserver(function () {
            clearTimeout(debTimer);
            debTimer = setTimeout(run, 80);
        }).observe(PD.body, { childList: true, subtree: true });

    }());
    </script>
    """, height=0, scrolling=False)

    # ── Masquer le micro-iframe généré par components.html ────────────────
    st.markdown("""
    <style>
    /* Supprime l'espace vide laissé par le composant JS invisible */
    .element-container:has(iframe[height="0"]) {
        height   : 0 !important;
        overflow : hidden !important;
        margin   : 0 !important;
        padding  : 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # TITRE
    # ══════════════════════════════════════════════════════════════════════
    st.markdown(
        '<div class="rl-settings-title">🏗️ Model Builder — Rotor Definition</div>',
        unsafe_allow_html=True
    )

    # ══════════════════════════════════════════════════════════════════════
    # BLOC FICHIERS
    # ══════════════════════════════════════════════════════════════════════
    st.markdown(
        '<p style="font-weight:700;margin:0 0 5px;color:#1A1A2E;'
        'font-size:.82em;text-transform:uppercase;letter-spacing:.05em;">'
        '🆕 Nouveau modèle</p>',
        unsafe_allow_html=True
    )

    # 1. Sélecteur de template
    template_choice = st.selectbox(
        "template",
        options=["simple", "industrial", "api684", "empty"],
        format_func=lambda x: {
            "simple":     "🔹 Simple (Pédagogique)",
            "industrial": "🔹 Industriel (Multi-étages)",
            "api684":     "🔹 API 684 (Référence normative)",
            "empty":      "🔹 Vide (Construction from scratch)",
        }[x],
        index=0,
        key="m1_template_selector_main",
        label_visibility="collapsed"
    )

    # 2. [A] Bouton Appliquer  ← stylé par le JS ci-dessus
    if st.button(
        "✅  Appliquer ce template",
        use_container_width=True,
        key="m1_btn_apply_template"
    ):
        if st.session_state.get("m1_has_unsaved_changes", False):
            st.session_state["m1_show_unsaved_dialog"] = True
            st.session_state["m1_pending_action"]       = "apply_template"
        else:
            _init_tables(template=template_choice)
            st.session_state["m1_has_unsaved_changes"] = False
            st.toast("🎯 Template appliqué !", icon="✅")
        st.rerun()

    # 3. [C] File uploader  ← transformé visuellement en bouton par le JS
    uploaded = st.file_uploader(
        "Charger",
        type=["json"],
        key="m1_upload_main",
        label_visibility="collapsed",
    )
    if uploaded is not None:
        file_id = f"{uploaded.name}_{uploaded.size}"
        if st.session_state.get("m1_last_file_id") != file_id:
            try:
                data = json.loads(uploaded.read().decode("utf-8"))
                if "shaft" not in data:
                    st.error("❌ Fichier invalide : clé 'shaft' manquante.")
                else:
                    _load_model_from_dict(data)
                    st.session_state["_df_shaft_live"] = st.session_state["df_shaft"].copy()
                    st.session_state["_df_disk_live"]  = st.session_state["df_disk"].copy()
                    st.session_state["_df_bear_live"]  = st.session_state["df_bear"].copy()
                    st.session_state["m1_data_gen"]    = \
                        st.session_state.get("m1_data_gen", 0) + 1
                    st.session_state["m1_last_file_id"]        = file_id
                    st.session_state["m1_has_unsaved_changes"] = False
                    st.success(f"✅ Modèle '{st.session_state['rotor_name']}' chargé !")
                    st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON malformé : {e}")
            except Exception as e:
                st.error(f"❌ Erreur : {e}")

    # 4. [B] Download button  ← stylé par le JS ci-dessus
    current_data = {
        "name":     st.session_state.get("rotor_name", "rotor_export"),
        "material": st.session_state.get("mat_name", "Acier standard (AISI 1045)"),
        "shaft":    st.session_state.get(
                        "_df_shaft_live",
                        st.session_state["df_shaft"]
                    ).to_dict(orient="records"),
        "disks":    st.session_state.get(
                        "_df_disk_live",
                        st.session_state["df_disk"]
                    ).to_dict(orient="records"),
        "bearings": st.session_state.get(
                        "_df_bear_live",
                        st.session_state["df_bear"]
                    ).to_dict(orient="records"),
    }
    st.download_button(
        label="💾  Sauvegarder le modèle (.json)",
        data=json.dumps(current_data, indent=2, ensure_ascii=False),
        file_name=f"{st.session_state.get('rotor_name', 'rotor_model')}.json",
        mime="application/json",
        use_container_width=True,
        key="m1_save_main",
        on_click=lambda: st.session_state.update(m1_has_unsaved_changes=False)
    )

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════
    # NAVIGATION ONGLETS
    # ══════════════════════════════════════════════════════════════════════
    _label_to_render = {
        "🧱 Matériau": _render_tab_material,
        "📏 Arbre":    _render_tab_shaft,
        "💿 Disques":  _render_tab_disk,
        "⚙️ Paliers":  _render_tab_bearing,
    }
    current = st.session_state.get("m1_tab_selector", "🧱 Matériau")
    _label_to_render.get(current, _render_tab_material)()

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════
    # BOUTON ASSEMBLER
    # ══════════════════════════════════════════════════════════════════════
    if st.button(
        "🚀 Assembler le rotor",
        type="primary",
        key="m1_build",
        use_container_width=True
    ):
        _assemble_rotor()


# =============================================================================
# _init_tables — version avec paramètre template=
# =============================================================================
def _init_tables(template: str = "simple"):
    """Initialise les tableaux selon le template choisi."""

    templates = {

        # ── Simple (pédagogique) ──────────────────────────────────────────
        "simple": {
            "shaft": [
                {"L (m)": 0.20, "id_L (m)": 0.0, "od_L (m)": 0.05,
                 "id_R (m)": 0.0, "od_R (m)": 0.05}
                for _ in range(5)
            ],
            "disk": [
                {"nœud": 2, "Masse (kg)": 15.12,
                 "Id (kg.m²)": 0.025, "Ip (kg.m²)": 0.047}
            ],
            "bear": [
                {"nœud": 0, "Type": "Palier",
                 "kxx": 1e6, "kyy": 1e6, "kxy": 0.0, "cxx": 0.0, "cyy": 0.0},
                {"nœud": 5, "Type": "Palier",
                 "kxx": 1e6, "kyy": 1e6, "kxy": 0.0, "cxx": 0.0, "cyy": 0.0},
            ],
            "name": "Rotor simple (pédagogique)",
        },

        # ── Industriel (multi-étages) ─────────────────────────────────────
        "industrial": {
            "shaft": [
                {"L (m)": 0.15, "id_L (m)": 0.0, "od_L (m)": 0.060,
                 "id_R (m)": 0.0, "od_R (m)": 0.060},
                {"L (m)": 0.10, "id_L (m)": 0.0, "od_L (m)": 0.080,
                 "id_R (m)": 0.0, "od_R (m)": 0.080},
                {"L (m)": 0.12, "id_L (m)": 0.0, "od_L (m)": 0.080,
                 "id_R (m)": 0.0, "od_R (m)": 0.080},
                {"L (m)": 0.12, "id_L (m)": 0.0, "od_L (m)": 0.080,
                 "id_R (m)": 0.0, "od_R (m)": 0.080},
                {"L (m)": 0.10, "id_L (m)": 0.0, "od_L (m)": 0.080,
                 "id_R (m)": 0.0, "od_R (m)": 0.080},
                {"L (m)": 0.15, "id_L (m)": 0.0, "od_L (m)": 0.060,
                 "id_R (m)": 0.0, "od_R (m)": 0.060},
            ],
            "disk": [
                {"nœud": 1, "Masse (kg)": 8.50,
                 "Id (kg.m²)": 0.015, "Ip (kg.m²)": 0.028},
                {"nœud": 3, "Masse (kg)": 22.30,
                 "Id (kg.m²)": 0.048, "Ip (kg.m²)": 0.091},
                {"nœud": 5, "Masse (kg)": 8.50,
                 "Id (kg.m²)": 0.015, "Ip (kg.m²)": 0.028},
            ],
            "bear": [
                {"nœud": 0, "Type": "Palier",
                 "kxx": 5e7, "kyy": 5e7, "kxy": 0.0, "cxx": 800.0, "cyy": 800.0},
                {"nœud": 6, "Type": "Palier",
                 "kxx": 5e7, "kyy": 5e7, "kxy": 0.0, "cxx": 800.0, "cyy": 800.0},
            ],
            "name": "Rotor industriel (multi-étages)",
        },

        # ── API 684 (référence normative) ──────────────────────────────────
        "api684": {
            "shaft": [
                {"L (m)": 0.254, "id_L (m)": 0.0, "od_L (m)": 0.0762,
                 "id_R (m)": 0.0, "od_R (m)": 0.0762},
                {"L (m)": 0.127, "id_L (m)": 0.0, "od_L (m)": 0.1016,
                 "id_R (m)": 0.0, "od_R (m)": 0.1016},
                {"L (m)": 0.152, "id_L (m)": 0.0, "od_L (m)": 0.1016,
                 "id_R (m)": 0.0, "od_R (m)": 0.1016},
                {"L (m)": 0.152, "id_L (m)": 0.0, "od_L (m)": 0.1016,
                 "id_R (m)": 0.0, "od_R (m)": 0.1016},
                {"L (m)": 0.127, "id_L (m)": 0.0, "od_L (m)": 0.1016,
                 "id_R (m)": 0.0, "od_R (m)": 0.1016},
                {"L (m)": 0.254, "id_L (m)": 0.0, "od_L (m)": 0.0762,
                 "id_R (m)": 0.0, "od_R (m)": 0.0762},
            ],
            "disk": [
                {"nœud": 2, "Masse (kg)": 32.70,
                 "Id (kg.m²)": 0.156, "Ip (kg.m²)": 0.243},
                {"nœud": 4, "Masse (kg)": 32.70,
                 "Id (kg.m²)": 0.156, "Ip (kg.m²)": 0.243},
            ],
            "bear": [
                {"nœud": 0, "Type": "Palier",
                 "kxx": 1.75e8, "kyy": 1.75e8, "kxy": 0.0,
                 "cxx": 2000.0, "cyy": 2000.0},
                {"nœud": 6, "Type": "Palier",
                 "kxx": 1.75e8, "kyy": 1.75e8, "kxy": 0.0,
                 "cxx": 2000.0, "cyy": 2000.0},
            ],
            "name": "Rotor référence API 684",
        },

        # ── Vide ──────────────────────────────────────────────────────────
        "empty": {
            "shaft": [],
            "disk":  [],
            "bear":  [],
            "name":  "Nouveau rotor",
        },
    }

    tpl = templates.get(template, templates["simple"])

    st.session_state["df_shaft"] = pd.DataFrame(tpl["shaft"]) \
        if tpl["shaft"] else pd.DataFrame(
            columns=["L (m)", "id_L (m)", "od_L (m)", "id_R (m)", "od_R (m)"])
    st.session_state["df_disk"]  = pd.DataFrame(tpl["disk"]) \
        if tpl["disk"] else pd.DataFrame(
            columns=["nœud", "Masse (kg)", "Id (kg.m²)", "Ip (kg.m²)"])
    st.session_state["df_bear"]  = pd.DataFrame(tpl["bear"]) \
        if tpl["bear"] else pd.DataFrame(
            columns=["nœud", "Type", "kxx", "kyy", "kxy", "cxx", "cyy"])

    # Synchroniser les versions _live
    st.session_state["_df_shaft_live"] = st.session_state["df_shaft"].copy()
    st.session_state["_df_disk_live"]  = st.session_state["df_disk"].copy()
    st.session_state["_df_bear_live"]  = st.session_state["df_bear"].copy()

    # Forcer la recréation des éditeurs
    st.session_state["m1_data_gen"] = \
        st.session_state.get("m1_data_gen", 0) + 1

    st.session_state["rotor_name"]          = tpl["name"]
    st.session_state["rotor"]               = None
    st.session_state["m1_has_unsaved_changes"] = False
    st.session_state["m1_preset_applied"]   = "-"

    for key in ["res_static", "res_modal", "res_campbell",
                "res_ucs", "res_unbalance", "res_freq", "res_temporal"]:
        st.session_state[key] = None
 
 
# =============================================================================
# HELPER — _load_model_from_dict
# Charge un dictionnaire JSON dans session_state (bases stables)
# =============================================================================
def _load_model_from_dict(data: dict):
    """Hydrate session_state depuis un dict JSON chargé."""
    # Effacer les clés d'éditeurs précédents pour forcer la recréation
    for editor_key in ["m1_shaft_editor", "m1_disk_editor", "m1_bear_editor"]:
        if editor_key in st.session_state:
            del st.session_state[editor_key]
 
    st.session_state["df_shaft"] = pd.DataFrame(data["shaft"])
    st.session_state["df_disk"]  = pd.DataFrame(
        data.get("disks", data.get("disk", [])))
    st.session_state["df_bear"]  = pd.DataFrame(
        data.get("bearings", data.get("bearing", [])))
    st.session_state["mat_name"] = data.get(
        "material", "Acier standard (AISI 1045)")
    st.session_state["rotor_name"] = data.get(
        "name", "Modèle importé")
 
    # Invalider les résultats de simulation
    for key in ["res_static", "res_modal", "res_campbell",
                "res_ucs", "res_unbalance", "res_freq", "res_temporal",
                "rotor"]:
        st.session_state[key] = None
 
 
# =============================================================================
# _init_tables — version avec paramètre template=
# =============================================================================
def _init_tables(template: str = "simple"):
    """Initialise les tableaux selon le template choisi."""
 
    templates = {
 
        # ── Simple (pédagogique) ──────────────────────────────────────────
        "simple": {
            "shaft": [
                {"L (m)": 0.20, "id_L (m)": 0.0, "od_L (m)": 0.05,
                 "id_R (m)": 0.0, "od_R (m)": 0.05}
                for _ in range(5)
            ],
            "disk": [
                {"nœud": 2, "Masse (kg)": 15.12,
                 "Id (kg.m²)": 0.025, "Ip (kg.m²)": 0.047}
            ],
            "bear": [
                {"nœud": 0, "Type": "Palier",
                 "kxx": 1e6, "kyy": 1e6, "kxy": 0.0, "cxx": 0.0, "cyy": 0.0},
                {"nœud": 5, "Type": "Palier",
                 "kxx": 1e6, "kyy": 1e6, "kxy": 0.0, "cxx": 0.0, "cyy": 0.0},
            ],
            "name": "Rotor simple (pédagogique)",
        },
 
        # ── Industriel (multi-étages) ─────────────────────────────────────
        "industrial": {
            "shaft": [
                {"L (m)": 0.15, "id_L (m)": 0.0, "od_L (m)": 0.060,
                 "id_R (m)": 0.0, "od_R (m)": 0.060},
                {"L (m)": 0.10, "id_L (m)": 0.0, "od_L (m)": 0.080,
                 "id_R (m)": 0.0, "od_R (m)": 0.080},
                {"L (m)": 0.12, "id_L (m)": 0.0, "od_L (m)": 0.080,
                 "id_R (m)": 0.0, "od_R (m)": 0.080},
                {"L (m)": 0.12, "id_L (m)": 0.0, "od_L (m)": 0.080,
                 "id_R (m)": 0.0, "od_R (m)": 0.080},
                {"L (m)": 0.10, "id_L (m)": 0.0, "od_L (m)": 0.080,
                 "id_R (m)": 0.0, "od_R (m)": 0.080},
                {"L (m)": 0.15, "id_L (m)": 0.0, "od_L (m)": 0.060,
                 "id_R (m)": 0.0, "od_R (m)": 0.060},
            ],
            "disk": [
                {"nœud": 1, "Masse (kg)": 8.50,
                 "Id (kg.m²)": 0.015, "Ip (kg.m²)": 0.028},
                {"nœud": 3, "Masse (kg)": 22.30,
                 "Id (kg.m²)": 0.048, "Ip (kg.m²)": 0.091},
                {"nœud": 5, "Masse (kg)": 8.50,
                 "Id (kg.m²)": 0.015, "Ip (kg.m²)": 0.028},
            ],
            "bear": [
                {"nœud": 0, "Type": "Palier",
                 "kxx": 5e7, "kyy": 5e7, "kxy": 0.0, "cxx": 800.0, "cyy": 800.0},
                {"nœud": 6, "Type": "Palier",
                 "kxx": 5e7, "kyy": 5e7, "kxy": 0.0, "cxx": 800.0, "cyy": 800.0},
            ],
            "name": "Rotor industriel (multi-étages)",
        },
 
        # ── API 684 (référence normative) ──────────────────────────────────
        "api684": {
            "shaft": [
                {"L (m)": 0.254, "id_L (m)": 0.0, "od_L (m)": 0.0762,
                 "id_R (m)": 0.0, "od_R (m)": 0.0762},
                {"L (m)": 0.127, "id_L (m)": 0.0, "od_L (m)": 0.1016,
                 "id_R (m)": 0.0, "od_R (m)": 0.1016},
                {"L (m)": 0.152, "id_L (m)": 0.0, "od_L (m)": 0.1016,
                 "id_R (m)": 0.0, "od_R (m)": 0.1016},
                {"L (m)": 0.152, "id_L (m)": 0.0, "od_L (m)": 0.1016,
                 "id_R (m)": 0.0, "od_R (m)": 0.1016},
                {"L (m)": 0.127, "id_L (m)": 0.0, "od_L (m)": 0.1016,
                 "id_R (m)": 0.0, "od_R (m)": 0.1016},
                {"L (m)": 0.254, "id_L (m)": 0.0, "od_L (m)": 0.0762,
                 "id_R (m)": 0.0, "od_R (m)": 0.0762},
            ],
            "disk": [
                {"nœud": 2, "Masse (kg)": 32.70,
                 "Id (kg.m²)": 0.156, "Ip (kg.m²)": 0.243},
                {"nœud": 4, "Masse (kg)": 32.70,
                 "Id (kg.m²)": 0.156, "Ip (kg.m²)": 0.243},
            ],
            "bear": [
                {"nœud": 0, "Type": "Palier",
                 "kxx": 1.75e8, "kyy": 1.75e8, "kxy": 0.0,
                 "cxx": 2000.0, "cyy": 2000.0},
                {"nœud": 6, "Type": "Palier",
                 "kxx": 1.75e8, "kyy": 1.75e8, "kxy": 0.0,
                 "cxx": 2000.0, "cyy": 2000.0},
            ],
            "name": "Rotor référence API 684",
        },
 
        # ── Vide ──────────────────────────────────────────────────────────
        "empty": {
            "shaft": [],
            "disk":  [],
            "bear":  [],
            "name":  "Nouveau rotor",
        },
    }
 
    tpl = templates.get(template, templates["simple"])
 
    st.session_state["df_shaft"] = pd.DataFrame(tpl["shaft"]) \
        if tpl["shaft"] else pd.DataFrame(
            columns=["L (m)", "id_L (m)", "od_L (m)", "id_R (m)", "od_R (m)"])
    st.session_state["df_disk"]  = pd.DataFrame(tpl["disk"]) \
        if tpl["disk"] else pd.DataFrame(
            columns=["nœud", "Masse (kg)", "Id (kg.m²)", "Ip (kg.m²)"])
    st.session_state["df_bear"]  = pd.DataFrame(tpl["bear"]) \
        if tpl["bear"] else pd.DataFrame(
            columns=["nœud", "Type", "kxx", "kyy", "kxy", "cxx", "cyy"])
 
    # Synchroniser les versions _live
    st.session_state["_df_shaft_live"] = st.session_state["df_shaft"].copy()
    st.session_state["_df_disk_live"]  = st.session_state["df_disk"].copy()
    st.session_state["_df_bear_live"]  = st.session_state["df_bear"].copy()
 
    # Forcer la recréation des éditeurs
    st.session_state["m1_data_gen"] = \
        st.session_state.get("m1_data_gen", 0) + 1
 
    st.session_state["rotor_name"]          = tpl["name"]
    st.session_state["rotor"]               = None
    st.session_state["m1_has_unsaved_changes"] = False
    st.session_state["m1_preset_applied"]   = "-"
 
    for key in ["res_static", "res_modal", "res_campbell",
                "res_ucs", "res_unbalance", "res_freq", "res_temporal"]:
        st.session_state[key] = None
 
 
# =============================================================================
# HELPER — _load_model_from_dict
# Charge un dictionnaire JSON dans session_state (bases stables)
# =============================================================================
def _load_model_from_dict(data: dict):
    """Hydrate session_state depuis un dict JSON chargé."""
    # Effacer les clés d'éditeurs précédents pour forcer la recréation
    for editor_key in ["m1_shaft_editor", "m1_disk_editor", "m1_bear_editor"]:
        if editor_key in st.session_state:
            del st.session_state[editor_key]
 
    st.session_state["df_shaft"] = pd.DataFrame(data["shaft"])
    st.session_state["df_disk"]  = pd.DataFrame(
        data.get("disks", data.get("disk", [])))
    st.session_state["df_bear"]  = pd.DataFrame(
        data.get("bearings", data.get("bearing", [])))
    st.session_state["mat_name"] = data.get(
        "material", "Acier standard (AISI 1045)")
    st.session_state["rotor_name"] = data.get(
        "name", "Modèle importé")
 
    # Invalider les résultats de simulation
    for key in ["res_static", "res_modal", "res_campbell",
                "res_ucs", "res_unbalance", "res_freq", "res_temporal",
                "rotor"]:
        st.session_state[key] = None
 
 
# =============================================================================
# _init_tables — version avec paramètre template=
# =============================================================================
def _init_tables(template: str = "simple"):
    """Initialise les tableaux selon le template choisi."""
 
    templates = {
 
        # ── Simple (pédagogique) ──────────────────────────────────────────
        "simple": {
            "shaft": [
                {"L (m)": 0.20, "id_L (m)": 0.0, "od_L (m)": 0.05,
                 "id_R (m)": 0.0, "od_R (m)": 0.05}
                for _ in range(5)
            ],
            "disk": [
                {"nœud": 2, "Masse (kg)": 15.12,
                 "Id (kg.m²)": 0.025, "Ip (kg.m²)": 0.047}
            ],
            "bear": [
                {"nœud": 0, "Type": "Palier",
                 "kxx": 1e6, "kyy": 1e6, "kxy": 0.0, "cxx": 0.0, "cyy": 0.0},
                {"nœud": 5, "Type": "Palier",
                 "kxx": 1e6, "kyy": 1e6, "kxy": 0.0, "cxx": 0.0, "cyy": 0.0},
            ],
            "name": "Rotor simple (pédagogique)",
        },
 
        # ── Industriel (multi-étages) ─────────────────────────────────────
        "industrial": {
            "shaft": [
                {"L (m)": 0.15, "id_L (m)": 0.0, "od_L (m)": 0.060,
                 "id_R (m)": 0.0, "od_R (m)": 0.060},
                {"L (m)": 0.10, "id_L (m)": 0.0, "od_L (m)": 0.080,
                 "id_R (m)": 0.0, "od_R (m)": 0.080},
                {"L (m)": 0.12, "id_L (m)": 0.0, "od_L (m)": 0.080,
                 "id_R (m)": 0.0, "od_R (m)": 0.080},
                {"L (m)": 0.12, "id_L (m)": 0.0, "od_L (m)": 0.080,
                 "id_R (m)": 0.0, "od_R (m)": 0.080},
                {"L (m)": 0.10, "id_L (m)": 0.0, "od_L (m)": 0.080,
                 "id_R (m)": 0.0, "od_R (m)": 0.080},
                {"L (m)": 0.15, "id_L (m)": 0.0, "od_L (m)": 0.060,
                 "id_R (m)": 0.0, "od_R (m)": 0.060},
            ],
            "disk": [
                {"nœud": 1, "Masse (kg)": 8.50,
                 "Id (kg.m²)": 0.015, "Ip (kg.m²)": 0.028},
                {"nœud": 3, "Masse (kg)": 22.30,
                 "Id (kg.m²)": 0.048, "Ip (kg.m²)": 0.091},
                {"nœud": 5, "Masse (kg)": 8.50,
                 "Id (kg.m²)": 0.015, "Ip (kg.m²)": 0.028},
            ],
            "bear": [
                {"nœud": 0, "Type": "Palier",
                 "kxx": 5e7, "kyy": 5e7, "kxy": 0.0, "cxx": 800.0, "cyy": 800.0},
                {"nœud": 6, "Type": "Palier",
                 "kxx": 5e7, "kyy": 5e7, "kxy": 0.0, "cxx": 800.0, "cyy": 800.0},
            ],
            "name": "Rotor industriel (multi-étages)",
        },
 
        # ── API 684 (référence normative) ──────────────────────────────────
        "api684": {
            "shaft": [
                {"L (m)": 0.254, "id_L (m)": 0.0, "od_L (m)": 0.0762,
                 "id_R (m)": 0.0, "od_R (m)": 0.0762},
                {"L (m)": 0.127, "id_L (m)": 0.0, "od_L (m)": 0.1016,
                 "id_R (m)": 0.0, "od_R (m)": 0.1016},
                {"L (m)": 0.152, "id_L (m)": 0.0, "od_L (m)": 0.1016,
                 "id_R (m)": 0.0, "od_R (m)": 0.1016},
                {"L (m)": 0.152, "id_L (m)": 0.0, "od_L (m)": 0.1016,
                 "id_R (m)": 0.0, "od_R (m)": 0.1016},
                {"L (m)": 0.127, "id_L (m)": 0.0, "od_L (m)": 0.1016,
                 "id_R (m)": 0.0, "od_R (m)": 0.1016},
                {"L (m)": 0.254, "id_L (m)": 0.0, "od_L (m)": 0.0762,
                 "id_R (m)": 0.0, "od_R (m)": 0.0762},
            ],
            "disk": [
                {"nœud": 2, "Masse (kg)": 32.70,
                 "Id (kg.m²)": 0.156, "Ip (kg.m²)": 0.243},
                {"nœud": 4, "Masse (kg)": 32.70,
                 "Id (kg.m²)": 0.156, "Ip (kg.m²)": 0.243},
            ],
            "bear": [
                {"nœud": 0, "Type": "Palier",
                 "kxx": 1.75e8, "kyy": 1.75e8, "kxy": 0.0,
                 "cxx": 2000.0, "cyy": 2000.0},
                {"nœud": 6, "Type": "Palier",
                 "kxx": 1.75e8, "kyy": 1.75e8, "kxy": 0.0,
                 "cxx": 2000.0, "cyy": 2000.0},
            ],
            "name": "Rotor référence API 684",
        },
 
        # ── Vide ──────────────────────────────────────────────────────────
        "empty": {
            "shaft": [],
            "disk":  [],
            "bear":  [],
            "name":  "Nouveau rotor",
        },
    }
 
    tpl = templates.get(template, templates["simple"])
 
    st.session_state["df_shaft"] = pd.DataFrame(tpl["shaft"]) \
        if tpl["shaft"] else pd.DataFrame(
            columns=["L (m)", "id_L (m)", "od_L (m)", "id_R (m)", "od_R (m)"])
    st.session_state["df_disk"]  = pd.DataFrame(tpl["disk"]) \
        if tpl["disk"] else pd.DataFrame(
            columns=["nœud", "Masse (kg)", "Id (kg.m²)", "Ip (kg.m²)"])
    st.session_state["df_bear"]  = pd.DataFrame(tpl["bear"]) \
        if tpl["bear"] else pd.DataFrame(
            columns=["nœud", "Type", "kxx", "kyy", "kxy", "cxx", "cyy"])
 
    # Synchroniser les versions _live
    st.session_state["_df_shaft_live"] = st.session_state["df_shaft"].copy()
    st.session_state["_df_disk_live"]  = st.session_state["df_disk"].copy()
    st.session_state["_df_bear_live"]  = st.session_state["df_bear"].copy()
 
    # Forcer la recréation des éditeurs
    st.session_state["m1_data_gen"] = \
        st.session_state.get("m1_data_gen", 0) + 1
 
    st.session_state["rotor_name"]          = tpl["name"]
    st.session_state["rotor"]               = None
    st.session_state["m1_has_unsaved_changes"] = False
    st.session_state["m1_preset_applied"]   = "-"
 
    for key in ["res_static", "res_modal", "res_campbell",
                "res_ucs", "res_unbalance", "res_freq", "res_temporal"]:
        st.session_state[key] = None
 
# =============================================================================
# ONGLET ARBRE
# =============================================================================
def _render_tab_shaft():
    st.markdown(
        '<div class="rl-section-header">📏 Éléments d\'arbre</div>',
        unsafe_allow_html=True
    )
    st.caption(
        "Éléments de poutre Timoshenko — L : longueur, id : Ø interne, "
        "od : Ø externe. _L = côté gauche, _R = côté droit (arbre conique)."
    )
 
    gen = st.session_state.get("m1_data_gen", 0)
 
    result = st.data_editor(
        st.session_state["df_shaft"],
        key=f"m1_shaft_editor_{gen}",
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "L (m)": st.column_config.NumberColumn("L (m)", min_value=0.001, format="%.4f"),
            "id_L (m)": st.column_config.NumberColumn("id_L (m)", min_value=0.0, format="%.4f"),
            "od_L (m)": st.column_config.NumberColumn("od_L (m)", min_value=0.001, format="%.4f"),
            "id_R (m)": st.column_config.NumberColumn("id_R (m)", min_value=0.0, format="%.4f"),
            "od_R (m)": st.column_config.NumberColumn("od_R (m)", min_value=0.001, format="%.4f"),
        },
        on_change=lambda: st.session_state.update(m1_has_unsaved_changes=True)
    )
    st.session_state["_df_shaft_live"] = result
 
    n_el = len(result)
    st.caption(f"→ {n_el} éléments · {n_el + 1} nœuds (0 → {n_el})")


# =============================================================================
# ONGLET DISQUES
# =============================================================================
def _render_tab_disk():
    st.markdown(
        '<div class="rl-section-header">💿 Éléments disques</div>',
        unsafe_allow_html=True
    )
    st.caption(
        "Masses concentrées — saisie directe de masse et inerties "
        "(données CAO ou catalogue constructeur)."
    )
 
    gen = st.session_state.get("m1_data_gen", 0)
 
    result = st.data_editor(
        st.session_state["df_disk"],
        key=f"m1_disk_editor_{gen}",
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "nœud": st.column_config.NumberColumn("Nœud", min_value=0, step=1),
            "Masse (kg)": st.column_config.NumberColumn("Masse (kg)", min_value=0.0, format="%.4f"),
            "Id (kg.m²)": st.column_config.NumberColumn("Id (kg.m²)", min_value=0.0, format="%.6f"),
            "Ip (kg.m²)": st.column_config.NumberColumn("Ip (kg.m²)", min_value=0.0, format="%.6f"),
        },
        on_change=lambda: st.session_state.update(m1_has_unsaved_changes=True)
    )
    st.session_state["_df_disk_live"] = result


# =============================================================================
# ONGLET PALIERS
# =============================================================================
def _render_tab_bearing():
    st.markdown(
        '<div class="rl-section-header">⚙️ Paliers & Joints</div>',
        unsafe_allow_html=True
    )
 
    if "df_bear" not in st.session_state:
        st.session_state["df_bear"] = pd.DataFrame(
            columns=["nœud", "Type", "kxx", "kyy", "kxy", "cxx", "cyy"]
        )
 
    preset = st.selectbox(
        "Preset :",
        ["-"] + list(BEARING_PRESETS.keys()),
        key="m1_preset"
    )
 
    preset_applied = st.session_state.get("m1_preset_applied", "-")
 
    if preset != "-" and preset != preset_applied:
        st.session_state["m1_preset_applied"] = preset
        st.session_state["m1_has_unsaved_changes"] = True
        p = BEARING_PRESETS[preset]
        n_el = max(1, len(st.session_state.get("df_shaft", [])))
        new_bear = pd.DataFrame([
            {"nœud": 0, "Type": "Palier",
             "kxx": p["kxx"], "kyy": p["kyy"], "kxy": p["kxy"],
             "cxx": p["cxx"], "cyy": p["cyy"]},
            {"nœud": n_el, "Type": "Palier",
             "kxx": p["kxx"], "kyy": p["kyy"], "kxy": p["kxy"],
             "cxx": p["cxx"], "cyy": p["cyy"]},
        ])
        st.session_state["df_bear"] = new_bear
        st.session_state["_df_bear_live"] = new_bear.copy()
        st.session_state["m1_data_gen"] = st.session_state.get("m1_data_gen", 0) + 1
 
    elif preset == "-":
        st.session_state["m1_preset_applied"] = "-"
 
    gen = st.session_state.get("m1_data_gen", 0)
 
    result = st.data_editor(
        st.session_state["df_bear"].fillna(0.0),
        key=f"m1_bear_editor_{gen}",
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Type": st.column_config.SelectboxColumn(
                "Type", options=["Palier", "Joint", "Roulement", "Masse"], required=True
            ),
            "kxx": st.column_config.NumberColumn("kxx (N/m)", format="%.2e"),
            "kyy": st.column_config.NumberColumn("kyy (N/m)", format="%.2e"),
            "kxy": st.column_config.NumberColumn("kxy (N/m)", format="%.2e"),
            "cxx": st.column_config.NumberColumn("cxx (N·s/m)", format="%.1f"),
            "cyy": st.column_config.NumberColumn("cyy (N·s/m)", format="%.1f"),
        },
        on_change=lambda: st.session_state.update(m1_has_unsaved_changes=True)
    )
    st.session_state["_df_bear_live"] = result
 
    st.caption(
        "💡 Type 'Masse' : ajoute une masse ponctuelle sans rigidité "
        "(capteur, demi-accouplement)."
    )

# =============================================================================
# À COLLER dans modules/m1_builder.py
# Placez cette fonction AVANT _render_settings (ou n'importe où dans le fichier,
# Python résout les noms à l'exécution, pas à la définition — mais par convention
# mettez-la avec les autres _render_tab_*)
# =============================================================================

def _render_tab_material():
    st.markdown(
        '<div class="rl-section-header">🧱 Matériau</div>',
        unsafe_allow_html=True
    )
    mat_name = st.selectbox(
        "Matériau :",
        list(MATERIALS_DB.keys()),
        index=list(MATERIALS_DB.keys()).index(
            st.session_state.get("mat_name", "Acier standard (AISI 1045)")
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
# =============================================================================
# PANNEAU GRAPHICS
# =============================================================================
def _render_graphics(active_node: str):
    st.markdown(
        '<div class="rl-graphics-title">🏗️ Rotor Geometry — 3D View</div>',
        unsafe_allow_html=True
    )

    rotor = st.session_state.get("rotor")

    if rotor is None:
        st.markdown("""
        <div class="rl-card-info">
          <strong>🚀 Démarrage rapide</strong><br>
          <ol style="margin:6px 0 0 16px; font-size:0.9em;">
            <li>Sélectionnez un <strong>matériau</strong></li>
            <li>Définissez les <strong>éléments d'arbre</strong></li>
            <li>Ajoutez les <strong>disques</strong></li>
            <li>Configurez les <strong>paliers</strong></li>
            <li>Cliquez sur <strong>🚀 Assembler le rotor</strong></li>
          </ol>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Métriques globales (utilise les données éditées) ─────────────────
    df_shaft_display = st.session_state.get("_df_shaft_live", st.session_state.get("df_shaft", pd.DataFrame()))
    n_el = len(df_shaft_display)
    L_total = sum(float(r.get("L (m)", 0)) for r in df_shaft_display.to_dict("records"))

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

    try:
        ddl_val = rotor.ndof
    except Exception:
        ddl_val = "—"

    c4.markdown(f"""
    <div class="rl-metric-card">
      <div class="rl-metric-label">DDL total</div>
      <div class="rl-metric-value">{ddl_val}</div>
      <div class="rl-metric-unit">Valeur ROSS</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Visualisation 3D ─────────────────────────────────────────────────
    try:
        fig = rotor.plot_rotor()
        fig.update_layout(height=420, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True, key=f"m1_3d_plot_{id(rotor)}")
        try:
            import kaleido
            st.session_state["img_rotor"] = fig.to_image(format="png", width=700, height=400)
        except Exception:
            pass
    except Exception as e:
        st.error(f"❌ Impossible d'afficher le modèle 3D. Détail : {e}")

    # ── Récapitulatif — utilise les versions _live ───────────────────────
    with st.expander("📋 Récapitulatif du modèle", expanded=False):
        tab_s, tab_d, tab_b = st.tabs(["Arbre", "Disques", "Paliers"])
        with tab_s:
            st.dataframe(
                st.session_state.get("_df_shaft_live", st.session_state["df_shaft"]),
                use_container_width=True, hide_index=True
            )
        with tab_d:
            st.dataframe(
                st.session_state.get("_df_disk_live", st.session_state["df_disk"]),
                use_container_width=True, hide_index=True
            )
        with tab_b:
            st.dataframe(
                st.session_state.get("_df_bear_live", st.session_state["df_bear"]),
                use_container_width=True, hide_index=True
            )

    # ── Export Excel ─────────────────────────────────────────────────────
    try:
        import io
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            st.session_state.get("_df_shaft_live", st.session_state["df_shaft"]).to_excel(
                writer, sheet_name="Arbre", index=False)
            st.session_state.get("_df_disk_live", st.session_state["df_disk"]).to_excel(
                writer, sheet_name="Disques", index=False)
            st.session_state.get("_df_bear_live", st.session_state["df_bear"]).to_excel(
                writer, sheet_name="Paliers", index=False)
        st.download_button(
            "📥 Export Excel (.xlsx)",
            data=buf.getvalue(),
            file_name="rotor_parameters.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="m1_excel"
        )
    except Exception:
        st.caption("⚠️ xlsxwriter manquant — export Excel désactivé.")


# =============================================================================
# ASSEMBLAGE DU ROTOR
# =============================================================================
def _assemble_rotor():
    if not ROSS_OK:
        st.error("❌ ROSS n'est pas installé.")
        return
 
    errors = []
 
    # Lire les données courantes (versions _live prioritaires)
    df_shaft = st.session_state.get("_df_shaft_live", st.session_state.get("df_shaft", pd.DataFrame())).copy()
    df_disk = st.session_state.get("_df_disk_live", st.session_state.get("df_disk", pd.DataFrame())).copy()
    df_bear = st.session_state.get("_df_bear_live", st.session_state.get("df_bear", pd.DataFrame())).copy()
 
    try:
        mat_name = st.session_state.get("mat_name", "Acier standard (AISI 1045)")
        props = MATERIALS_DB[mat_name]
        mat = rs.Material(
            name=mat_name.replace(" ", "_"),
            rho=props["rho"],
            E=props["E"],
            G_s=props["G_s"]
        )
 
        # ── Arbre ────────────────────────────────────────────────────────
        shaft = []
        for i, row in df_shaft.iterrows():
            L = float(row.get("L (m)", 0.2))
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
 
        # ── Disques ──────────────────────────────────────────────────────
        disks = []
        for i, row in df_disk.iterrows():
            try:
                disks.append(rs.DiskElement(
                    n=int(row["nœud"]),
                    m=float(row["Masse (kg)"]),
                    Id=float(row["Id (kg.m²)"]),
                    Ip=float(row["Ip (kg.m²)"])
                ))
            except Exception as e:
                errors.append(f"Disque ligne {i+1} : {e}")
 
        # ── Paliers ──────────────────────────────────────────────────────
        bears = []
        for i, row in df_bear.fillna(0.0).iterrows():
            try:
                n = int(row["nœud"])
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
                        disks.append(rs.DiskElement(n=n, m=m_val, Id=0.0, Ip=0.0))
                elif e_type == "Joint":
                    bears.append(rs.SealElement(
                        n=n, kxx=kxx, kyy=kyy, kxy=kxy, kyx=-kxy, cxx=cxx, cyy=cyy))
                elif e_type == "Roulement":
                    bears.append(rs.RollerBearingElement(
                        n=n, kxx=kxx, kyy=kyy, kxy=kxy, kyx=-kxy, cxx=cxx, cyy=cyy))
                else:
                    bears.append(rs.BearingElement(
                        n=n, kxx=kxx, kyy=kyy, kxy=kxy, kyx=-kxy, cxx=cxx, cyy=cyy))
            except Exception as e:
                errors.append(f"Palier ligne {i+1} : {e}")
 
        if not bears:
            errors.append("Aucun palier défini.")
 
        if errors:
            for err in errors:
                st.error(f"❌ {err}")
            return
 
        with st.spinner("Assemblage du modèle éléments finis…"):
            rotor = rs.Rotor(shaft, disks, bears)
 
        # ✅ Synchronisation df_base ↔ df_live après assemblage
        st.session_state["df_shaft"] = df_shaft.copy()
        st.session_state["df_disk"] = df_disk.copy()
        st.session_state["df_bear"] = df_bear.copy()
        st.session_state["_df_shaft_live"] = df_shaft.copy()
        st.session_state["_df_disk_live"] = df_disk.copy()
        st.session_state["_df_bear_live"] = df_bear.copy()
 
        st.session_state["rotor"] = rotor
        st.session_state["rotor_name"] = "Rotor personnalisé"
        st.session_state["rotor_source"] = "custom"
 
        for key in ["res_static", "res_modal", "res_campbell",
                    "res_ucs", "res_unbalance", "res_freq", "res_temporal"]:
            st.session_state[key] = None
 
        try:
            from app import add_log
            add_log(f"Rotor assemblé : {len(rotor.nodes)} nœuds, {rotor.m:.2f} kg, {rotor.ndof} DDL", "ok")
        except ImportError:
            pass
 
        st.session_state["m1_has_unsaved_changes"] = False
        st.success(f"✅ Rotor assemblé — {len(rotor.nodes)} nœuds | {rotor.m:.2f} kg | {rotor.ndof} DDL")
        st.rerun()
 
    except Exception as e:
        st.error(f"❌ Erreur d'assemblage : {e}")
        import traceback
        st.code(traceback.format_exc(), language="python")


# =============================================================================
# INITIALISATION DES TABLEAUX PAR TEMPLATE
# =============================================================================
def _init_tables(template: str = "simple"):
    """Initialise les DataFrames selon un template prédéfini."""
    
    templates = {
        "empty": {
            "shaft": pd.DataFrame(columns=["L (m)", "id_L (m)", "od_L (m)", "id_R (m)", "od_R (m)"]),
            "disk": pd.DataFrame(columns=["nœud", "Masse (kg)", "Id (kg.m²)", "Ip (kg.m²)"]),
            "bear": pd.DataFrame(columns=["nœud", "Type", "kxx", "kyy", "kxy", "cxx", "cyy"]),
            "name": "Nouveau rotor (vide)"
        },
        "simple": {
            "shaft": pd.DataFrame([
                {"L (m)": 0.20, "id_L (m)": 0.0, "od_L (m)": 0.05, "id_R (m)": 0.0, "od_R (m)": 0.05}
                for _ in range(5)
            ]),
            "disk": pd.DataFrame([
                {"nœud": 2, "Masse (kg)": 15.12, "Id (kg.m²)": 0.025, "Ip (kg.m²)": 0.047}
            ]),
            "bear": pd.DataFrame([
                {"nœud": 0, "Type": "Palier", "kxx": 1e6, "kyy": 1e6, "kxy": 0.0, "cxx": 0.0, "cyy": 0.0},
                {"nœud": 5, "Type": "Palier", "kxx": 1e6, "kyy": 1e6, "kxy": 0.0, "cxx": 0.0, "cyy": 0.0},
            ]),
            "name": "Nouveau rotor (simple)"
        },
        "industrial": {
            "shaft": pd.DataFrame([
                {"L (m)": 0.15, "id_L (m)": 0.02, "od_L (m)": 0.04, "id_R (m)": 0.02, "od_R (m)": 0.04},
                {"L (m)": 0.25, "id_L (m)": 0.02, "od_L (m)": 0.04, "id_R (m)": 0.03, "od_R (m)": 0.05},
                {"L (m)": 0.30, "id_L (m)": 0.03, "od_L (m)": 0.05, "id_R (m)": 0.03, "od_R (m)": 0.05},
                {"L (m)": 0.25, "id_L (m)": 0.03, "od_L (m)": 0.05, "id_R (m)": 0.02, "od_R (m)": 0.04},
                {"L (m)": 0.15, "id_L (m)": 0.02, "od_L (m)": 0.04, "id_R (m)": 0.02, "od_R (m)": 0.04},
            ]),
            "disk": pd.DataFrame([
                {"nœud": 1, "Masse (kg)": 8.5, "Id (kg.m²)": 0.012, "Ip (kg.m²)": 0.021},
                {"nœud": 3, "Masse (kg)": 22.3, "Id (kg.m²)": 0.045, "Ip (kg.m²)": 0.082},
                {"nœud": 4, "Masse (kg)": 8.5, "Id (kg.m²)": 0.012, "Ip (kg.m²)": 0.021},
            ]),
            "bear": pd.DataFrame([
                {"nœud": 0, "Type": "Palier", "kxx": 2.5e7, "kyy": 2.5e7, "kxy": 1.2e6, "cxx": 1200, "cyy": 1200},
                {"nœud": 5, "Type": "Palier", "kxx": 2.5e7, "kyy": 2.5e7, "kxy": 1.2e6, "cxx": 1200, "cyy": 1200},
            ]),
            "name": "Nouveau rotor (industriel)"
        },
        "api684": {
            "shaft": pd.DataFrame([
                {"L (m)": 0.30, "id_L (m)": 0.0, "od_L (m)": 0.075, "id_R (m)": 0.0, "od_R (m)": 0.075}
                for _ in range(4)
            ]),
            "disk": pd.DataFrame([
                {"nœud": 2, "Masse (kg)": 45.0, "Id (kg.m²)": 0.18, "Ip (kg.m²)": 0.32},
            ]),
            "bear": pd.DataFrame([
                {"nœud": 0, "Type": "Palier", "kxx": 1.8e7, "kyy": 1.8e7, "kxy": 0.0, "cxx": 2500, "cyy": 2500},
                {"nœud": 4, "Type": "Palier", "kxx": 1.8e7, "kyy": 1.8e7, "kxy": 0.0, "cxx": 2500, "cyy": 2500},
            ]),
            "name": "Rotor référence API 684"
        }
    }
    
    tpl = templates.get(template, templates["simple"])
    
    # Initialiser les DataFrames
    st.session_state["df_shaft"] = tpl["shaft"].copy()
    st.session_state["df_disk"] = tpl["disk"].copy()
    st.session_state["df_bear"] = tpl["bear"].copy()
    
    # Synchroniser les versions _live
    st.session_state["_df_shaft_live"] = tpl["shaft"].copy()
    st.session_state["_df_disk_live"] = tpl["disk"].copy()
    st.session_state["_df_bear_live"] = tpl["bear"].copy()
    
    # Incrémenter la génération pour forcer le re-render des éditeurs
    st.session_state["m1_data_gen"] = st.session_state.get("m1_data_gen", 0) + 1
    
    # Mettre à jour le nom et réinitialiser les résultats
    st.session_state["rotor_name"] = tpl["name"]
    st.session_state["rotor"] = None
    for key in ["res_static", "res_modal", "res_campbell",
                "res_ucs", "res_unbalance", "res_freq", "res_temporal"]:
        st.session_state[key] = None
    
    # ✅ PRÉSERVER le matériau sélectionné (paramètre global)
    # st.session_state["mat_name"] reste inchangé


def _get_template_preview(template: str) -> str:
    """Retourne une description HTML de l'aperçu du template."""
    previews = {
        "empty": "Arbre vide • 0 élément • À vous de construire chaque composant",
        "simple": "5 éléments d'arbre cylindriques • 1 disque central • 2 paliers identiques • Idéal pour apprendre",
        "industrial": "5 éléments coniques • 3 disques (compresseur/turbine) • Paliers hydrodynamiques réalistes",
        "api684": "4 éléments identiques • 1 disque lourd • Conforme aux critères de validation API 684"
    }
    return previews.get(template, "")


def _load_model_from_dict(data: dict):
    """Charge un modèle depuis un dictionnaire JSON (après upload)."""
    # Nettoyer les éditeurs existants pour éviter les conflits de clés
    for editor_key in ["m1_shaft_editor", "m1_disk_editor", "m1_bear_editor"]:
        if editor_key in st.session_state:
            del st.session_state[editor_key]
    
    # Charger les DataFrames
    st.session_state["df_shaft"] = pd.DataFrame(data["shaft"])
    st.session_state["df_disk"] = pd.DataFrame(data.get("disks", data.get("disk", [])))
    st.session_state["df_bear"] = pd.DataFrame(data.get("bearings", data.get("bearing", [])))
    
    # Initialiser les versions _live
    st.session_state["_df_shaft_live"] = st.session_state["df_shaft"].copy()
    st.session_state["_df_disk_live"] = st.session_state["df_disk"].copy()
    st.session_state["_df_bear_live"] = st.session_state["df_bear"].copy()
    
    # Gestion de la génération
    st.session_state["m1_data_gen"] = st.session_state.get("m1_data_gen", 0) + 1
    
    # Métadonnées
    st.session_state["mat_name"] = data.get("material", "Acier standard (AISI 1045)")
    st.session_state["rotor_name"] = data.get("name", "Modèle importé")
    
    # Réinitialiser les résultats d'analyse
    for key in ["res_static", "res_modal", "res_campbell",
                "res_ucs", "res_unbalance", "res_freq", "res_temporal"]:
        st.session_state[key] = None
    
    # Réinitialiser le rotor
    st.session_state["rotor"] = None


def _trigger_save():
    """Marque le modèle comme sauvegardé (la sauvegarde réelle passe par le download_button)."""
    st.session_state["m1_has_unsaved_changes"] = False
    st.toast("💾 Modèle marqué comme sauvegardé", icon="✅")
