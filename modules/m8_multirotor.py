# modules/m8_multirotor.py — MultiRotor & GearElement v2
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
# Entree par JSON + Benchmark ROSS Tutorial Part 4
# =============================================================================

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

try:
    import ross as rs
    ROSS_OK = True
except ImportError:
    ROSS_OK = False

# =============================================================================
# MODELE DE REFERENCE — ROSS Tutorial Part 4
# Source : ross.readthedocs.io/en/stable/user_guide/tutorial_part_4.html
# =============================================================================
REFERENCE_JSON = {
    "name": "ROSS Tutorial Part 4 - Reference MultiRotor",
    "material": {"name": "Steel", "rho": 7810, "E": 211e9, "G_s": 81.2e9},
    "rotor1": {
        "description": "Rotor moteur (generateur + pignon z=37)",
        "shaft": [
            {"L": 0.300, "idl": 0.0, "odl": 0.123, "idr": 0.0, "odr": 0.123},
            {"L": 0.092, "idl": 0.0, "odl": 0.150, "idr": 0.0, "odr": 0.150},
            {"L": 0.200, "idl": 0.0, "odl": 0.150, "idr": 0.0, "odr": 0.150},
            {"L": 0.200, "idl": 0.0, "odl": 0.150, "idr": 0.0, "odr": 0.150},
            {"L": 0.092, "idl": 0.0, "odl": 0.150, "idr": 0.0, "odr": 0.150},
            {"L": 0.300, "idl": 0.0, "odl": 0.123, "idr": 0.0, "odr": 0.123}
        ],
        "disks": [
            {"n": 0, "m": 66.63, "Id": 0.431, "Ip": 0.735},
            {"n": 6, "m": 69.83, "Id": 0.542, "Ip": 0.884}
        ],
        "gear_elements": [
            {"n": 3, "m": 14.37, "Id": 0.068, "Ip": 0.136,
             "width": 0.07,
             "n_teeth": 37, "base_diameter": 0.19,
             "pressure_angle_deg": 22.5, "helix_angle_deg": 0.0}
        ],
        "bearings": [
            {"n": 2, "kxx": 5.5e8, "kyy": 6.7e8, "cxx": 3e3, "cyy": 3e3},
            {"n": 4, "kxx": 5.5e8, "kyy": 6.7e8, "cxx": 3e3, "cyy": 3e3}
        ],
        "speed_rpm": 1200.0
    },
    "rotor2": {
        "description": "Rotor recepteur (turbine + roue z=159)",
        "shaft": [
            {"L": 0.080, "idl": 0.0, "odl": 0.321, "idr": 0.0, "odr": 0.321},
            {"L": 0.200, "idl": 0.0, "odl": 0.321, "idr": 0.0, "odr": 0.321},
            {"L": 0.200, "idl": 0.0, "odl": 0.261, "idr": 0.0, "odr": 0.261},
            {"L": 0.640, "idl": 0.0, "odl": 0.261, "idr": 0.0, "odr": 0.261}
        ],
        "disks": [],
        "gear_elements": [
            {"n": 1, "m": 322.0, "Id": 24.17, "Ip": 48.34,
             "width": 0.20,
             "n_teeth": 159, "base_diameter": 0.826,
             "pressure_angle_deg": 22.5, "helix_angle_deg": 0.0}
        ],
        "bearings": [
            {"n": 0, "kxx": 3.2e9, "kyy": 4.6e9, "cxx": 3e3, "cyy": 3e3},
            {"n": 4, "kxx": 3.2e9, "kyy": 4.6e9, "cxx": 3e3, "cyy": 3e3}
        ],
        "speed_rpm": 279.0
    }
}


# =============================================================================
# POINT D ENTREE
# =============================================================================
def render_m8(col_settings, col_graphics):
    with col_settings:
        _render_settings()
    with col_graphics:
        _render_graphics()


# =============================================================================
# PANNEAU SETTINGS
# =============================================================================
def _render_settings():
    st.markdown(
        '<div class="rl-settings-title">MultiRotor & GearElement [NEW]</div>',
        unsafe_allow_html=True)
    st.markdown(
        '<span class="rl-badge rl-badge-new">NEW v2.0</span>',
        unsafe_allow_html=True)

    tab_load, tab_params, tab_run = st.tabs([
        "Chargement du modele",
        "Parametres de calcul",
        "Statut & Actions"
    ])

    with tab_load:
        _render_tab_load()
    with tab_params:
        _render_tab_params()
    with tab_run:
        _render_tab_run()


