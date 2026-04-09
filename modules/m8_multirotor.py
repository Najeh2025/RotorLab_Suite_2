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
             "width": 0.07,              # ← AJOUTER
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
             "width": 0.20,              # ← AJOUTER
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
    st.markdown('<div class="rl-section-header">Source du modele</div>',
                unsafe_allow_html=True)

    source = st.radio(
        "Source :",
        ["Modele de reference (ROSS Tutorial Part 4)", "Charger un fichier JSON"],
        key="m8_source")

    if source == "Modele de reference (ROSS Tutorial Part 4)":
        st.markdown("""
        <div class="rl-card-info">
          <strong>Benchmark ROSS Tutorial Part 4</strong><br>
          <small>Generateur-turbine couple par engrenage droit 22.5 deg.<br>
          R1 : 7 noeuds | R2 : 5 noeuds | z1=37, z2=159, i=0.2327<br>
          N1=1200 RPM, N2=279 RPM, fe=740 Hz</small>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Charger le modele de reference", type="primary",
                     key="m8_load_ref", use_container_width=True):
            st.session_state["m8_json_data"]   = REFERENCE_JSON
            st.session_state["m8_loaded"]      = True
            st.session_state["m8_source_name"] = "ROSS Tutorial Part 4"
            _clear_results()
            _log("Modele reference ROSS Part 4 charge", "ok")

        st.download_button(
            "Telecharger le JSON de reference",
            data=json.dumps(REFERENCE_JSON, indent=2),
            file_name="ross_tutorial_part4.json",
            mime="application/json",
            key="m8_dl_ref")

    else:
        st.markdown("""
        <div class="rl-card-info">
          <small>Telechargez d'abord le JSON de reference pour voir
          la structure attendue (shaft, disks, gear_elements, bearings).</small>
        </div>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Fichier JSON MultiRotor",
            type=["json"],
            label_visibility="collapsed",
            key="m8_upload")

        if uploaded is not None:
            file_id = "{}_{}".format(uploaded.name, uploaded.size)
            if st.session_state.get("m8_last_file_id") != file_id:
                try:
                    data = json.loads(uploaded.read().decode("utf-8"))
                    _validate_json(data)
                    st.session_state["m8_json_data"]    = data
                    st.session_state["m8_loaded"]       = True
                    st.session_state["m8_last_file_id"] = file_id
                    st.session_state["m8_source_name"]  = data.get(
                        "name", uploaded.name)
                    _clear_results()
                    st.success("Charge : {}".format(
                        st.session_state["m8_source_name"]))
                    _log("JSON charge", "ok")
                except Exception as e:
                    st.error("Erreur JSON : {}".format(e))

    # Resume modele charge
    if st.session_state.get("m8_loaded") and \
            st.session_state.get("m8_json_data"):
        _show_model_summary()


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

    st.markdown('<div class="rl-section-header">Reponse au balourd</div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Magnitude (kg.m)", 1e-6, 1.0, 1e-3,
                        format="%.4f", key="m8_unb_mag")
    with c2:
        st.radio("Rotor", ["Rotor 1", "Rotor 2"],
                 key="m8_unb_rotor", horizontal=True)


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

    if st.session_state.get("m8_error"):
        st.error(st.session_state["m8_error"])

    checks = [
        ("m8_rotor1",   "Rotor 1 assemble"),
        ("m8_rotor2",   "Rotor 2 assemble"),
        ("m8_multi",    "MultiRotor couple"),
        ("m8_modal1",   "Modal Rotor 1"),
        ("m8_modal2",   "Modal Rotor 2"),
        ("m8_camp",     "Campbell MultiRotor"),
        ("m8_unbal_res","Reponse au balourd"),
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

    tab_geo, tab_camp, tab_modal, tab_unbal, tab_bench, tab_theory = st.tabs([
        "Geometrie", "Campbell couple", "Analyse modale",
        "Reponse balourd", "Benchmark", "Theorie"
    ])

    with tab_geo:    _display_geometry()
    with tab_camp:   _display_campbell()
    with tab_modal:  _display_modal()
    with tab_unbal:  _display_unbalance()
    with tab_bench:  _display_benchmark()
    with tab_theory: _display_theory()


# =============================================================================
# UTILITAIRES
# =============================================================================
def _clear_results():
    for k in ["m8_rotor1","m8_rotor2","m8_multi","m8_modal1","m8_modal2",
              "m8_camp","m8_camp1","m8_camp2","m8_unbal_res",
              "m8_error","m8_multi_warn"]:
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


def _get_gear_params(rotor_data, key):
    gears = rotor_data.get("gear_elements", [])
    if gears:
        return gears[0].get(key, 0)
    return 0


# =============================================================================
# CONSTRUCTION DEPUIS JSON
# =============================================================================
def _build_rotor_from_json(rotor_data, mat):
    shaft = []
    for el in rotor_data["shaft"]:
        shaft.append(rs.ShaftElement(
            L=float(el["L"]), idl=float(el.get("idl",0.0)),
            odl=float(el["odl"]),
            idr=float(el.get("idr", el.get("idl",0.0))),
            odr=float(el.get("odr", el["odl"])),
            material=mat, shear_effects=True,
            rotary_inertia=True, gyroscopic=True))

    disks = []
    for d in rotor_data.get("disks", []):
        disks.append(rs.DiskElement(
            n=int(d["n"]), m=float(d["m"]),
            Id=float(d["Id"]), Ip=float(d["Ip"])))

    for g in rotor_data.get("gear_elements", []):
        try:
            gear = rs.GearElement(
                n=int(g["n"]),
                m=float(g["m"]),
                Id=float(g["Id"]),
                Ip=float(g["Ip"]),
                width=float(g.get("width", 0.07)),   # ← AJOUT OBLIGATOIRE
                n_teeth=int(g["n_teeth"]),
                base_diameter=float(g["base_diameter"]),
                pressure_angle=rs.Q_(float(g.get("pressure_angle_deg", 22.5)), "deg"),  # ← "pressure_angle" pas "pr_angle"
                helix_angle=float(g.get("helix_angle_deg", 0.0))
                )
            disks.append(gear)
        except Exception as e:
            _log("GearElement fallback : {}".format(e), "warn")
            disks.append(rs.DiskElement(
                n=int(g["n"]), m=float(g["m"]),
                Id=float(g["Id"]), Ip=float(g["Ip"])))

    bears = []
    for b in rotor_data["bearings"]:
        bears.append(rs.BearingElement(
            n=int(b["n"]),
            kxx=float(b["kxx"]), kyy=float(b.get("kyy",b["kxx"])),
            kxy=float(b.get("kxy",0.0)), kyx=float(b.get("kyx",0.0)),
            cxx=float(b.get("cxx",500.0)),
            cyy=float(b.get("cyy",b.get("cxx",500.0)))))

    return rs.Rotor(shaft, disks, bears)


# =============================================================================
# CALCUL PRINCIPAL
# =============================================================================
def _run_all():
    if not st.session_state.get("m8_loaded") or \
            not st.session_state.get("m8_json_data"):
        st.session_state["m8_error"] = "Aucun modele charge."
        return
    if not ROSS_OK:
        st.session_state["m8_error"] = "ROSS non disponible."
        return

    data = st.session_state["m8_json_data"]
    mat_d = data.get("material",
                     {"name":"Steel","rho":7810,"E":211e9,"G_s":81.2e9})
    mat = rs.Material(
        name=str(mat_d.get("name","Steel")).replace(" ","_"),
        rho=float(mat_d["rho"]), E=float(mat_d["E"]),
        G_s=float(mat_d["G_s"]))

    try:
        r1 = _build_rotor_from_json(data["rotor1"], mat)
        r2 = _build_rotor_from_json(data["rotor2"], mat)
        st.session_state["m8_rotor1"] = r1
        st.session_state["m8_rotor2"] = r2
        st.session_state["m8_error"]  = None
        _log("R1:{} noeuds {:.1f}kg | R2:{} noeuds {:.1f}kg".format(
            len(r1.nodes), r1.m, len(r2.nodes), r2.m), "ok")

        vmax    = float(st.session_state.get("m8_vmax", 4000))
        npts    = int(st.session_state.get("m8_npts", 25))
        n_modes = int(st.session_state.get("m8_n_modes", 12))
        speeds  = np.linspace(0, vmax * np.pi / 30, npts)

        # MultiRotor couple
        try:
            multi = rs.MultiRotor(rotors=[r1, r2])
            st.session_state["m8_multi"] = multi
            frequency_range = rs.Q_(np.linspace(0, vmax, npts), "RPM")  # ← REMPLACER speeds par frequency_range en RPM
            camp = multi.run_campbell(frequency_range, frequencies=n_modes)
            st.session_state["m8_camp"]      = camp
            st.session_state["m8_camp_vmax"] = vmax
            st.session_state["m8_gear_ratio"] = multi.mesh.gear_ratio    # ← AJOUTER cette ligne
            _log("MultiRotor couple calcule", "ok")
        except Exception as e_m:
            st.session_state["m8_error"] = "MultiRotor ERREUR: {}".format(e_m)
            _log("MultiRotor: {} -> Campbell individuel".format(e_m), "warn")
            st.session_state["m8_multi_warn"] = str(e_m)
            z1 = _get_gear_params(data["rotor1"], "n_teeth")
            z2 = _get_gear_params(data["rotor2"], "n_teeth")
            ratio = z1/z2 if z2 > 0 else 1.0
            camp1 = r1.run_campbell(speeds, frequencies=n_modes)
            camp2 = r2.run_campbell(speeds * ratio, frequencies=n_modes)
            st.session_state["m8_camp1"]     = camp1
            st.session_state["m8_camp2"]     = camp2
            st.session_state["m8_camp_vmax"] = vmax
            _log("Campbell R1+R2 calcules", "ok")

        # Modales
        # Modes individuels (gardés pour le fallback)
        st.session_state["m8_modal1"] = r1.run_modal(speed=0)
        st.session_state["m8_modal2"] = r2.run_modal(speed=0)
        
        # Modes du système couplé si MultiRotor disponible
        multi = st.session_state.get("m8_multi")
        if multi is not None:
            try:
                st.session_state["m8_modal_multi"] = multi.run_modal(speed=0)
                _log("Modal MultiRotor couple calcule", "ok")
            except Exception as e:
                _log("Modal MultiRotor : {}".format(e), "warn")
                _log("Analyses modales terminees", "ok")

        # Balourd
        _run_unbalance_calc(r1, r2)

    except Exception as e:
        st.session_state["m8_error"] = str(e)
        _log("Erreur : {}".format(e), "err")


def _run_unbalance_calc(r1, r2):
    try:
        unb_mag  = float(st.session_state.get("m8_unb_mag", 1e-3))
        vmax     = float(st.session_state.get("m8_vmax", 4000))
        rotor_s  = r1 if "1" in st.session_state.get("m8_unb_rotor", "R1") \
                   else r2
        node_m   = len(rotor_s.nodes) // 2

        freqs_rad = np.linspace(0, vmax * np.pi / 30, 300)  # ← rad/s

        res = rotor_s.run_unbalance_response(
            node=[node_m],
            unbalance_magnitude=[unb_mag],
            unbalance_phase=[0.0],
            frequency=freqs_rad
        )

        st.session_state["m8_unbal_res"]  = res
        st.session_state["m8_unbal_node"] = node_m
        _log("Balourd calcule (N{})".format(node_m), "ok")

    except Exception as e:
        _log("Balourd : {}".format(e), "warn")


# =============================================================================
# AFFICHAGE GEOMETRIE
# =============================================================================
def _display_geometry():
    r1 = st.session_state.get("m8_rotor1")
    r2 = st.session_state.get("m8_rotor2")
    if r1 is None or r2 is None:
        st.info("Chargez un modele et lancez les calculs.")
        return

    data  = st.session_state.get("m8_json_data", {})
    r1d   = data.get("rotor1", {})
    r2d   = data.get("rotor2", {})
    z1    = _get_gear_params(r1d, "n_teeth")
    z2    = _get_gear_params(r2d, "n_teeth")
    rpm1  = float(r1d.get("speed_rpm", 1000))
    rpm2  = rpm1 * z1 / z2 if z2 > 0 else 0
    fe    = rpm1 / 60 * z1

    multi = st.session_state.get("m8_multi")

    if multi is not None:
        # ✅ Schéma couplé comme dans le tutorial
        try:
            fig = multi.plot_rotor()
            fig.update_layout(
                height=350,
                title="MultiRotor couplé — R1 + R2",
                font=dict(size=11),          # ← taille police réduite
                margin=dict(l=0,r=0,t=40,b=0)
            )
            st.plotly_chart(fig, use_container_width=True, key="m8_geo_multi")
        except Exception as e:
            st.warning("plot_rotor MultiRotor : {}".format(e))
    else:
        # Fallback si MultiRotor non disponible
        st.warning("MultiRotor non couplé — affichage individuel")
        col1, col2 = st.columns(2)
        with col1:
            fig1 = r1.plot_rotor()
            fig1.update_layout(height=260, font=dict(size=10))
            st.plotly_chart(fig1, use_container_width=True, key="m8_geo1")
        with col2:
            fig2 = r2.plot_rotor()
            fig2.update_layout(height=260, font=dict(size=10))
            st.plotly_chart(fig2, use_container_width=True, key="m8_geo2")

    st.markdown("---")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("z1 / z2",    "{} / {}".format(z1, z2))
    c2.metric("Rapport i",  "{:.4f}".format(z1/z2 if z2>0 else 0))
    c3.metric("N1",         "{:.0f} RPM".format(rpm1))
    c4.metric("N2",         "{:.0f} RPM".format(rpm2))
    c5.metric("fe",         "{:.1f} Hz".format(fe))

    warn = st.session_state.get("m8_multi_warn")
    if warn:
        st.markdown("""
        <div class="rl-card-warn">
          <strong>Note :</strong> MultiRotor : <code>{}</code><br>
          Campbells individuels affiches.
        </div>""".format(warn), unsafe_allow_html=True)


# =============================================================================
# AFFICHAGE CAMPBELL
# =============================================================================
def _display_campbell():
    camp_m = st.session_state.get("m8_camp")
    camp1  = st.session_state.get("m8_camp1")
    camp2  = st.session_state.get("m8_camp2")
    if camp_m is None and camp1 is None:
        st.info("Lancez les calculs.")
        return

    data  = st.session_state.get("m8_json_data", {})
    r1d   = data.get("rotor1", {})
    r2d   = data.get("rotor2", {})
    z1    = _get_gear_params(r1d, "n_teeth")
    z2    = _get_gear_params(r2d, "n_teeth")
    rpm1  = float(r1d.get("speed_rpm", 1000))
    rpm2  = rpm1 * z1/z2 if z2 > 0 else 0
    fe    = rpm1/60 * z1
    vmax  = float(st.session_state.get("m8_camp_vmax", 4000))
    harms = st.session_state.get("m8_harmonics", "1X + 2X + fe")

    CR1 = ["#1F5C8B","#0288D1","#00796B","#388E3C","#1565C0","#006064"]
    CR2 = ["#C55A11","#E64A19","#C62828","#AD1457","#6A1B9A","#00695C"]

    # Si MultiRotor couplé disponible → utiliser l'API native ROSS
    if camp_m is not None:
        gear_ratio = st.session_state.get("m8_gear_ratio", 0.2327)
        fig = camp_m.plot(
            frequency_units="Hz",
            harmonics=[1, round(gear_ratio, 3)]
        )
        fig.update_layout(height=480)
        st.plotly_chart(fig, use_container_width=True, key="m8_camp_fig")

    # Sinon fallback : Campbell individuels R1 + R2
    else:
        fig = go.Figure()

        def _add(camp, colors, prefix):
            # ... garder votre code existant tel quel ...
    df_f = pd.DataFrame({
        "Grandeur": ["N1","N2","i = z1/z2","fe","2fe","3fe"],
        "Valeur": [
            "{:.0f} RPM".format(rpm1), "{:.0f} RPM".format(rpm2),
            "{}/{} = {:.4f}".format(z1,z2,z1/z2 if z2>0 else 0),
            "{:.2f} Hz".format(fe), "{:.2f} Hz".format(2*fe),
            "{:.2f} Hz".format(3*fe)]
    })
    st.dataframe(df_f, use_container_width=True, hide_index=True)


# =============================================================================
# AFFICHAGE MODAL
# =============================================================================
def _display_modal():
     modal_multi = st.session_state.get("m8_modal_multi")

    # ✅ Priorité : modes du système couplé
    if modal_multi is not None:
        st.markdown("**Modes du système MultiRotor couplé**")
        fn = modal_multi.wn / (2 * np.pi)
        ld = getattr(modal_multi, 'log_dec', np.zeros(len(fn)))
        n  = min(12, len(fn))
        df = pd.DataFrame({
            "Mode":    list(range(1, n+1)),
            "fn (Hz)": ["{:.3f}".format(fn[i]) for i in range(n)],
            "Log Dec": ["{:.4f}".format(ld[i]) for i in range(n)],
            "Statut":  ["INST" if ld[i]<=0 else "Marg" if ld[i]<0.1
                        else "OK" for i in range(n)]
        })
        st.dataframe(df, use_container_width=True, hide_index=True)
        return   # ← ne pas afficher les modes individuels en dessous
    m1 = st.session_state.get("m8_modal1")
    m2 = st.session_state.get("m8_modal2")
    if m1 is None and m2 is None:
        st.info("Lancez les calculs.")
        return

    def _df(modal):
        fn = modal.wn / (2*np.pi)
        ld = getattr(modal,'log_dec', np.zeros(len(fn)))
        n  = min(8, len(fn))
        return pd.DataFrame({
            "Mode":    list(range(1,n+1)),
            "fn (Hz)": ["{:.3f}".format(fn[i]) for i in range(n)],
            "Log Dec": ["{:.4f}".format(ld[i]) for i in range(n)],
            "Statut":  ["INST" if ld[i]<=0 else "Marg" if ld[i]<0.1
                        else "OK" for i in range(n)]
        })

    col1, col2 = st.columns(2)
    r1 = st.session_state.get("m8_rotor1")
    r2 = st.session_state.get("m8_rotor2")

    with col1:
        st.markdown("**Rotor 1** — {:.2f} kg".format(r1.m if r1 else 0))
        if m1:
            st.dataframe(_df(m1), use_container_width=True, hide_index=True)
            n1 = min(6, len(m1.wn))
            sel1 = st.selectbox("Mode R1 :", list(range(n1)),
                format_func=lambda x: "M{} {:.2f}Hz".format(
                    x+1, m1.wn[x]/(2*np.pi)), key="m8_ms1")
            for meth in ["plot_mode_3d","plot_mode_shape"]:
                if hasattr(m1, meth):
                    try:
                        fig = getattr(m1, meth)(mode=sel1)
                        fig.update_layout(height=280)
                        st.plotly_chart(fig, use_container_width=True,
                                        key="m8_mf1")
                        break
                    except Exception: continue

    with col2:
        st.markdown("**Rotor 2** — {:.2f} kg".format(r2.m if r2 else 0))
        if m2:
            st.dataframe(_df(m2), use_container_width=True, hide_index=True)
            n2 = min(6, len(m2.wn))
            sel2 = st.selectbox("Mode R2 :", list(range(n2)),
                format_func=lambda x: "M{} {:.2f}Hz".format(
                    x+1, m2.wn[x]/(2*np.pi)), key="m8_ms2")
            for meth in ["plot_mode_3d","plot_mode_shape"]:
                if hasattr(m2, meth):
                    try:
                        fig = getattr(m2, meth)(mode=sel2)
                        fig.update_layout(height=280)
                        st.plotly_chart(fig, use_container_width=True,
                                        key="m8_mf2")
                        break
                    except Exception: continue

    if m1 and m2:
        fn1 = m1.wn[:6]/(2*np.pi)
        fn2 = m2.wn[:6]/(2*np.pi)
        n   = min(len(fn1), len(fn2))
        data = st.session_state.get("m8_json_data", {})
        z1   = _get_gear_params(data.get("rotor1",{}), "n_teeth")
        rpm1 = float(data.get("rotor1",{}).get("speed_rpm", 1000))
        fe   = rpm1/60*z1
        labels = ["M{}".format(i+1) for i in range(n)]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=labels, y=fn1[:n], name="R1",
                             marker_color="#1F5C8B"))
        fig.add_trace(go.Bar(x=labels, y=fn2[:n], name="R2",
                             marker_color="#C55A11"))
        if fe > 0:
            fig.add_hline(y=fe, line_dash="dot", line_color="#7B1FA2",
                          annotation_text="fe={:.1f}Hz".format(fe),
                          annotation_font=dict(color="#7B1FA2"))
        fig.update_layout(height=320, barmode="group",
                          title="fn R1 vs R2 (fe={:.1f}Hz)".format(fe),
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
        st.info("Lancez les calculs.")
        return

    node  = int(st.session_state.get("m8_unbal_node", 2))
    freqs = None
    for attr in ("speed_range","frequency","frequency_range"):
        if hasattr(res, attr) and getattr(res, attr) is not None:
            freqs = np.array(getattr(res, attr))
            if "speed" in attr: freqs = freqs/(2*np.pi)
            break
    if freqs is None:
        freqs = np.linspace(0, 100, 300)

    amps = None
    # Lecture des fréquences depuis le résultat
    freqs_hz = np.array(res.speed_range) / (2 * np.pi)   # rad/s → Hz
    
    # Lecture des amplitudes — API ROSS actuelle
    try:
        from ross import Probe
        probe = Probe(node, 0)    # nœud, angle 0° = direction X
        amps = res.data_magnitude(probe=probe)
        except Exception:
            # Fallback lecture directe
            arr = np.abs(np.array(res.forced_resp))
            dof = min(node * 4, arr.shape[0] - 1)
            amps = arr[dof, :]

    if amps is None:
        for attr in ("forced_resp","response"):
            if hasattr(res, attr):
                arr = np.abs(np.array(getattr(res, attr)))
                if arr.ndim == 2:
                    dof = min(node*4, arr.shape[0]-1)
                    amps = arr[dof, :]
                else:
                    amps = arr
                break

    if amps is None:
        st.warning("Donnees indisponibles.")
        return

    n = min(len(amps), len(freqs))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=freqs[:n], y=amps[:n]*1e6,
        line=dict(color="#1F5C8B", width=2),
        fill="tozeroy", fillcolor="rgba(31,92,139,0.08)",
        hovertemplate="f=%{x:.1f}Hz | A=%{y:.4f}µm<extra></extra>"))
    m1 = st.session_state.get("m8_modal1")
    if m1:
        for i, wn in enumerate(m1.wn[:4]):
            fn = wn/(2*np.pi)
            fig.add_vline(x=fn, line_dash="dot", line_color="#22863A",
                          annotation_text="M{}".format(i+1),
                          annotation_font=dict(color="#22863A",size=10))
    fig.update_layout(height=400,
                      title="Balourd — N{} ({})".format(
                          node, st.session_state.get("m8_unb_rotor","R1")),
                      xaxis_title="Frequence (Hz)",
                      yaxis_title="Amplitude (µm)",
                      plot_bgcolor="white",
                      xaxis=dict(showgrid=True, gridcolor="#F0F4FF"),
                      yaxis=dict(showgrid=True, gridcolor="#F0F4FF"))
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

    m1 = st.session_state.get("m8_modal1")
    m2 = st.session_state.get("m8_modal2")

    # Valeurs de reference (lecture tutorial ROSS Part 4)
    ref_r1 = [11.6, 17.3, 42.8, 65.1]
    ref_r2 = [ 8.4, 14.1, 31.2, 55.7]
    # Fréquences propres du système couplé — Tutorial ROSS Part 4
    # Source : Timbó et al. 2020, modèle générateur-turbine
    ref_couplé = [109.0, 116.0, 146.0, 148.0, 276.0, 288.0, 447.0, 519.0]

    if m1 is None or m2 is None:
        st.info("Chargez le modele de reference et lancez les calculs.")
        _show_ref_params()
        return

    fn1 = list(m1.wn[:4]/(2*np.pi))
    fn2 = list(m2.wn[:4]/(2*np.pi))

    rows = []
    for i in range(min(4, len(fn1), len(fn2))):
        e1 = abs(fn1[i]-ref_r1[i])/ref_r1[i]*100 if i<len(ref_r1) else 0
        e2 = abs(fn2[i]-ref_r2[i])/ref_r2[i]*100 if i<len(ref_r2) else 0
        rows.append({
            "Mode":          i+1,
            "fn R1 calc":    "{:.3f}".format(fn1[i]),
            "fn R1 ref":     "{:.3f}".format(ref_r1[i] if i<len(ref_r1) else 0),
            "Ecart R1 (%)":  "{:.1f}".format(e1),
            "fn R2 calc":    "{:.3f}".format(fn2[i]),
            "fn R2 ref":     "{:.3f}".format(ref_r2[i] if i<len(ref_r2) else 0),
            "Ecart R2 (%)":  "{:.1f}".format(e2),
        })
    st.dataframe(pd.DataFrame(rows),
                 use_container_width=True, hide_index=True)

    n = len(rows)
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=["Rotor 1","Rotor 2"])
    lbl = ["M{}".format(i+1) for i in range(n)]
    fig.add_trace(go.Bar(x=lbl, y=fn1[:n], name="Calcule R1",
                         marker_color="#1F5C8B"), row=1, col=1)
    fig.add_trace(go.Bar(x=lbl, y=ref_r1[:n], name="Reference R1",
                         marker_color="#90CAF9",
                         marker_pattern_shape="/"), row=1, col=1)
    fig.add_trace(go.Bar(x=lbl, y=fn2[:n], name="Calcule R2",
                         marker_color="#C55A11"), row=1, col=2)
    fig.add_trace(go.Bar(x=lbl, y=ref_r2[:n], name="Reference R2",
                         marker_color="#FFCCBC",
                         marker_pattern_shape="/"), row=1, col=2)
    fig.update_layout(height=340, barmode="group",
                      title="Calcule vs Reference ROSS Part 4",
                      plot_bgcolor="white",
                      yaxis=dict(title="fn (Hz)",
                                 showgrid=True, gridcolor="#F0F4FF"),
                      yaxis2=dict(title="fn (Hz)",
                                  showgrid=True, gridcolor="#F0F4FF"))
    st.plotly_chart(fig, use_container_width=True, key="m8_bench_fig")

    errs = [float(r["Ecart R1 (%)"]) for r in rows] + \
           [float(r["Ecart R2 (%)"]) for r in rows]
    me = np.mean(errs) if errs else 0
    if me < 5:
        st.markdown("""
        <div class="rl-card-ok">
          <strong>Validation OK</strong> — Ecart moyen : {:.1f}%
        </div>""".format(me), unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="rl-card-warn">
          <strong>Ecart : {:.1f}%</strong> (valeurs ref. approx. du tutoriel)
        </div>""".format(me), unsafe_allow_html=True)

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
    n=3,                       # Noeud sur le rotor
    m=14.37,                   # Masse (kg)
    Id=0.068, Ip=0.136,        # Inerties (kg.m2)
    n_teeth=37,                # Nombre de dents
    base_diameter=0.19,        # Diametre de base (m)
    pr_angle=rs.Q_(22.5,"deg"),# Angle de pression
    helix_angle=0.0            # 0 = droit
)
```

**MultiRotor ROSS :**
```python
multi = rs.MultiRotor(rotors=[r1, r2])
frequency_range = rs.Q_(np.linspace(0, vmax, npts), "RPM")  # ← Q_() en RPM
camp = multi.run_campbell(frequency_range, frequencies=n_modes)
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
        "Type":         ["Droit","Helicoidal","Conique","Epicycloidal"],
        "Angle helice": ["0","15-45 deg","Variable","0"],
        "Rapport max":  ["1:10","1:8","1:5","1:12"],
        "Force axiale": ["Non","Oui","Oui","Non"],
        "Stabilite":    ["Moyenne","Bonne","Bonne","Excellente"]
    })
    st.dataframe(df_types, use_container_width=True, hide_index=True)


# =============================================================================
# HELPER LOG
# =============================================================================
def _log(message, level="info"):
    try:
        from app import add_log
        add_log(message, level)
    except Exception:
        pass
