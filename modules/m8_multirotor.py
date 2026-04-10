# modules/m8_multirotor.py - MultiRotor & GearElement v2
# RotorLab Suite 2.0 - Pr. Najeh Ben Guedria
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
# MODELE DE REFERENCE
# =============================================================================
REFERENCE_JSON = {
    "name": "ROSS Tutorial Part 4 - Reference MultiRotor",
    "material": {"name": "Steel", "rho": 7810, "E": 211e9, "G_s": 81.2e9},
    "rotor1": {
        "description": "Rotor moteur",
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
             "width": 0.07, "n_teeth": 37, "base_diameter": 0.19,
             "pressure_angle_deg": 22.5, "helix_angle_deg": 0.0}
        ],
        "bearings": [
            {"n": 2, "kxx": 5.5e8, "kyy": 6.7e8, "cxx": 3e3, "cyy": 3e3},
            {"n": 4, "kxx": 5.5e8, "kyy": 6.7e8, "cxx": 3e3, "cyy": 3e3}
        ],
        "speed_rpm": 1200.0
    },
    "rotor2": {
        "description": "Rotor recepteur",
        "shaft": [
            {"L": 0.080, "idl": 0.0, "odl": 0.321, "idr": 0.0, "odr": 0.321},
            {"L": 0.200, "idl": 0.0, "odl": 0.321, "idr": 0.0, "odr": 0.321},
            {"L": 0.200, "idl": 0.0, "odl": 0.261, "idr": 0.0, "odr": 0.261},
            {"L": 0.640, "idl": 0.0, "odl": 0.261, "idr": 0.0, "odr": 0.261}
        ],
        "disks": [],
        "gear_elements": [
            {"n": 1, "m": 322.0, "Id": 24.17, "Ip": 48.34,
             "width": 0.20, "n_teeth": 159, "base_diameter": 0.826,
             "pressure_angle_deg": 22.5, "helix_angle_deg": 0.0}
        ],
        "bearings": [
            {"n": 0, "kxx": 3.2e9, "kyy": 4.6e9, "cxx": 3e3, "cyy": 3e3},
            {"n": 4, "kxx": 3.2e9, "kyy": 4.6e9, "cxx": 3e3, "cyy": 3e3}
        ],
        "speed_rpm": 279.0
    }
}

def render_m8(col_settings, col_graphics):
    with col_settings:
        _render_settings()
    with col_graphics:
        _render_graphics()

def _render_settings():
    st.markdown('<div class="rl-settings-title">MultiRotor & GearElement [NEW]</div>', unsafe_allow_html=True)
    st.markdown('<span class="rl-badge rl-badge-new">NEW v2.0</span>', unsafe_allow_html=True)
    tab_load, tab_params, tab_run = st.tabs(["Chargement du modele", "Parametres de calcul", "Statut & Actions"])
    with tab_load: _render_tab_load()
    with tab_params: _render_tab_params()
    with tab_run: _render_tab_run()

def _render_tab_load():
    st.markdown('<div class="rl-section-header">Source du modele</div>', unsafe_allow_html=True)
    source = st.radio("Source :", ["Modele de reference (ROSS Tutorial Part 4)", "Charger un fichier JSON"], key="m8_source")
    if source == "Modele de reference (ROSS Tutorial Part 4)":
        if st.button("Charger le modele de reference", type="primary", key="m8_load_ref", use_container_width=True):
            st.session_state["m8_json_data"] = REFERENCE_JSON
            st.session_state["m8_loaded"] = True
            st.session_state["m8_source_name"] = "ROSS Tutorial Part 4"
            _clear_results()
            _log("Modele reference charge", "ok")
        st.download_button("Telecharger le JSON de reference", data=json.dumps(REFERENCE_JSON, indent=2), file_name="ross_tutorial_part4.json", mime="application/json", key="m8_dl_ref")
    else:
        uploaded = st.file_uploader("Fichier JSON MultiRotor", type=["json"], label_visibility="collapsed", key="m8_upload")
        if uploaded is not None:
            try:
                data = json.loads(uploaded.read().decode("utf-8"))
                st.session_state["m8_json_data"] = data
                st.session_state["m8_loaded"] = True
                st.session_state["m8_source_name"] = data.get("name", uploaded.name)
                _clear_results()
                st.success("Charge : {}".format(st.session_state["m8_source_name"]))
            except Exception as e:
                st.error("Erreur JSON : {}".format(e))
    if st.session_state.get("m8_loaded") and st.session_state.get("m8_json_data"):
        _show_model_summary()