def _render_tab_load():
    # ── STYLE "PRO" POUR LES BOUTONS (Version Bouton Solide) ─────────────
    # ── STYLE "PRO" (On cible le bouton standard pour contourner Streamlit) ──
    st.markdown("""
    <style>
        /* 1. Le bouton "Charger modèle" (Apparence forcée) */
        div[data-testid="stBaseButton-secondary"] button {
            background-color: #1F5C8B !important;  /* Force le fond bleu */
            color: white !important;                /* Force le texte blanc */
            border: none !important;                
            border-radius: 8px !important;          
            box-shadow: 0 4px 6px rgba(0,0,0,0.15) !important; 
            font-weight: bold !important;
        }
        
        div[data-testid="stBaseButton-secondary"] button:hover {
            background-color: #164b70 !important;  /* Bleu plus foncé au survol */
        }

        /* Apparence quand le bouton est grisé (si aucun JSON sélectionné) */
        div[data-testid="stBaseButton-secondary"] button:disabled {
            background-color: #a0b4c8 !important;  /* Gris bleuté */
            color: white !important;
        }

        /* 2. Bouton "Télécharger" (Aspect discret fantôme) */
        .stDownloadButton > button {
            background-color: transparent !important; 
            color: #1F5C8B !important;                
            border: 1px dashed #1F5C8B !important;    
            border-radius: 5px !important;
            font-weight: 500 !important;
        }
        .stDownloadButton > button:hover {
            background-color: #f0f4f8 !important;    
            border: 1px solid #1F5C8B !important;    
        }
    </style>
    """, unsafe_allow_html=True)
    # ──────────────────────────────────────────────────────────────────────

    st.markdown('<div class="rl-section-header">Source du modèle</div>',
                unsafe_allow_html=True)

    # ── ÉTAPE 1 : Choix de la source ─────────────────────────────────────
    source = st.radio(
        "Source :",
        ["Modèle de référence (ROSS Tutorial Part 4)", "Charger un modèle (fichier json)"],
        key="m8_source")

    # ── ÉTAPE 2 : Champ de saisie dynamique selon le choix ───────────────
    fichier_uploade = None
    
    if source == "Modèle de référence (ROSS Tutorial Part 4)":
        st.markdown("""
        <div class="rl-card-info">
          <strong>Benchmark ROSS Tutorial Part 4</strong><br>
          <small>Générateur-turbine couplé par engrenage droit 22.5 deg.<br>
          R1 : 7 nœuds | R2 : 5 nœuds | z1=37, z2=159, i=0.2327<br>
          N1=1200 RPM, N2=279 RPM, fe=740 Hz</small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="rl-card-info">
          <small>Chargez un fichier JSON respectant la structure attendue 
          (shaft, disks, gear_elements, bearings).</small>
        </div>
        """, unsafe_allow_html=True)
        
        fichier_uploade = st.file_uploader(
            "Sélectionnez votre fichier JSON",
            type=["json"],
            label_visibility="collapsed",
            key="m8_upload")

    st.markdown("") 

    # ── ÉTAPE 3 : Le bouton d'action UNIQUE ──────────────────────────────
    bouton_desactive = (source == "Charger un modèle (fichier json)" and fichier_uploade is None)
    
    if st.button("Charger modèle", key="m8_load_action", 
                 use_container_width=True, disabled=bouton_desactive):
        
        if source == "Modèle de référence (ROSS Tutorial Part 4)":
            st.session_state["m8_json_data"]   = REFERENCE_JSON
            st.session_state["m8_loaded"]      = True
            st.session_state["m8_source_name"] = "ROSS Tutorial Part 4"
            _clear_results()
            _log("Modèle référence ROSS Part 4 chargé", "ok")
            
        else:
            if fichier_uploade is not None:
                try:
                    data = json.loads(fichier_uploade.read().decode("utf-8"))
                    _validate_json(data)
                    st.session_state["m8_json_data"]    = data
                    st.session_state["m8_loaded"]       = True
                    st.session_state["m8_source_name"]  = data.get("name", fichier_uploade.name)
                    _clear_results()
                    _log("JSON chargé avec succès", "ok")
                except Exception as e:
                    st.error("Erreur lors de la lecture du JSON : {}".format(e))
            else:
                st.warning("Veuillez d'abord sélectionner un fichier.")

    # ── ÉTAPE 4 : Affichage après chargement ─────────────────────────────
    if st.session_state.get("m8_loaded") and st.session_state.get("m8_json_data"):
        st.markdown("---")
        _show_model_summary()
        
        st.download_button(
            "Télécharger le JSON en cours",
            data=json.dumps(st.session_state["m8_json_data"], indent=2),
            file_name="multirotor_model.json",
            mime="application/json",
            key="m8_dl_current")
def _show_model_summary():
    data = st.session_state["m8_json_data"]
    r1d  = data.get("rotor1", {})
    r2d  = data.get("rotor2", {})
    z1   = r1d["gear_elements"][0]["n_teeth"] \
           if r1d.get("gear_elements") else 1
    z2   = r2d["gear_elements"][0]["n_teeth"] \
           if r2d.get("gear_elements") else 1
    rpm1 = float(r1d.get("speed_rpm", 1000))
    rpm2 = rpm1 * z1 / z2 if z2 > 0 else 0
    fe   = rpm1 / 60 * z1

    st.markdown("---")
    st.markdown("**Resume :**")
    c1, c2 = st.columns(2)
    with c1:
        st.caption("R1 : {} el | {} disques | {} paliers".format(
            len(r1d.get("shaft", [])),
            len(r1d.get("disks", [])),
            len(r1d.get("bearings", []))))
        st.caption("{:.0f} RPM | {} dents".format(rpm1, z1))
    with c2:
        st.caption("R2 : {} el | {} disques | {} paliers".format(
            len(r2d.get("shaft", [])),
            len(r2d.get("disks", [])),
            len(r2d.get("bearings", []))))
        st.caption("{:.0f} RPM | {} dents".format(rpm2, z2))
    st.caption("fe = {:.2f} Hz | i = {}/{} = {:.4f}".format(
        fe, z1, z2, z1/z2 if z2 > 0 else 0))


