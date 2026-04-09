# modules/m8_multirotor.py — MultiRotor Positional Arguments Fix
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

# =============================================================================
# MODÈLE DE VALIDATION (TUTORIAL 4)
# =============================================================================

def build_tutorial_4_model():
    mat = rs.Material(name="Steel", rho=7810, E=211e9, G_s=81.2e9)

    # Rotor 1
    shaft1 = [
        rs.ShaftElement(L=0.10, idl=0.0, odl=0.30, material=mat),
        rs.ShaftElement(L=4.24, idl=0.0, odl=0.30, material=mat),
        rs.ShaftElement(L=1.16, idl=0.0, odl=0.22, material=mat),
        rs.ShaftElement(L=0.30, idl=0.0, odl=0.22, material=mat),
    ]
    disks1 = [
        rs.DiskElement(n=0, m=50.0, Id=1.50, Ip=3.00),
        rs.DiskElement(n=4, m=20.0, Id=0.50, Ip=1.00),
    ]
    bearings1 = [
        rs.BearingElement(n=0, kxx=1.839e8, kyy=2.004e8, cxx=3000.0, cyy=3000.0),
        rs.BearingElement(n=3, kxx=1.839e8, kyy=2.004e8, cxx=3000.0, cyy=3000.0),
    ]
    r1 = rs.Rotor(shaft1, disks1, bearings1)

    # Rotor 2
    shaft2 = [
        rs.ShaftElement(L=1.50, idl=0.0, odl=0.25, material=mat),
        rs.ShaftElement(L=2.50, idl=0.0, odl=0.25, material=mat),
        rs.ShaftElement(L=1.00, idl=0.0, odl=0.20, material=mat),
    ]
    disks2 = [
        rs.DiskElement(n=3, m=35.0, Id=1.20, Ip=2.40),
    ]
    bearings2 = [
        rs.BearingElement(n=0, kxx=1.5e8, kyy=1.5e8, cxx=2500.0, cyy=2500.0),
        rs.BearingElement(n=2, kxx=1.5e8, kyy=1.5e8, cxx=2500.0, cyy=2500.0),
    ]
    r2 = rs.Rotor(shaft2, disks2, bearings2)

    # Engrenage
    gear = rs.GearElement(
        2, 5.0, 0.002, 0.004, 20, 0.5, np.radians(22.5)
    )

    # MULTI ROTOR - CORRECTION : Utilisation d'arguments positionnels
    # Ordre : ([rotors], [gears], [connections])
    multi = rs.MultiRotor([r1, r2], [gear], [(0, 2, 1, 1)])
    
    return multi, r1, r2

# =============================================================================
# LOGIQUE DE CHARGEMENT JSON
# =============================================================================

def build_rotor_from_json(shaft_data, disk_data, bearing_data, material_obj):
    shaft_elements = [rs.ShaftElement(L=s["L (m)"], idl=s["id_L (m)"], odl=s["od_L (m)"], material=material_obj) for s in shaft_data]
    disk_elements = [rs.DiskElement(n=d["nœud"], m=d["Masse (kg)"], Id=d["Id (kg.m²)"], Ip=d["Ip (kg.m²)"]) for d in disk_data]
    bearing_elements = [rs.BearingElement(n=b["nœud"], kxx=b["kxx"], kyy=b["kyy"], cxx=b["cxx"], cyy=b["cyy"]) for b in bearing_data]
    return rs.Rotor(shaft_elements, disk_elements, bearing_elements)

def load_multirotor_from_json(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    mat = rs.Material(name="Steel", rho=7810, E=211e9, G_s=81.2e9)
    r1 = build_rotor_from_json(data["shaft"], data["disks"], data["bearings"], mat)
    r2 = build_rotor_from_json(data["shaft_2"], data["disks_2"], data["bearings_2"], mat)
    
    gear_info = data["gears"][0]
    gear = rs.GearElement(
        gear_info["nœud_rotor_1"], 
        gear_info["Masse (kg)"], 
        gear_info["Id (kg.m²)"], 
        gear_info["Ip (kg.m²)"], 
        gear_info["n_teeth"], 
        gear_info["pitch_diameter"], 
        np.radians(gear_info["pr_angle"])
    )
    
    # MULTI ROTOR - CORRECTION : Arguments positionnels
    multi = rs.MultiRotor([r1, r2], [gear], [(0, gear_info["nœud_rotor_1"], 1, gear_info["nœud_rotor_2"])])
    return multi, r1, r2

# =============================================================================
# INTERFACE STREAMLIT
# =============================================================================

def render_m8(col_settings, col_graphics):
    with col_settings:
        st.markdown('<div class="rl-settings-title">MultiRotor System</div>', unsafe_allow_html=True)
        mode = st.radio("Source du modèle", ["Modèle de Validation (Tutorial 4)", "Charger JSON"], index=0)
        
        if mode == "Charger JSON":
            uploaded_file = st.file_uploader("Fichier .json", type=["json"])
            if uploaded_file:
                with open("temp_system.json", "wb") as f:
                    f.write(uploaded_file.getbuffer())
        
        if st.button("Assembler le système", type="primary", use_container_width=True):
            if not ROSS_OK:
                st.error("ROSS n'est pas installé.")
                return
            try:
                with st.spinner("Construction..."):
                    if mode == "Modèle de Validation (Tutorial 4)":
                        multi, r1, r2 = build_tutorial_4_model()
                    else:
                        multi, r1, r2 = load_multirotor_from_json("temp_system.json")
                    st.session_state["m8_multi"] = multi
                    st.session_state["m8_rotor1"] = r1
                    st.session_state["m8_rotor2"] = r2
                    st.success("Système assemblé avec succès !")
            except Exception as e:
                st.error(f"Erreur lors du chargement : {e}")

        st.markdown("---")
        vmax = st.slider("Vitesse max (RPM)", 1000, 20000, 10000)
        if st.button("Calculer Campbell", use_container_width=True):
            if "m8_multi" in st.session_state:
                try:
                    speeds = np.linspace(0, vmax * np.pi / 30, 30)
                    st.session_state["m8_camp"] = st.session_state["m8_multi"].run_campbell(speeds, frequencies=10)
                    st.success("Calcul terminé !")
                except Exception as e:
                    st.error(f"Erreur de calcul : {e}")

    with col_graphics:
        _display_results()

def _display_results():
    st.markdown('<div class="rl-graphics-title">Résultats MultiRotor</div>', unsafe_allow_html=True)
    if "m8_multi" not in st.session_state:
        st.info("Veuillez assembler le système.")
        return
    tab1, tab2 = st.tabs(["Géométrie", "Campbell"])
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Rotor 1**")
            st.plotly_chart(st.session_state["m8_rotor1"].plot_rotor(), use_container_width=True)
        with col2:
            st.markdown("**Rotor 2**")
            st.plotly_chart(st.session_state["m8_rotor2"].plot_rotor(), use_container_width=True)
    with tab2:
        if "m8_camp" in st.session_state:
            camp = st.session_state["m8_camp"]
            spd_rpm = np.linspace(0, 10000, 30) 
            fn_mat = camp.wd / (2 * np.pi)
            fig = go.Figure()
            for i in range(fn_mat.shape[1]):
                fig.add_trace(go.Scatter(x=spd_rpm, y=fn_mat[:, i], name=f"Mode {i+1}"))
            fig.update_layout(title="Diagramme de Campbell", xaxis_title="RPM", yaxis_title="Hz")
            st.plotly_chart(fig, use_container_width=True)