def _show_model_summary():
    data = st.session_state["m8_json_data"]
    z1 = data["rotor1"]["gear_elements"][0]["n_teeth"] if data["rotor1"].get("gear_elements") else 1
    z2 = data["rotor2"]["gear_elements"][0]["n_teeth"] if data["rotor2"].get("gear_elements") else 1
    rpm1 = float(data["rotor1"].get("speed_rpm", 1000))
    st.caption("R1: {} el | z={} | R2: {} el | z={} | i={:.4f}".format(len(data["rotor1"].get("shaft",[])), z1, len(data["rotor2"].get("shaft",[])), z2, z1/z2))

def _render_tab_params():
    st.markdown('<div class="rl-section-header">Parametres Campbell</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Vitesse max (RPM)", 500.0, 30000.0, 4000.0, step=500.0, key="m8_vmax")
        st.slider("Resolution (points)", 10, 80, 25, key="m8_npts")
    with c2:
        st.slider("Nombre de modes", 4, 24, 12, key="m8_n_modes")
        st.radio("Harmoniques", ["1X", "1X + 2X", "1X + 2X + fe"], index=2, horizontal=True, key="m8_harmonics")
    st.markdown('<div class="rl-section-header">Reponse au balourd</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Magnitude (kg.m)", 1e-6, 1.0, 1e-3, format="%.4f", key="m8_unb_mag")
    with c2:
        st.radio("Rotor", ["Rotor 1", "Rotor 2"], key="m8_unb_rotor", horizontal=True)

def _render_tab_run():
    if not st.session_state.get("m8_loaded"):
        st.warning("Chargez un modele.")
        return
    st.success("Modele : {}".format(st.session_state.get("m8_source_name", "--")))
    st.button("Assembler et lancer tous les calculs", type="primary", key="m8_run_all", use_container_width=True, on_click=_run_all)
    if st.session_state.get("m8_error"):
        st.error(st.session_state["m8_error"])
    checks = [("m8_rotor1","Rotor 1"), ("m8_rotor2","Rotor 2"), ("m8_multi","MultiRotor couple"), ("m8_camp","Campbell")]
    for k, l in checks:
        st.caption("[{}] {}".format("OK" if st.session_state.get(k) else "...", l))

def _render_graphics():
    st.markdown('<div class="rl-graphics-title">MultiRotor - Results</div>', unsafe_allow_html=True)
    tabs = st.tabs(["Geometrie", "Campbell couple", "Analyse modale", "Reponse balourd", "Benchmark", "Theorie", "Diagnostic"])
    tab_geo, tab_camp, tab_modal, tab_unbal, tab_bench, tab_theory, tab_diag = tabs
    with tab_geo: _display_geometry()
    with tab_camp: _display_campbell()
    with tab_modal: _display_modal()
    with tab_unbal: _display_unbalance()
    with tab_bench: _display_benchmark()
    with tab_theory: _display_theory()
    with tab_diag: _display_diagnostic()

def _clear_results():
    for k in ["m8_rotor1", "m8_rotor2", "m8_multi", "m8_modal1", "m8_modal2", "m8_modal_multi", "m8_camp", "m8_camp1", "m8_camp2", "m8_unbal_res", "m8_error", "m8_multi_warn", "m8_gear_ratio"]:
        st.session_state[k] = None

def _get_gear_params(rotor_data, key):
    gears = rotor_data.get("gear_elements", [])
    return gears[0].get(key, 0) if gears else 0

def _build_rotor_from_json(rotor_data, mat):
    shaft = []
    for el in rotor_data["shaft"]:
        shaft.append(rs.ShaftElement(L=float(el["L"]), idl=float(el.get("idl",0.0)), odl=float(el["odl"]), idr=float(el.get("idr",0.0)), odr=float(el.get("odr",el["odl"])), material=mat, shear_effects=True, rotary_inertia=True, gyroscopic=True))
    disks = []
    for d in rotor_data.get("disks", []):
        disks.append(rs.DiskElement(n=int(d["n"]), m=float(d["m"]), Id=float(d["Id"]), Ip=float(d["Ip"])))
    for g in rotor_data.get("gear_elements", []):
        try:
            import inspect
            gear_sig = inspect.signature(rs.GearElement.__init__)
            valid_args = set(gear_sig.parameters.keys())
            gear_kwargs = {"n": int(g["n"]), "m": float(g["m"]), "Id": float(g["Id"]), "Ip": float(g["Ip"]), "width": float(g.get("width", 0.07)), "n_teeth": int(g["n_teeth"]), "base_diameter": float(g["base_diameter"]), "pressure_angle": float(g.get("pressure_angle_deg", 22.5)), "helix_angle": float(g.get("helix_angle_deg", 0.0))}
            filtered_kwargs = {k: v for k, v in gear_kwargs.items() if k in valid_args}
            disks.append(rs.GearElement(**filtered_kwargs))
        except Exception as e:
            disks.append(rs.DiskElement(n=int(g["n"]), m=float(g["m"]), Id=float(g["Id"]), Ip=float(g["Ip"])))
    bears = []
    for b in rotor_data["bearings"]:
        bears.append(rs.BearingElement(n=int(b["n"]), kxx=float(b["kxx"]), kyy=float(b.get("kyy", b["kxx"])), cxx=float(b.get("cxx", 500.0)), cyy=float(b.get("cyy", 500.0))))
    return rs.Rotor(shaft, disks, bears)

def _run_all():
    if not st.session_state.get("m8_loaded") or not st.session_state.get("m8_json_data"): return
    if not ROSS_OK: return
    data = st.session_state["m8_json_data"]
    mat_d = data.get("material", {"name": "Steel", "rho": 7810, "E": 211e9, "G_s": 81.2e9})
    mat = rs.Material(name="Steel", rho=float(mat_d["rho"]), E=float(mat_d["E"]), G_s=float(mat_d["G_s"]))
    try:
        r1 = _build_rotor_from_json(data["rotor1"], mat)
        r2 = _build_rotor_from_json(data["rotor2"], mat)
        st.session_state["m8_rotor1"] = r1
        st.session_state["m8_rotor2"] = r2
        st.session_state["m8_error"] = None
        vmax = float(st.session_state.get("m8_vmax", 4000))
        npts = int(st.session_state.get("m8_npts", 25))
        n_modes = int(st.session_state.get("m8_n_modes", 12))
        try:
            try:
                multi = rs.MultiRotor(rotors=[r1, r2], gear_mesh_stiffness=1e8)
            except TypeError:
                multi = rs.MultiRotor(r1, r2, coupled_nodes=(3, 1), gear_mesh_stiffness=1e8)
            st.session_state["m8_multi"] = multi
            frequency_range = rs.Q_(np.linspace(0, vmax, npts), "RPM")
            camp = multi.run_campbell(frequency_range, frequencies=n_modes)
            st.session_state["m8_camp"] = camp
            st.session_state["m8_camp_vmax"] = vmax
            st.session_state["m8_gear_ratio"] = multi.mesh.gear_ratio
        except Exception as e_m:
            import traceback
            st.session_state["m8_error"] = "MultiRotor ERREUR: {}".format(e_m)
            st.session_state["m8_multi_warn"] = traceback.format_exc()
        st.session_state["m8_modal1"] = r1.run_modal(speed=0)
        st.session_state["m8_modal2"] = r2.run_modal(speed=0)
        if st.session_state.get("m8_multi"):
            try: st.session_state["m8_modal_multi"] = st.session_state["m8_multi"].run_modal(speed=0)
            except: pass
        _run_unbalance_calc(r1, r2)
    except Exception as e:
        import traceback
        st.session_state["m8_error"] = traceback.format_exc()

def _run_unbalance_calc(r1, r2):
    try:
        vmax = float(st.session_state.get("m8_vmax", 4000))
        rotor_s = r1 if "1" in st.session_state.get("m8_unb_rotor", "R1") else r2
        node_m = len(rotor_s.nodes) // 2
        freqs_rad = np.linspace(0, vmax * np.pi / 30, 300)
        res = rotor_s.run_unbalance_response(node=[node_m], unbalance_magnitude=[1e-3], unbalance_phase=[0.0], frequency=freqs_rad)
        st.session_state["m8_unbal_res"] = res
        st.session_state["m8_unbal_node"] = node_m
    except Exception: pass

def _display_geometry():
    r1 = st.session_state.get("m8_rotor1")
    r2 = st.session_state.get("m8_rotor2")
    if r1 is None or r2 is None: return st.info("Lancez les calculs.")
    multi = st.session_state.get("m8_multi")
    if multi is not None:
        try:
            fig = multi.plot_rotor()
            fig.update_layout(height=380, title="MultiRotor couple", margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True, key="m8_geo_multi")
        except Exception as e: st.warning("{}".format(e))
    else:
        st.warning("MultiRotor non couple - affichage individuel")
        c1, c2 = st.columns(2)
        with c1:
            try:
                fig1 = r1.plot_rotor()
                fig1.update_layout(height=260, title="Rotor 1", margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig1, use_container_width=True, key="m8_geo1")
            except Exception: pass
        with c2:
            try:
                fig2 = r2.plot_rotor()
                fig2.update_layout(height=260, title="Rotor 2", margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig2, use_container_width=True, key="m8_geo2")
            except Exception: pass

def _display_campbell():
    camp_m = st.session_state.get("m8_camp")
    if camp_m is None: return st.info("Lancez les calculs.")
    data = st.session_state.get("m8_json_data", {})
    z1 = _get_gear_params(data.get("rotor1", {}), "n_teeth")
    z2 = _get_gear_params(data.get("rotor2", {}), "n_teeth")
    rpm1 = float(data.get("rotor1", {}).get("speed_rpm", 1000))
    rpm2 = rpm1 * z1 / z2 if z2 > 0 else 0
    fe = rpm1 / 60 * z1
    vmax = float(st.session_state.get("m8_camp_vmax", 4000))
    gear_ratio = z1 / z2 if z2 > 0 else 0.2327
    harm_sel = st.session_state.get("m8_harmonics", "1X + 2X + fe")
    try:
        plot_harmonics = [1]
        if "2X" in harm_sel: plot_harmonics.append(2)
        if abs(gear_ratio - 1) > 0.01: plot_harmonics.append(round(gear_ratio, 4))
        fig = camp_m.plot(frequency_units="Hz", harmonics=plot_harmonics)
        y_max_auto = 600
        try:
            if hasattr(camp_m, 'wn') and camp_m.wn is not None:
                y_max_auto = max(600, float(np.max(camp_m.wn)) / (2 * np.pi) * 1.15)
        except Exception: pass
        fig.update_yaxes(range=[0, min(y_max_auto, 800)])
        if "fe" in harm_sel and fe < y_max_auto * 1.5:
            fig.add_hline(y=fe, line_dash="longdash", line_color="#7B1FA2", line_width=2.5, annotation_text=" fe = {:.0f} Hz".format(fe), annotation_position="top left", annotation_font=dict(color="#7B1FA2", size=11))
        fig.add_vline(x=rpm1, line_dash="dash", line_color="#1F5C8B", line_width=2, annotation_text=" N1 = {:.0f} RPM".format(rpm1), annotation_font=dict(color="#1F5C8B", size=11))
        if rpm2 > 0 and rpm2 <= vmax:
            fig.add_vline(x=rpm2, line_dash="dash", line_color="#C55A11", line_width=2, annotation_text=" N2 = {:.0f} RPM".format(rpm2), annotation_font=dict(color="#C55A11", size=11))
        fig.update_layout(height=550, title="Diagramme de Campbell - MultiRotor couple", xaxis_title="Vitesse R1 (RPM)", yaxis_title="Frequence (Hz)", plot_bgcolor="white", legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, use_container_width=True, key="m8_camp_fig")
    except Exception as e:
        import traceback
        st.warning("Erreur plot: {}".format(e))
        with st.expander("Details", expanded=False): st.code(traceback.format_exc())

def _display_modal():
    m1 = st.session_state.get("m8_modal1")
    m2 = st.session_state.get("m8_modal2")
    if m1 is None and m2 is None: return st.info("Lancez les calculs.")
    c1, c2 = st.columns(2)
    with c1:
        if m1:
            fn = m1.wn[:6] / (2 * np.pi)
            for i, f in enumerate(fn): st.caption("M{}: {:.2f} Hz".format(i+1, f))
    with c2:
        if m2:
            fn = m2.wn[:6] / (2 * np.pi)
            for i, f in enumerate(fn): st.caption("M{}: {:.2f} Hz".format(i+1, f))

def _display_unbalance():
    res = st.session_state.get("m8_unbal_res")
    if res is None: return st.info("Lancez les calculs.")
    st.success("Reponse au balourd calculee.")

def _display_benchmark():
    st.info("Benchmark ROSS Tutorial Part 4 - voir onglet Diagnostic pour les ecarts.")

def _display_theory():
    st.markdown("### Theorie des systemes MultiRotors\nEquation du mouvement global incluant la raideur de la ligne d action des dents.")

def _display_diagnostic():
    st.markdown("### Diagnostic du systeme MultiRotor")
    r1 = st.session_state.get("m8_rotor1")
    r2 = st.session_state.get("m8_rotor2")
    multi = st.session_state.get("m8_multi")
    error = st.session_state.get("m8_error")
    warn = st.session_state.get("m8_multi_warn")
    c1, c2, c3 = st.columns(3)
    with c1:
        txt = "OK" if r1 else "NON"
        col = "green" if r1 else "red"
        st.markdown('<span style="color:{}"><b>Rotor 1: {}</b></span>'.format(col, txt), unsafe_allow_html=True)
    with c2:
        txt = "OK" if r2 else "NON"
        col = "green" if r2 else "red"
        st.markdown('<span style="color:{}"><b>Rotor 2: {}</b></span>'.format(col, txt), unsafe_allow_html=True)
    with c3:
        txt = "COUPLE" if multi else "NON COUPLE"
        col = "green" if multi else "orange"
        st.markdown('<span style="color:{}"><b>MultiRotor: {}</b></span>'.format(col, txt), unsafe_allow_html=True)
    if error:
        st.error("Erreur : {}".format(error))
    if warn:
        with st.expander("Details erreur MultiRotor"):
            st.code(str(warn))
    if multi:
        st.success("Systeme operationnel. Voir Campbell couple pour les resultats.")

def _log(message, level="info"):
    try:
        from app import add_log
        add_log(message, level)
    except Exception: pass