def _render_tab_params():
    st.markdown('<div class="rl-section-header">Parametres Campbell</div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Vitesse max (RPM)", 500.0, 30000.0, 4000.0,
                        step=500.0, key="m8_vmax")
        st.slider("Resolution (points)", 10, 80, 25, key="m8_npts")
    with c2:
        st.slider("Nombre de modes", 4, 24, 12, key="m8_n_modes")
        st.radio("Harmoniques", ["1X", "1X + 2X", "1X + 2X + fe"],
                 index=2, horizontal=True, key="m8_harmonics")

    # ── Réponse au balourd ───────────────────────────────────────────────
    # CORRECTION : Désindenter cette ligne pour qu'elle soit hors du bloc "with c2:"
    st.markdown('<div class="rl-section-header">Reponse au balourd</div>',
                unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.radio("Rotor cible", ["Rotor 1", "Rotor 2"],
                 key="m8_unb_rotor", horizontal=False)
        st.number_input("Noeud de mesure", min_value=0, value=0, step=1,
                        key="m8_unb_node_ui",
                        help="Indice du noeud (0 = premier noeud)")
    with c2:
        st.radio("Plan de mesure", ["Horizontal (X)", "Vertical (Y)"],
                 key="m8_unb_dof", horizontal=True)
        st.number_input("Magnitude (kg.m)", 1e-6, 1.0, 1e-3,
                        format="%.4f", key="m8_unb_mag")

def _render_tab_run():
    st.markdown('<div class="rl-section-header">Lancement</div>',
                unsafe_allow_html=True)

    if not st.session_state.get("m8_loaded"):
        st.warning("Chargez d'abord un modele.")
        return

    st.success("Modele : {}".format(
        st.session_state.get("m8_source_name", "—")))

    st.button("Assembler et lancer tous les calculs",
              type="primary", key="m8_run_all",
              use_container_width=True, on_click=_run_all)

    if st.session_state.get("m8_multi_warn"):
        st.error("⚠️ Erreur MultiRotor :")
        with st.expander("Voir les détails techniques", expanded=True):
            st.code(st.session_state["m8_multi_warn"], language="python")

    checks = [
        ("m8_rotor1",    "Rotor 1 assemble"),
        ("m8_rotor2",    "Rotor 2 assemble"),
        ("m8_multi",     "MultiRotor couple"),
        ("m8_modal_multi","Modal MultiRotor couple"),
        ("m8_modal1",    "Modal Rotor 1"),
        ("m8_modal2",    "Modal Rotor 2"),
        ("m8_camp",      "Campbell MultiRotor"),
        ("m8_unbal_res", "Reponse au balourd"),
    ]
    for key, label in checks:
        icon = "OK" if st.session_state.get(key) is not None else "..."
        st.caption("[{}] {}".format(icon, label))

    if st.session_state.get("m8_json_data"):
        st.markdown("---")
        st.download_button(
            "Sauvegarder le modele (.json)",
            data=json.dumps(st.session_state["m8_json_data"], indent=2),
            file_name="multirotor_model.json",
            mime="application/json",
            key="m8_save")

# =============================================================================
# PANNEAU GRAPHICS
# =============================================================================
def _render_graphics():
    st.markdown(
        '<div class="rl-graphics-title">MultiRotor — Results</div>',
        unsafe_allow_html=True)

    # Déclaration des onglets (sur une seule liste)
    tabs = st.tabs([
        "Geometrie", "Campbell couple", "Analyse modale",
        "Reponse balourd", "Benchmark", "Theorie", "Diagnostic"
    ])
    
    # Assignation séparée (évite les erreurs de copier-coller)
    tab_geo, tab_camp, tab_modal, tab_unbal, tab_bench, tab_theory, tab_diag = tabs

    with tab_geo:    _display_geometry()
    with tab_camp:   _display_campbell()
    with tab_modal:  _display_modal()
    with tab_unbal:  _display_unbalance()
    with tab_bench:  _display_benchmark()
    with tab_theory: _display_theory()
    with tab_diag:   _display_diagnostic()


# =============================================================================
# UTILITAIRES
# =============================================================================
def _clear_results():
    for k in ["m8_rotor1", "m8_rotor2", "m8_multi",
              "m8_modal1", "m8_modal2", "m8_modal_multi",
              "m8_camp", "m8_camp1", "m8_camp2",
              "m8_unbal_res", "m8_error", "m8_multi_warn",
              "m8_gear_ratio"]:
        st.session_state[k] = None


def _validate_json(data):
    for key in ["rotor1", "rotor2"]:
        if key not in data:
            raise ValueError("Cle '{}' manquante.".format(key))
        r = data[key]
        if not r.get("shaft"):
            raise ValueError("{} : 'shaft' manquant.".format(key))
        if not r.get("bearings"):
            raise ValueError("{} : 'bearings' manquant.".format(key))
        if not r.get("gear_elements"):
            raise ValueError("{} : 'gear_elements' requis pour MultiRotor.".format(key))


def _get_gear_params(rotor_data, key):
    gears = rotor_data.get("gear_elements", [])
    if gears:
        return gears[0].get(key, 0)
    return 0

# =============================================================================
# CONSTRUCTION DEPUIS JSON (VERSION CORRIGÉE)
# =============================================================================
def _build_rotor_from_json(rotor_data, mat, rotor_name=""):
    shaft = [rs.ShaftElement(L=float(e["L"]), idl=float(e.get("idl", 0.0)), odl=float(e["odl"]), idr=float(e.get("idr", 0.0)), odr=float(e.get("odr", e["odl"])), material=mat, shear_effects=True, rotary_inertia=True, gyroscopic=True) for e in rotor_data["shaft"]]
    
    disks = [rs.DiskElement(n=int(d["n"]), m=float(d["m"]), Id=float(d["Id"]), Ip=float(d["Ip"])) for d in rotor_data.get("disks", [])]
    
    gear_elements = []
    for g in rotor_data.get("gear_elements", []):
        try:
            import inspect
            sig = inspect.signature(rs.GearElement.__init__)
            kw = {"n": int(g["n"]), "m": float(g["m"]), "Id": float(g["Id"]), "Ip": float(g["Ip"]), "width": float(g.get("width", 0.07)), "n_teeth": int(g["n_teeth"]), "base_diameter": float(g["base_diameter"]), "pressure_angle": float(g.get("pressure_angle_deg", 22.5)), "helix_angle": float(g.get("helix_angle_deg", 0.0))}
            gear_elements.append(rs.GearElement(**{k: v for k, v in kw.items() if k in sig.parameters}))
        except Exception as e:
            _log("GearElement erreur, fallback DiskElement: {}".format(e), "warn")
            gear_elements.append(rs.DiskElement(n=int(g["n"]), m=float(g["m"]), Id=float(g["Id"]), Ip=float(g["Ip"])))

    bears = [rs.BearingElement(n=int(b["n"]), kxx=float(b["kxx"]), kyy=float(b.get("kyy", b["kxx"])), kxy=float(b.get("kxy", 0.0)), kyx=float(b.get("kyx", 0.0)), cxx=float(b.get("cxx", 500.0)), cyy=float(b.get("cyy", 500.0))) for b in rotor_data["bearings"]]

    return rs.Rotor(shaft, disks + gear_elements, bears)
# =============================================================================
# CALCUL PRINCIPAL (VERSION CORRIGÉE)
# =============================================================================
def _run_all():
    if not st.session_state.get("m8_loaded") or \
            not st.session_state.get("m8_json_data"):
        st.session_state["m8_error"] = "Aucun modele charge."
        return
    if not ROSS_OK:
        st.session_state["m8_error"] = "ROSS non disponible."
        return

    data  = st.session_state["m8_json_data"]
    mat_d = data.get("material",
                     {"name": "Steel", "rho": 7810, "E": 211e9, "G_s": 81.2e9})
    mat = rs.Material(
        name=str(mat_d.get("name", "Steel")).replace(" ", "_"),
        rho=float(mat_d["rho"]),
        E=float(mat_d["E"]),
        G_s=float(mat_d["G_s"]))

    try:
        # Appel de la fonction corrigée avec un nom pour les messages d'erreur
        r1 = _build_rotor_from_json(data["rotor1"], mat, rotor_name="Rotor 1")
        r2 = _build_rotor_from_json(data["rotor2"], mat, rotor_name="Rotor 2")
        st.session_state["m8_rotor1"] = r1
        st.session_state["m8_rotor2"] = r2
        st.session_state["m8_error"]  = None
        _log("R1:{} noeuds {:.1f}kg | R2:{} noeuds {:.1f}kg".format(
            len(r1.nodes), r1.m, len(r2.nodes), r2.m), "ok")

        vmax    = float(st.session_state.get("m8_vmax", 4000))
        npts    = int(st.session_state.get("m8_npts", 25))
        n_modes = int(st.session_state.get("m8_n_modes", 12))

        # === CORRECTION 3 : Vérification de la cohérence des nœuds ===
        # Récupérer les numéros de nœuds depuis le JSON
        gear_node_r1 = int(data["rotor1"]["gear_elements"][0]["n"])
        gear_node_r2 = int(data["rotor2"]["gear_elements"][0]["n"])

        # Vérifier que les nœuds existent dans les rotors construits
        if gear_node_r1 >= len(r1.nodes):
            st.error(f"❌ ERREUR : Le nœud pour l'engrenage du Rotor 1 est défini à {gear_node_r1}, mais ce rotor n'a que {len(r1.nodes)} nœuds (numérotés de 0 à {len(r1.nodes)-1}).")
            return
        if gear_node_r2 >= len(r2.nodes):
            st.error(f"❌ ERREUR : Le nœud pour l'engrenage du Rotor 2 est défini à {gear_node_r2}, mais ce rotor n'a que {len(r2.nodes)} nœuds (numérotés de 0 à {len(r2.nodes)-1}).")
            return

        # ── MultiRotor couple ─────────────────────────────────────────────
        try:
            # Tentative avec l'API ROSS moderne (liste de rotors)
            try:
                multi = rs.MultiRotor(
                    rotors=[r1, r2],
                    gear_mesh_stiffness=1e8
                )
            except TypeError:
                # Fallback ancienne API (arguments separes)
                gear_node_r1 = int(data["rotor1"]["gear_elements"][0]["n"])
                gear_node_r2 = int(data["rotor2"]["gear_elements"][0]["n"])
                multi = rs.MultiRotor(
                    r1,
                    r2,
                    coupled_nodes=(gear_node_r1, gear_node_r2),
                    gear_mesh_stiffness=1e8,
                    orientation_angle=0,
                    position="below",
                )
            st.session_state["m8_multi"] = multi

            frequency_range = rs.Q_(np.linspace(0, vmax, npts), "RPM")
            camp = multi.run_campbell(frequency_range, frequencies=n_modes)
            st.session_state["m8_camp"]       = camp
            st.session_state["m8_camp_vmax"]  = vmax
            st.session_state["m8_gear_ratio"] = multi.mesh.gear_ratio
            _log("MultiRotor couple et Campbell calcules", "ok")

        except Exception as e_m:
            import traceback
            msg_complet = traceback.format_exc()
            st.session_state["m8_error"]      = "MultiRotor ERREUR: {}".format(e_m)
            st.session_state["m8_multi_warn"] = msg_complet
            _log("MultiRotor ERREUR: {}".format(e_m), "err")

            # Fallback : Campbell individuels
            speeds = np.linspace(0, vmax * np.pi / 30, npts)
            z1 = _get_gear_params(data["rotor1"], "n_teeth")
            z2 = _get_gear_params(data["rotor2"], "n_teeth")
            ratio = z1 / z2 if z2 > 0 else 1.0
            camp1 = r1.run_campbell(speeds, frequencies=n_modes)
            camp2 = r2.run_campbell(speeds * ratio, frequencies=n_modes)
            st.session_state["m8_camp1"]     = camp1
            st.session_state["m8_camp2"]     = camp2
            st.session_state["m8_camp_vmax"] = vmax
            _log("Campbell individuels R1+R2 calcules (fallback)", "ok")

        # ── Analyses modales ──────────────────────────────────────────────
        st.session_state["m8_modal1"] = r1.run_modal(speed=0)
        st.session_state["m8_modal2"] = r2.run_modal(speed=0)
        _log("Analyses modales individuelles terminees", "ok")

        multi_ok = st.session_state.get("m8_multi")
        if multi_ok is not None:
            try:
                st.session_state["m8_modal_multi"] = multi_ok.run_modal(speed=0)
                _log("Modal MultiRotor couple calcule", "ok")
            except Exception as e:
                _log("Modal MultiRotor : {}".format(e), "warn")

        # ── Reponse au balourd ────────────────────────────────────────────
        _run_unbalance_calc(r1, r2)

    except Exception as e:
        import traceback
        st.session_state["m8_error"] = traceback.format_exc()
        _log("Erreur generale : {}".format(e), "err")


def _run_unbalance_calc(r1, r2):
    try:
        unb_mag  = float(st.session_state.get("m8_unb_mag", 1e-3))
        vmax     = float(st.session_state.get("m8_vmax", 4000))
        rotor_s  = r1 if "1" in st.session_state.get("m8_unb_rotor", "R1") else r2
        
        # Lecture du noeud choisi par l'utilisateur dans l'UI
        node_m = int(st.session_state.get("m8_unb_node_ui", 0))
        
        # Securite : verification que le noeud existe bien pour le rotor choisi
        max_node = len(rotor_s.nodes) - 1
        if node_m > max_node:
            node_m = max_node

        freqs_rad = np.linspace(0, vmax * np.pi / 30, 300)

        res = rotor_s.run_unbalance_response(
            node=[node_m],
            unbalance_magnitude=[unb_mag],
            unbalance_phase=[0.0],
            frequency=freqs_rad)

        st.session_state["m8_unbal_res"]  = res
        st.session_state["m8_unbal_node"] = node_m
        _log("Balourd calcule (N{})".format(node_m), "ok")

    except Exception as e:
        import traceback
        _log("Balourd : {}".format(traceback.format_exc()), "warn")


# =============================================================================
# AFFICHAGE GEOMETRIE
# =============================================================================
def _display_geometry():
    r1 = st.session_state.get("m8_rotor1")
    r2 = st.session_state.get("m8_rotor2")
    if r1 is None or r2 is None:
        st.info("Chargez un modele et lancez les calculs.")
        return

    data = st.session_state.get("m8_json_data", {})
    r1d  = data.get("rotor1", {})
    r2d  = data.get("rotor2", {})
    z1   = _get_gear_params(r1d, "n_teeth")
    z2   = _get_gear_params(r2d, "n_teeth")
    rpm1 = float(r1d.get("speed_rpm", 1000))
    rpm2 = rpm1 * z1 / z2 if z2 > 0 else 0
    fe   = rpm1 / 60 * z1

    multi = st.session_state.get("m8_multi")

    if multi is not None:
        try:
            fig = multi.plot_rotor()
            fig.update_layout(
                height=380,
                title="MultiRotor couple — R1 + R2",
                font=dict(size=11),
                margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True, key="m8_geo_multi")
        except Exception as e:
            st.warning("plot_rotor MultiRotor : {}".format(e))
    else:
        st.warning("MultiRotor non couple — affichage individuel (voir erreur dans Statut)")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**R1** — {:.0f} RPM | {:.2f} kg".format(rpm1, r1.m))
            try:
                fig1 = r1.plot_rotor()
                fig1.update_layout(height=260, title="Rotor 1",
                                   font=dict(size=10),
                                   margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig1, use_container_width=True, key="m8_geo1")
            except Exception as e:
                st.warning("R1 : {}".format(e))
        with col2:
            st.markdown("**R2** — {:.0f} RPM | {:.2f} kg".format(rpm2, r2.m))
            try:
                fig2 = r2.plot_rotor()
                fig2.update_layout(height=260, title="Rotor 2",
                                   font=dict(size=10),
                                   margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig2, use_container_width=True, key="m8_geo2")
            except Exception as e:
                st.warning("R2 : {}".format(e))

        st.markdown("---")
    
        st.markdown("---")
    
    # --- AFFICHAGE PERSONNALISE AVEC TAILLE DE POLICE MAÎTRISÉE ---
    html_metrics = f"""
    <div style="display: flex; justify-content: space-between; font-family: sans-serif;">
        <div style="text-align: center;">
            <div style="font-size: 13px; color: #888; font-weight: bold;">z1 / z2</div>
            <div style="font-size: 18px; font-weight: bold; color: #333;">{z1} / {z2}</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 13px; color: #888; font-weight: bold;">Rapport i</div>
            <div style="font-size: 18px; font-weight: bold; color: #333;">{z1 / z2 if z2 > 0 else 0:.4f}</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 13px; color: #888; font-weight: bold;">N1</div>
            <div style="font-size: 18px; font-weight: bold; color: #333;">{rpm1:.0f} RPM</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 13px; color: #888; font-weight: bold;">N2</div>
            <div style="font-size: 18px; font-weight: bold; color: #333;">{rpm2:.0f} RPM</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 13px; color: #888; font-weight: bold;">fe</div>
            <div style="font-size: 18px; font-weight: bold; color: #333;">{fe:.1f} Hz</div>
        </div>
    </div>
    """
    st.markdown(html_metrics, unsafe_allow_html=True)

# =============================================================================
# AFFICHAGE CAMPBELL
# =============================================================================
def _display_campbell():
    camp_m = st.session_state.get("m8_camp")
    if not camp_m:
        return st.info("Lancez les calculs.")
    data = st.session_state.get("m8_json_data", {})
    z1 = _get_gear_params(data["rotor1"], "n_teeth")
    z2 = _get_gear_params(data["rotor2"], "n_teeth")
    rpm1 = float(data["rotor1"]["speed_rpm"])
    rpm2 = rpm1 * z1 / z2
    fe = rpm1 / 60 * z1
    vmax = float(st.session_state.get("m8_camp_vmax", 4000))
    try:
        harm = [1]
        if "2X" in st.session_state.get("m8_harmonics", ""):
            harm.append(2)
        harm.append(round(z1/z2, 4))
        fig = camp_m.plot(frequency_units="Hz", harmonics=harm)
        y_max = 600
        try:
            y_max = max(600, float(np.max(camp_m.wn))/(2*np.pi)*1.15)
        except Exception:
            pass
        fig.update_yaxes(range=[0, min(y_max, 800)])
        if "fe" in st.session_state.get("m8_harmoniques", "1X + 2X + fe") and fe < y_max*1.5:
            fig.add_hline(y=fe, line_dash="longdash", line_color="#7B1FA2", line_width=2.5, annotation_text=" fe = {:.0f} Hz".format(fe))
        fig.add_vline(x=rpm1, line_dash="dash", line_color="#1F5C8B", line_width=2, annotation_text=" N1={:.0f} RPM".format(rpm1))
        if rpm2 <= vmax:
            fig.add_vline(x=rpm2, line_dash="dash", line_color="#C55A11", line_width=2, annotation_text=" N2={:.0f} RPM".format(rpm2))
        fig.update_layout(height=550, title="Diagramme de Campbell - MultiRotor couple", plot_bgcolor="white", legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(str(e))


# =============================================================================
# AFFICHAGE MODAL
# =============================================================================
def _display_modal():
    modal_multi = st.session_state.get("m8_modal_multi")

    # Priorite : modes du systeme couple
    if modal_multi is not None:
        st.markdown("**Modes du systeme MultiRotor couple**")
        fn = modal_multi.wn / (2 * np.pi)
        ld = getattr(modal_multi, "log_dec", np.zeros(len(fn)))
        n  = min(12, len(fn))
        df = pd.DataFrame({
            "Mode":    list(range(1, n + 1)),
            "fn (Hz)": ["{:.3f}".format(fn[i]) for i in range(n)],
            "Log Dec": ["{:.4f}".format(ld[i]) for i in range(n)],
            "Statut":  ["INST" if ld[i] <= 0 else "Marg" if ld[i] < 0.1
                        else "OK" for i in range(n)]
        })
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Graphique barres des frequences propres
        data = st.session_state.get("m8_json_data", {})
        z1   = _get_gear_params(data.get("rotor1", {}), "n_teeth")
        rpm1 = float(data.get("rotor1", {}).get("speed_rpm", 1000))
        fe   = rpm1 / 60 * z1
        lbl  = ["M{}".format(i + 1) for i in range(n)]
        fig  = go.Figure()
        fig.add_trace(go.Bar(x=lbl, y=list(fn[:n]), name="Modes couples",
                             marker_color="#1F5C8B"))
        if fe > 0:
            fig.add_hline(y=fe, line_dash="dot", line_color="#7B1FA2",
                          annotation_text="fe={:.1f}Hz".format(fe))
        fig.update_layout(height=320, title="fn systeme couple",
                          plot_bgcolor="white",
                          yaxis=dict(title="fn (Hz)",
                                     showgrid=True, gridcolor="#F0F4FF"))
        st.plotly_chart(fig, use_container_width=True, key="m8_modal_multi_bar")
        return

    # Fallback : modes individuels
    m1 = st.session_state.get("m8_modal1")
    m2 = st.session_state.get("m8_modal2")
    if m1 is None and m2 is None:
        st.info("Lancez les calculs.")
        return

    def _df(modal):
        fn = modal.wn / (2 * np.pi)
        ld = getattr(modal, "log_dec", np.zeros(len(fn)))
        n  = min(8, len(fn))
        return pd.DataFrame({
            "Mode":    list(range(1, n + 1)),
            "fn (Hz)": ["{:.3f}".format(fn[i]) for i in range(n)],
            "Log Dec": ["{:.4f}".format(ld[i]) for i in range(n)],
            "Statut":  ["INST" if ld[i] <= 0 else "Marg" if ld[i] < 0.1
                        else "OK" for i in range(n)]
        })

    r1   = st.session_state.get("m8_rotor1")
    r2   = st.session_state.get("m8_rotor2")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Rotor 1** — {:.2f} kg".format(r1.m if r1 else 0))
        if m1:
            st.dataframe(_df(m1), use_container_width=True, hide_index=True)
            n1   = min(6, len(m1.wn))
            sel1 = st.selectbox("Mode R1 :", list(range(n1)),
                                format_func=lambda x: "M{} {:.2f}Hz".format(
                                    x + 1, m1.wn[x] / (2 * np.pi)),
                                key="m8_ms1")
            for meth in ["plot_mode_3d", "plot_mode_shape"]:
                if hasattr(m1, meth):
                    try:
                        fig = getattr(m1, meth)(mode=sel1)
                        fig.update_layout(height=280)
                        st.plotly_chart(fig, use_container_width=True, key="m8_mf1")
                        break
                    except Exception:
                        continue

    with col2:
        st.markdown("**Rotor 2** — {:.2f} kg".format(r2.m if r2 else 0))
        if m2:
            st.dataframe(_df(m2), use_container_width=True, hide_index=True)
            n2   = min(6, len(m2.wn))
            sel2 = st.selectbox("Mode R2 :", list(range(n2)),
                                format_func=lambda x: "M{} {:.2f}Hz".format(
                                    x + 1, m2.wn[x] / (2 * np.pi)),
                                key="m8_ms2")
            for meth in ["plot_mode_3d", "plot_mode_shape"]:
                if hasattr(m2, meth):
                    try:
                        fig = getattr(m2, meth)(mode=sel2)
                        fig.update_layout(height=280)
                        st.plotly_chart(fig, use_container_width=True, key="m8_mf2")
                        break
                    except Exception:
                        continue

    if m1 and m2:
        fn1  = m1.wn[:6] / (2 * np.pi)
        fn2  = m2.wn[:6] / (2 * np.pi)
        n    = min(len(fn1), len(fn2))
        data = st.session_state.get("m8_json_data", {})
        z1   = _get_gear_params(data.get("rotor1", {}), "n_teeth")
        rpm1 = float(data.get("rotor1", {}).get("speed_rpm", 1000))
        fe   = rpm1 / 60 * z1
        lbl  = ["M{}".format(i + 1) for i in range(n)]
        fig  = go.Figure()
        fig.add_trace(go.Bar(x=lbl, y=fn1[:n], name="R1", marker_color="#1F5C8B"))
        fig.add_trace(go.Bar(x=lbl, y=fn2[:n], name="R2", marker_color="#C55A11"))
        if fe > 0:
            fig.add_hline(y=fe, line_dash="dot", line_color="#7B1FA2",
                          annotation_text="fe={:.1f}Hz".format(fe))
        fig.update_layout(height=320, barmode="group",
                          title="fn R1 vs R2",
                          plot_bgcolor="white",
                          yaxis=dict(title="fn (Hz)",
                                     showgrid=True, gridcolor="#F0F4FF"))
        st.plotly_chart(fig, use_container_width=True, key="m8_modal_bar")


# =============================================================================
# AFFICHAGE REPONSE BALOURD
# =============================================================================
def _display_unbalance():
    res = st.session_state.get("m8_unbal_res")
    if res is None:
        return st.info("Lancez les calculs.")
    
    node = int(st.session_state.get("m8_unbal_node", 2))
    is_x = "X" in st.session_state.get("m8_unb_dof", "Horizontal (X)")
    dof_idx = node * 4 + (0 if is_x else 1)
    plan_label = "X (Horizontal)" if is_x else "Y (Vertical)"

    try:
        # Extraction robuste : forced_resp est une matrice complexe (ndofs x nfrequencies)
        # Ordre ROSS : X0, Y0, A0, B0, X1, Y1, A1, B1...
        forced_resp = np.array(res.forced_resp)
        amps = np.abs(forced_resp[dof_idx, :])
        phases = np.angle(forced_resp[dof_idx, :], deg=True)
        freqs_rad = np.array(res.speed_range)
        freqs_hz = freqs_rad / (2 * np.pi)
    except Exception as e:
        st.error("Erreur d'extraction des donnees : {}".format(e))
        return

    # Création du graphique avec axe secondaire pour la phase
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=freqs_hz, y=amps * 1e6, name="Amplitude",
        line=dict(color="#1F5C8B", width=2), fill="tozeroy", fillcolor="rgba(31,92,139,0.08)"
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=freqs_hz, y=phases, name="Phase",
        line=dict(color="#E64A19", width=1.5, dash="dot")
    ), secondary_y=True)

    # Ajout des résonances modales (individuelles car le balourd est calculé sur un rotor isolé)
    r1 = st.session_state.get("m8_rotor1")
    r2 = st.session_state.get("m8_rotor2")
    selected_rotor = r1 if "1" in st.session_state.get("m8_unb_rotor", "R1") else r2
    m_modal = st.session_state.get("m8_modal1") if "1" in st.session_state.get("m8_unb_rotor", "R1") else st.session_state.get("m8_modal2")
    
    if m_modal:
        for i, wn in enumerate(m_modal.wn[:4]):
            fn = wn / (2 * np.pi)
            fig.add_vline(x=fn, line_dash="dash", line_color="#22863A",
                          annotation_text="f{}={:.1f}Hz".format(i+1, fn),
                          annotation_font=dict(color="#22863A", size=9))

    fig.update_layout(
        height=450, title="Reponse au balourd - Noeud {} ({})".format(node, plan_label),
        plot_bgcolor="white",
        xaxis_title="Frequence (Hz)",
        legend=dict(orientation="h", y=1.1)
    )
    fig.update_yaxes(title_text="Amplitude (um)", secondary_y=False, showgrid=True, gridcolor="#F0F4FF")
    fig.update_yaxes(title_text="Phase (deg)", secondary_y=True, range=[-180, 180])
    
    st.plotly_chart(fig, use_container_width=True, key="m8_unb_fig")

