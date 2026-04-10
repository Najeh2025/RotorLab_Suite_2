import os

code = r'''
# modules/m8_multirotor.py
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import json

try:
    import ross as rs
    ROSS_OK = True
except ImportError:
    ROSS_OK = False

REFERENCE_JSON = {
    "name": "ROSS Tutorial Part 4", "material": {"name": "Steel", "rho": 7810, "E": 211e9, "G_s": 81.2e9},
    "rotor1": {
        "shaft": [
            {"L": 0.3, "idl": 0.0, "odl": 0.123, "idr": 0.0, "odr": 0.123}, {"L": 0.092, "idl": 0.0, "odl": 0.15, "idr": 0.0, "odr": 0.15},
            {"L": 0.2, "idl": 0.0, "odl": 0.15, "idr": 0.0, "odr": 0.15}, {"L": 0.2, "idl": 0.0, "odl": 0.15, "idr": 0.0, "odr": 0.15},
            {"L": 0.092, "idl": 0.0, "odl": 0.15, "idr": 0.0, "odr": 0.15}, {"L": 0.3, "idl": 0.0, "odl": 0.123, "idr": 0.0, "odr": 0.123}
        ],
        "disks": [{"n": 0, "m": 66.63, "Id": 0.431, "Ip": 0.735}, {"n": 6, "m": 69.83, "Id": 0.542, "Ip": 0.884}],
        "gear_elements": [{"n": 3, "m": 14.37, "Id": 0.068, "Ip": 0.136, "width": 0.07, "n_teeth": 37, "base_diameter": 0.19, "pressure_angle_deg": 22.5, "helix_angle_deg": 0.0}],
        "bearings": [{"n": 2, "kxx": 5.5e8, "kyy": 6.7e8, "cxx": 3e3, "cyy": 3e3}, {"n": 4, "kxx": 5.5e8, "kyy": 6.7e8, "cxx": 3e3, "cyy": 3e3}],
        "speed_rpm": 1200.0
    },
    "rotor2": {
        "shaft": [
            {"L": 0.08, "idl": 0.0, "odl": 0.321, "idr": 0.0, "odr": 0.321}, {"L": 0.2, "idl": 0.0, "odl": 0.321, "idr": 0.0, "odr": 0.321},
            {"L": 0.2, "idl": 0.0, "odl": 0.261, "idr": 0.0, "odr": 0.261}, {"L": 0.64, "idl": 0.0, "odl": 0.261, "idr": 0.0, "odr": 0.261}
        ],
        "disks": [],
        "gear_elements": [{"n": 1, "m": 322.0, "Id": 24.17, "Ip": 48.34, "width": 0.2, "n_teeth": 159, "base_diameter": 0.826, "pressure_angle_deg": 22.5, "helix_angle_deg": 0.0}],
        "bearings": [{"n": 0, "kxx": 3.2e9, "kyy": 4.6e9, "cxx": 3e3, "cyy": 3e3}, {"n": 4, "kxx": 3.2e9, "kyy": 4.6e9, "cxx": 3e3, "cyy": 3e3}],
        "speed_rpm": 279.0
    }
}

def render_m8(col_settings, col_graphics):
    with col_settings: _render_settings()
    with col_graphics: _render_graphics()

def _render_settings():
    st.markdown('<div class="rl-settings-title">MultiRotor & GearElement [NEW]</div>', unsafe_allow_html=True)
    st.markdown('<span class="rl-badge rl-badge-new">NEW v2.0</span>', unsafe_allow_html=True)
    tab_load, tab_params, tab_run = st.tabs(["Chargement du modele", "Parametres de calcul", "Statut & Actions"])
    with tab_load: _render_tab_load()
    with tab_params: _render_tab_params()
    with tab_run: _render_tab_run()

def _render_tab_load():
    source = st.radio("Source :", ["Modele de reference (ROSS Tutorial Part 4)", "Charger un fichier JSON"], key="m8_source")
    if source == "Modele de reference (ROSS Tutorial Part 4)":
        if st.button("Charger le modele de reference", type="primary", key="m8_load_ref", use_container_width=True):
            st.session_state["m8_json_data"] = REFERENCE_JSON
            st.session_state["m8_loaded"] = True
            st.session_state["m8_source_name"] = "ROSS Tutorial Part 4"
            _clear_results()
        st.download_button("Telecharger JSON", data=json.dumps(REFERENCE_JSON, indent=2), file_name="ross_tutorial_part4.json", mime="application/json", key="m8_dl_ref")
    else:
        uploaded = st.file_uploader("Fichier JSON", type=["json"], key="m8_upload")
        if uploaded is not None:
            try:
                data = json.loads(uploaded.read().decode("utf-8"))
                st.session_state["m8_json_data"] = data
                st.session_state["m8_loaded"] = True
                st.session_state["m8_source_name"] = data.get("name", "Custom")
                _clear_results()
            except Exception as e: st.error("Erreur JSON: {}".format(e))
    if st.session_state.get("m8_loaded"):
        _show_model_summary()

def _show_model_summary():
    data = st.session_state["m8_json_data"]
    z1 = data["rotor1"]["gear_elements"][0]["n_teeth"]
    z2 = data["rotor2"]["gear_elements"][0]["n_teeth"]
    st.caption("R1: z={} | R2: z={} | i={:.4f}".format(z1, z2, z1/z2))

def _render_tab_params():
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Vitesse max (RPM)", 500.0, 30000.0, 4000.0, step=500.0, key="m8_vmax")
        st.slider("Resolution", 10, 80, 25, key="m8_npts")
    with c2:
        st.slider("Nombre de modes", 4, 24, 12, key="m8_n_modes")
        st.radio("Harmoniques", ["1X", "1X + 2X", "1X + 2X + fe"], index=2, horizontal=True, key="m8_harmonics")
    st.markdown("Reponse au balourd")
    c1, c2 = st.columns(2)
    with c1: st.number_input("Magnitude (kg.m)", 1e-6, 1.0, 1e-3, format="%.4f", key="m8_unb_mag")
    with c2: st.radio("Rotor", ["Rotor 1", "Rotor 2"], key="m8_unb_rotor", horizontal=True)

def _render_tab_run():
    if not st.session_state.get("m8_loaded"): return st.warning("Chargez un modele.")
    st.button("Assembler et lancer", type="primary", key="m8_run_all", use_container_width=True, on_click=_run_all)
    if st.session_state.get("m8_error"): st.error(st.session_state["m8_error"])
    for k, l in [("m8_rotor1","R1"), ("m8_rotor2","R2"), ("m8_multi","MultiRotor"), ("m8_camp","Campbell")]:
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
    for k in ["m8_rotor1", "m8_rotor2", "m8_multi", "m8_modal1", "m8_modal2", "m8_modal_multi", "m8_camp", "m8_unbal_res", "m8_error", "m8_multi_warn", "m8_gear_ratio"]:
        st.session_state[k] = None

def _get_gear_params(rd, k):
    return rd.get("gear_elements", [{}])[0].get(k, 0)

def _build_rotor_from_json(rd, mat):
    shaft = [rs.ShaftElement(L=float(e["L"]), idl=float(e.get("idl",0)), odl=float(e["odl"]), idr=float(e.get("idr",0)), odr=float(e.get("odr",e["odl"])), material=mat, shear_effects=True, rotary_inertia=True, gyroscopic=True) for e in rd["shaft"]]
    disks = [rs.DiskElement(n=int(d["n"]), m=float(d["m"]), Id=float(d["Id"]), Ip=float(d["Ip"])) for d in rd.get("disks", [])]
    for g in rd.get("gear_elements", []):
        try:
            import inspect
            sig = inspect.signature(rs.GearElement.__init__)
            kw = {"n": int(g["n"]), "m": float(g["m"]), "Id": float(g["Id"]), "Ip": float(g["Ip"]), "width": float(g.get("width", 0.07)), "n_teeth": int(g["n_teeth"]), "base_diameter": float(g["base_diameter"]), "pressure_angle": float(g.get("pressure_angle_deg", 22.5)), "helix_angle": float(g.get("helix_angle_deg", 0.0))}
            disks.append(rs.GearElement(**{k: v for k, v in kw.items() if k in sig.parameters}))
        except: disks.append(rs.DiskElement(n=int(g["n"]), m=float(g["m"]), Id=float(g["Id"]), Ip=float(g["Ip"])))
    bears = [rs.BearingElement(n=int(b["n"]), kxx=float(b["kxx"]), kyy=float(b.get("kyy", b["kxx"])), cxx=float(b.get("cxx", 500)), cyy=float(b.get("cyy", 500))) for b in rd["bearings"]]
    return rs.Rotor(shaft, disks, bears)

def _run_all():
    if not ROSS_OK: return
    data = st.session_state["m8_json_data"]
    md = data.get("material", {"rho": 7810, "E": 211e9, "G_s": 81.2e9})
    mat = rs.Material(name="Steel", rho=float(md["rho"]), E=float(md["E"]), G_s=float(md["G_s"]))
    try:
        r1 = _build_rotor_from_json(data["rotor1"], mat)
        r2 = _build_rotor_from_json(data["rotor2"], mat)
        st.session_state["m8_rotor1"], st.session_state["m8_rotor2"], st.session_state["m8_error"] = r1, r2, None
        vmax = float(st.session_state.get("m8_vmax", 4000))
        try:
            try: multi = rs.MultiRotor(rotors=[r1, r2], gear_mesh_stiffness=1e8)
            except: multi = rs.MultiRotor(r1, r2, coupled_nodes=(3,1), gear_mesh_stiffness=1e8)
            st.session_state["m8_multi"] = multi
            camp = multi.run_campbell(rs.Q_(np.linspace(0, vmax, 25), "RPM"), frequencies=12)
            st.session_state["m8_camp"], st.session_state["m8_camp_vmax"] = camp, vmax
            st.session_state["m8_gear_ratio"] = multi.mesh.gear_ratio
        except Exception as e:
            st.session_state["m8_error"] = "Err Multi: {}".format(e)
        st.session_state["m8_modal1"] = r1.run_modal(speed=0)
        st.session_state["m8_modal2"] = r2.run_modal(speed=0)
        if st.session_state.get("m8_multi"):
            try: st.session_state["m8_modal_multi"] = st.session_state["m8_multi"].run_modal(speed=0)
            except: pass
        try:
            rs_val = r1 if "1" in st.session_state.get("m8_unb_rotor", "R1") else r2
            res = rs_val.run_unbalance_response(node=[len(rs_val.nodes)//2], unbalance_magnitude=[1e-3], unbalance_phase=[0.0], frequency=np.linspace(0, vmax*np.pi/30, 300))
            st.session_state["m8_unbal_res"] = res
        except: pass
    except Exception as e: st.session_state["m8_error"] = str(e)

def _display_geometry():
    r1, r2 = st.session_state.get("m8_rotor1"), st.session_state.get("m8_rotor2")
    if not r1 or not r2: return st.info("Lancez les calculs.")
    multi = st.session_state.get("m8_multi")
    if multi:
        try:
            fig = multi.plot_rotor(); fig.update_layout(height=400, title="MultiRotor couple", margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e: st.warning(str(e))
    else:
        c1, c2 = st.columns(2)
        with c1:
            try: st.plotly_chart(r1.plot_rotor().update_layout(height=300, title="Rotor 1"), use_container_width=True)
            except: pass
        with c2:
            try: st.plotly_chart(r2.plot_rotor().update_layout(height=300, title="Rotor 2"), use_container_width=True)
            except: pass

def _display_campbell():
    camp_m = st.session_state.get("m8_camp")
    if not camp_m: return st.info("Lancez les calculs.")
    data = st.session_state.get("m8_json_data", {})
    z1, z2 = _get_gear_params(data["rotor1"], "n_teeth"), _get_gear_params(data["rotor2"], "n_teeth")
    rpm1, rpm2 = float(data["rotor1"]["speed_rpm"]), float(data["rotor1"]["speed_rpm"]) * z1/z2
    fe = rpm1 / 60 * z1
    vmax = float(st.session_state.get("m8_camp_vmax", 4000))
    try:
        harm = [1]
        if "2X" in st.session_state.get("m8_harmonics", ""): harm.append(2)
        harm.append(round(z1/z2, 4))
        fig = camp_m.plot(frequency_units="Hz", harmonics=harm)
        y_max = 600
        try: y_max = max(600, float(np.max(camp_m.wn))/(2*np.pi)*1.15)
        except: pass
        fig.update_yaxes(range=[0, min(y_max, 800)])
        if "fe" in st.session_state.get("m8_harmoniques", "1X + 2X + fe") and fe < y_max*1.5:
            fig.add_hline(y=fe, line_dash="longdash", line_color="#7B1FA2", line_width=2.5, annotation_text=" fe = {:.0f} Hz".format(fe))
        fig.add_vline(x=rpm1, line_dash="dash", line_color="#1F5C8B", line_width=2, annotation_text=" N1={:.0f} RPM".format(rpm1))
        if rpm2 <= vmax: fig.add_vline(x=rpm2, line_dash="dash", line_color="#C55A11", line_width=2, annotation_text=" N2={:.0f} RPM".format(rpm2))
        fig.update_layout(height=550, title="Diagramme de Campbell - MultiRotor couple", plot_bgcolor="white", legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e: st.warning(str(e))

def _display_modal():
    mm = st.session_state.get("m8_modal_multi")
    if mm:
        fn = mm.wn/(2*np.pi)
        df = pd.DataFrame({"Mode": range(1,len(fn)+1), "fn (Hz)": ["{:.3f}".format(f) for f in fn]})
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        m1, m2 = st.session_state.get("m8_modal1"), st.session_state.get("m8_modal2")
        if m1:
            fn = m1.wn[:6]/(2*np.pi)
            st.markdown("**R1**")
            st.dataframe(pd.DataFrame({"Mode": range(1,len(fn)+1), "fn (Hz)": ["{:.3f}".format(f) for f in fn]}), hide_index=True)
        if m2:
            fn = m2.wn[:6]/(2*np.pi)
            st.markdown("**R2**")
            st.dataframe(pd.DataFrame({"Mode": range(1,len(fn)+1), "fn (Hz)": ["{:.3f}".format(f) for f in fn]}), hide_index=True)

def _display_unbalance():
    if not st.session_state.get("m8_unbal_res"): return st.info("Lancez les calculs.")
    st.success("Reponse au balourd calculee.")

def _display_benchmark():
    mm = st.session_state.get("m8_modal_multi")
    if mm:
        ref = [109.0, 116.0, 146.0, 148.0, 276.0, 288.0, 447.0, 519.0]
        fn_c = list(mm.wn[:8]/(2*np.pi))
        rows = [{"Mode":i+1, "Calc (Hz)":"{:.3f}".format(fn_c[i]), "Ref (Hz)":"{:.3f}".format(ref[i]), "Err (%)":"{:.1f}".format(abs(fn_c[i]-ref[i])/ref[i]*100)} for i in range(min(8, len(fn_c), len(ref)))]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else: st.info("Modele non couple.")

def _display_theory():
    st.markdown("### Theorie\nEquation du mouvement global avec raideur de la ligne d action des dents.")

def _display_diagnostic():
    st.markdown("### Diagnostic")
    r1, r2, multi = st.session_state.get("m8_rotor1"), st.session_state.get("m8_rotor2"), st.session_state.get("m8_multi")
    c1,c2,c3 = st.columns(3)
    c1.markdown("R1: {}".format("OK" if r1 else "ERR"))
    c2.markdown("R2: {}".format("OK" if r2 else "ERR"))
    c3.markdown("Multi: {}".format("OK" if multi else "ERR"))
    if st.session_state.get("m8_error"): st.error(st.session_state["m8_error"])

def _log(m, l="info"):
    try:
        from app import add_log
        add_log(m, l)
    except: pass
'''

filepath = os.path.join("modules", "m8_multirotor.py")
with open(filepath, "w", encoding="utf-8") as f:
    f.write(code.strip())

print("SUCCESS: Fichier {} reconstruit proprement !".format(filepath))