# =============================================================================
# BENCHMARK ROSS PART 4
# =============================================================================
def _display_benchmark():
    st.markdown("### Validation — ROSS Tutorial Part 4")
    st.markdown("""
    <div class="rl-card-info">
      <strong>Benchmark :</strong> Systeme generateur-turbine couple.
      Source : ross.readthedocs.io/tutorial_part_4.<br>
      <small>Timbó R. et al. (2020). JOSS, 5(48), 2120.</small>
    </div>
    """, unsafe_allow_html=True)

    modal_multi = st.session_state.get("m8_modal_multi")
    m1          = st.session_state.get("m8_modal1")
    m2          = st.session_state.get("m8_modal2")

    # Valeurs de reference du systeme couple — Tutorial ROSS Part 4
    ref_couple = [109.0, 116.0, 146.0, 148.0, 276.0, 288.0, 447.0, 519.0]

    if modal_multi is not None:
        # Comparaison avec modes couples
        fn_calc = list(modal_multi.wn[:8] / (2 * np.pi))
        rows = []
        for i in range(min(8, len(fn_calc), len(ref_couple))):
            e = abs(fn_calc[i] - ref_couple[i]) / ref_couple[i] * 100
            rows.append({
                "Mode":          i + 1,
                "fn calc (Hz)":  "{:.3f}".format(fn_calc[i]),
                "fn ref (Hz)":   "{:.3f}".format(ref_couple[i]),
                "Ecart (%)":     "{:.1f}".format(e)
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        errs = [float(r["Ecart (%)"]) for r in rows]
        me   = np.mean(errs) if errs else 0

        n   = len(rows)
        lbl = ["M{}".format(i + 1) for i in range(n)]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=lbl, y=fn_calc[:n], name="Calcule",
                             marker_color="#1F5C8B"))
        fig.add_trace(go.Bar(x=lbl, y=ref_couple[:n], name="Reference ROSS Part 4",
                             marker_color="#90CAF9", marker_pattern_shape="/"))
        fig.update_layout(height=340, barmode="group",
                          title="Calcule vs Reference ROSS Part 4",
                          plot_bgcolor="white",
                          yaxis=dict(title="fn (Hz)",
                                     showgrid=True, gridcolor="#F0F4FF"))
        st.plotly_chart(fig, use_container_width=True, key="m8_bench_fig")

        if me < 5:
            st.markdown("""
            <div class="rl-card-ok">
              <strong>Validation OK</strong> — Ecart moyen : {:.1f}%
            </div>""".format(me), unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="rl-card-warn">
              <strong>Ecart moyen : {:.1f}%</strong>
            </div>""".format(me), unsafe_allow_html=True)

    elif m1 is not None and m2 is not None:
        st.warning("MultiRotor non couple — comparaison sur modes individuels (moins precis)")
        fn1 = list(m1.wn[:4] / (2 * np.pi))
        fn2 = list(m2.wn[:4] / (2 * np.pi))
        ref_r1 = ref_couple[:4]
        ref_r2 = ref_couple[4:8]
        rows = []
        for i in range(min(4, len(fn1), len(fn2))):
            e1 = abs(fn1[i] - ref_r1[i]) / ref_r1[i] * 100
            e2 = abs(fn2[i] - ref_r2[i]) / ref_r2[i] * 100
            rows.append({
                "Mode":         i + 1,
                "fn R1 calc":   "{:.3f}".format(fn1[i]),
                "fn R1 ref":    "{:.3f}".format(ref_r1[i]),
                "Ecart R1 (%)": "{:.1f}".format(e1),
                "fn R2 calc":   "{:.3f}".format(fn2[i]),
                "fn R2 ref":    "{:.3f}".format(ref_r2[i]),
                "Ecart R2 (%)": "{:.1f}".format(e2),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Chargez le modele de reference et lancez les calculs.")

    st.markdown("---")
    _show_ref_params()


def _show_ref_params():
    st.markdown("#### Code de reference ROSS Tutorial Part 4")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Rotor 1 (Generateur)**")
        st.code(
            "L1=[0.3,0.092,0.2,0.2,0.092,0.3] m\n"
            "r1=[0.123,0.15,0.15,0.15,0.15,0.123] m\n"
            "D1: n=0, m=66.63kg, Ip=0.735 kg.m2\n"
            "D2: n=6, m=69.83kg, Ip=0.884 kg.m2\n"
            "G1: n=3, z=37, d_base=0.19m, pr=22.5deg\n"
            "B1: n=2, Kxx=5.5e8, Kyy=6.7e8 N/m\n"
            "B2: n=4, Kxx=5.5e8, Kyy=6.7e8 N/m\n"
            "N1 = 1200 RPM",
            language="python")
    with col2:
        st.markdown("**Rotor 2 (Turbine)**")
        st.code(
            "L2=[0.08,0.2,0.2,0.64] m\n"
            "r2=[0.321,0.321,0.261,0.261] m\n"
            "G2: n=1, z=159, d_base=0.826m, pr=22.5deg\n"
            "B3: n=0, Kxx=3.2e9, Kyy=4.6e9 N/m\n"
            "B4: n=4, Kxx=3.2e9, Kyy=4.6e9 N/m\n"
            "N2 = 279 RPM\n"
            "i = 37/159 = 0.2327\n"
            "fe = 1200/60*37 = 740 Hz",
            language="python")


# =============================================================================
# THEORIE
# =============================================================================
def _display_theory():
    st.markdown("### Theorie des systemes MultiRotors")
    st.markdown("""
**Equation du mouvement global :**

```
[M_global]{q_ddot} + ([C]+[G]){q_dot} + [K_global]{q} = {F(t)}
```

`[K_global]` inclut la raideur de la ligne d action des dents.

**GearElement ROSS :**
```python
gear = rs.GearElement(
    n=3, m=14.37, Id=0.068, Ip=0.136,
    width=0.07,
    n_teeth=37,
    base_diameter=0.19,
    pressure_angle=rs.Q_(22.5, "deg"),
    helix_angle=0.0
)
```

**MultiRotor ROSS :**
```python
multi = rs.MultiRotor(rotors=[rotor1, rotor2])
freq  = rs.Q_(np.linspace(0, 5000, 51), "RPM")
camp  = multi.run_campbell(freq, frequencies=13)
camp.plot(frequency_units="Hz",
          harmonics=[1, round(multi.mesh.gear_ratio, 3)]).show()
```

**Frequences caracteristiques :**

| Frequence | Formule | Description |
|-----------|---------|-------------|
| 1X R1 | N1/60 | Synchrone R1 |
| 1X R2 | N1*z1/(60*z2) | Synchrone R2 |
| fe | N1*z1/60 | Engrenement |
| 2fe, 3fe | Harmoniques | Defaut profil |
| fe +/- fn | Sidelobes | Modulation |

**Modes du systeme couple :**
- Modes lateraux R1 et R2 (flexion de chaque arbre)
- Modes torsionnels (torsion en opposition)
- Modes couples lateral-torsionnel
    """)

    df_types = pd.DataFrame({
        "Type":         ["Droit", "Helicoidal", "Conique", "Epicycloidal"],
        "Angle helice": ["0", "15-45 deg", "Variable", "0"],
        "Rapport max":  ["1:10", "1:8", "1:5", "1:12"],
        "Force axiale": ["Non", "Oui", "Oui", "Non"],
        "Stabilite":    ["Moyenne", "Bonne", "Bonne", "Excellente"]
    })
    st.dataframe(df_types, use_container_width=True, hide_index=True)

# =============================================================================
# AFFICHAGE DIAGNOSTIC
# =============================================================================
# =============================================================================
# AFFICHAGE DIAGNOSTIC
# =============================================================================
def _display_diagnostic():
    """Onglet de diagnostic complet pour le systeme MultiRotor."""
    st.markdown("### Diagnostic du systeme MultiRotor")
    
    r1 = st.session_state.get("m8_rotor1")
    r2 = st.session_state.get("m8_rotor2")
    multi = st.session_state.get("m8_multi")
    modal_multi = st.session_state.get("m8_modal_multi")
    m1 = st.session_state.get("m8_modal1")
    m2 = st.session_state.get("m8_modal2")
    camp = st.session_state.get("m8_camp")
    error = st.session_state.get("m8_error")
    warn = st.session_state.get("m8_multi_warn")
    
    # ── Section 1 : Etat du systeme ──────────────────────────────────────
    st.markdown("#### 1. Etat du systeme")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_r1 = "OK" if r1 is not None else "NON INITIALISE"
        color = "green" if r1 is not None else "red"
        bg = "#e8f5e9" if r1 else "#ffebee"
        st.markdown(f'<div style="padding:10px;background:{bg};border-radius:5px;">'
                    f'<strong>Rotor 1:</strong> <span style="color:{color}">{status_r1}</span>'
                    f'</div>', unsafe_allow_html=True)
    
    with col2:
        status_r2 = "OK" if r2 is not None else "NON INITIALISE"
        color = "green" if r2 is not None else "red"
        bg = "#e8f5e9" if r2 else "#ffebee"
        st.markdown(f'<div style="padding:10px;background:{bg};border-radius:5px;">'
                    f'<strong>Rotor 2:</strong> <span style="color:{color}">{status_r2}</span>'
                    f'</div>', unsafe_allow_html=True)
    
    with col3:
        status_m = "COUPLE" if multi is not None else "NON COUPLE"
        color = "green" if multi is not None else "orange"
        bg = "#e8f5e9" if multi else "#fff3e0"
        st.markdown(f'<div style="padding:10px;background:{bg};border-radius:5px;">'
                    f'<strong>MultiRotor:</strong> <span style="color:{color}">{status_m}</span>'
                    f'</div>', unsafe_allow_html=True)
    
    # ── Section 2 : Erreurs et warnings ──────────────────────────────────
    st.markdown("#### 2. Erreurs et avertissements")
    
    if error:
        st.error("**Erreur principale:**")
        st.code(str(error), language="python")
    else:
        st.success("Aucune erreur principale detectee.")
    
    if warn:
        with st.expander("Details de l'erreur MultiRotor (cliquer pour voir)", expanded=False):
            st.code(str(warn), language="python")
    
    # ── Section 3 : Verifications de coherence ───────────────────────────
    st.markdown("#### 3. Verifications de coherence")
    
    checks = []
    
    if r1 is not None:
        checks.append(("R1 assemble", True, "{} noeuds, {:.2f} kg".format(len(r1.nodes), r1.m)))
    else:
        checks.append(("R1 assemble", False, "Non defini"))
    
    if r2 is not None:
        checks.append(("R2 assemble", True, "{} noeuds, {:.2f} kg".format(len(r2.nodes), r2.m)))
    else:
        checks.append(("R2 assemble", False, "Non defini"))
    
    if multi is not None:
        checks.append(("MultiRotor couple", True, "OK"))
    else:
        checks.append(("MultiRotor couple", False, "Voir erreurs ci-dessus"))
    
    if modal_multi is not None:
        fn_modes = modal_multi.wn / (2 * np.pi)
        checks.append(("Modal couple", True, "{} modes calcules".format(len(fn_modes))))
    else:
        checks.append(("Modal couple", False, "Non calcule"))
    
    if camp is not None:
        checks.append(("Campbell", True, "Calcule"))
    elif st.session_state.get("m8_camp1") is not None:
        checks.append(("Campbell (fallback)", True, "Individuel R1+R2"))
    else:
        checks.append(("Campbell", False, "Non calcule"))
    
    for name, ok, detail in checks:
        icon = "✅" if ok else "❌"
        st.markdown("{} **{}**: {}".format(icon, name, detail))
    
    # ── Section 4 : Analyse des frequences propres ────────────────────────
    st.markdown("#### 4. Analyse des frequences propres")
    
    data = st.session_state.get("m8_json_data", {})
    r1d = data.get("rotor1", {})
    z1 = _get_gear_params(r1d, "n_teeth")
    rpm1 = float(r1d.get("speed_rpm", 1000))
    fe = rpm1 / 60 * z1
    
    if modal_multi is not None:
        fn = modal_multi.wn / (2 * np.pi)
        st.markdown("**Modes du systeme couple:**")
        
        warnings_freq = []
        for i, f in enumerate(fn):
            if fe > 0 and abs(f - fe) / fe < 0.1:
                warnings_freq.append((i+1, f, "PROCHE DE fe"))
            elif fe > 0 and abs(f - 2*fe) / (2*fe) < 0.1:
                warnings_freq.append((i+1, f, "PROCHE DE 2fe"))
        
        if warnings_freq:
            st.warning("⚠️ Modes proches des frequences d'engrenement:")
            for mode, freq, reason in warnings_freq:
                st.markdown("  - Mode {}: {:.2f} Hz → {}".format(mode, freq, reason))
        else:
            st.success("Aucun mode proche de fe ou 2fe (bonne marge)")
    elif m1 is not None and m2 is not None:
        st.info("Modes individuels (systeme non couple - analyse limitee)")
        st.markdown("fe = {:.1f} Hz".format(fe))
    
    # ── Section 5 : Verification du rapport d'engrenage ──────────────────
    st.markdown("#### 5. Verification du rapport d'engrenage")
    
    if r1 is not None and r2 is not None:
        r2d = data.get("rotor2", {})
        z2 = _get_gear_params(r2d, "n_teeth")
        
        if z1 > 0 and z2 > 0:
            ratio_theo = z1 / z2
            ratio_calc = st.session_state.get("m8_gear_ratio", ratio_theo)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("z1", z1)
                st.metric("z2", z2)
            with col2:
                st.metric("Rapport theorique", "{:.4f}".format(ratio_theo))
                if ratio_calc != ratio_theo:
                    st.metric("Rapport calcule (ROSS)", "{:.4f}".format(ratio_calc))
                    ecart = abs(ratio_calc - ratio_theo) / ratio_theo * 100
                    if ecart > 1:
                        st.warning("Ecart rapport: {:.2f}%".format(ecart))
    
    # ── Section 6 : Informations de debug ────────────────────────────────
    st.markdown("#### 6. Informations de debug")
    
    with st.expander("Variables session_state (debug)", expanded=False):
        debug_keys = [k for k in st.session_state.keys() if k.startswith("m8_")]
        for key in sorted(debug_keys):
            val = st.session_state[key]
            if val is None:
                st.markdown("`{}`: `None`".format(key))
            else:
                # Sécurisé : ne dépend pas de l'import de 'rs'
                type_name = type(val).__name__
                st.markdown("`{}`: `{}`".format(key, type_name))
    
    # ── Section 7 : Suggestions ──────────────────────────────────────────
    st.markdown("#### 7. Suggestions")
    
    if multi is None:
        st.markdown("""
        **MultiRotor non couple - causes possibles:**
        1. Version ROSS incompatible - verifier `pip show ross`
        2. API MultiRotor modifiee dans les versions recentes
        3. Parametres gear_mesh_stiffness mal configures
        4. Erreur dans la definition des noeuds couples
        
        **Solution alternative:** Utiliser `GearElement` directement sur chaque rotor
        avec coupling manuel via matrices de raideur.
        """)
    
    if error and "GearElement" in str(error):
        st.markdown("""
        **Erreur GearElement detectee:** Verifier que les parametres
        `pressure_angle` et `helix_angle` sont correctement definis avec
        `rs.Q_(value, "deg")` pour l'angle de pression.
        """)


# =============================================================================
# HELPER LOG
# =============================================================================
def _log(message, level="info"):
    try:
        from app import add_log
        add_log(message, level)
    except Exception:
        pass

