# modules/m8_json_loader.py — MultiRotor JSON Loader
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
# LOGIQUE DE CHARGEMENT JSON -> ROSS
# =============================================================================

def _get_material(mat_name):
    """Convertit le nom du matériau JSON en objet rs.Material"""
    mats = {
        "mat_steel": rs.Material(name="Steel", rho=7810, E=211e9, G_s=81.2e9),
        "mat_titanium": rs.Material(name="Titanium", rho=4430, E=114e9, G_s=44.0e9),
    }
    return mats.get(mat_name, mats["mat_steel"])

def build_rotor_from_json(shaft_data, disk_data, bearing_data, material_obj):
    """Construit un objet rs.Rotor à partir des listes du JSON"""
    
    # 1. Construction de l'arbre (gestion des diamètres variables L et R)
    shaft_elements = []
    for s in shaft_data:
        # Note: rs.ShaftElement prend généralement idl et odl. 
        # Si ROSS supporte les cônes, on utiliserait idl, odl, idr, odr.
        # Ici on utilise la moyenne ou le côté gauche pour la compatibilité.
        element = rs.ShaftElement(
            L=s["L (m)"], 
            idl=s["id_L (m)"], 
            odl=s["od_L (m)"], 
            material=material_obj
        )
        shaft_elements.append(element)

    # 2. Construction des disques (via Masse et Inertie)
    disk_elements = []
    for d in disk_data:
        disk = rs.DiskElement(
            n=d["nœud"], 
            m=d["Masse (kg)"], 
            id=d["Id (kg.m²)"], 
            ip=d["Ip (kg.m²)"]
        )
        disk_elements.append(disk)

    # 3. Construction des paliers
    bearing_elements = []
    for b in bearing_data:
        bearing = rs.BearingElement(
            n=b["nœud"], 
            kxx=b["kxx"], 
            kyy=b["kyy"], 
            kxy=b.get("kxy", 0.0), 
            cxx=b["cxx"], 
            cyy=b["cyy"]
        )
        bearing_elements.append(bearing)

    return rs.Rotor(shaft_elements, disk_elements, bearing_elements)

def load_multirotor_system(json_file):
    """Fonction principale d'assemblage du système complet"""
    # Lecture du fichier
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mat = _get_material(data["material"])

    # Construction Rotor 1
    r1 = build_rotor_from_json(data["shaft"], data["disks"], data["bearings"], mat)
    
    # Construction Rotor 2
    r2 = build_rotor_from_json(data["shaft_2"], data["disks_2"], data["bearings_2"], mat)

    # Construction de l'engrenage
    gear_info = data["gears"][0]
    gear = rs.GearElement(
        n=gear_info["nœud_rotor_1"], 
        pitch_diameter=gear_info["pitch_diameter"], 
        pressure_angle=np.radians(gear_info["pr_angle"])
    )

    # Assemblage MultiRotor (Séquence : Rotor0_Node, Rotor1_Node)
    multi = rs.MultiRotor(
        rotors=[r1, r2], 
        gear_elements=[gear], 
        connections=[(0, gear_info["nœud_rotor_1"], 1, gear_info["nœud_rotor_2"])]
    )
    
    return multi, r1, r2

# =============================================================================
# INTERFACE STREAMLIT
# =============================================================================

def render_m8_json(col_settings, col_graphics):
    with col_settings:
        st.markdown('<div class="rl-settings-title">JSON MultiRotor Loader</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Charger le fichier .json du système", type=["json"])
        
        if uploaded_file is not None:
            if not ROSS_OK:
                st.error("ROSS n'est pas installé.")
                return

            # Sauvegarde temporaire du fichier pour l'ouverture
            with open("temp_system.json", "wb") as f:
                f.write(uploaded_file.getbuffer())

            if st.button("Assembler le système", type="primary", use_container_width=True):
                try:
                    with st.spinner("Assemblage des matrices globales..."):
                        multi, r1, r2 = load_multirotor_system("temp_system.json")
                        st.session_state["m8_multi"] = multi
                        st.session_state["m8_rotor1"] = r1
                        st.session_state["m8_rotor2"] = r2
                        st.success("Système chargé avec succès !")
                except Exception as e:
                    st.error(f"Erreur lors du chargement : {e}")

        st.markdown("---")
        st.markdown("#### Paramètres d'analyse")
        vmax = st.slider("Vitesse max Campbell (RPM)", 1000, 20000, 10000)
        n_modes = st.slider("Nombre de modes", 2, 20, 10)
        
        if st.button("Calculer Campbell", use_container_width=True):
            if "m8_multi" in st.session_state:
                try:
                    speeds = np.linspace(0, vmax * np.pi / 30, 30)
                    camp = st.session_state["m8_multi"].run_campbell(speeds, frequencies=n_modes)
                    st.session_state["m8_camp"] = camp
                    st.success("Calcul terminé !")
                except Exception as e:
                    st.error(f"Erreur de calcul : {e}")
            else:
                st.warning("Veuillez d'abord assembler le système.")

    with col_graphics:
        _display_results()

def _display_results():
    st.markdown('<div class="rl-graphics-title">Visualisation du Système JSON</div>', unsafe_allow_html=True)
    
    if "m8_multi" not in st.session_state:
        st.info("En attente du chargement d'un fichier JSON...")
        return

    tab1, tab2 = st.tabs(["Géométrie", "Campbell"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Rotor 1**")
            fig1 = st.session_state["m8_rotor1"].plot_rotor()
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            st.markdown("**Rotor 2**")
            fig2 = st.session_state["m8_rotor2"].plot_rotor()
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        if "m8_camp" in st.session_state:
            camp = st.session_state["m8_camp"]
            # Extraction des données pour Plotly
            spd_rpm = np.linspace(0, 10000, 30) # À adapter selon vmax
            fn_mat = camp.wd / (2 * np.pi)
            
            fig = go.Figure()
            for i in range(fn_mat.shape[1]):
                fig.add_trace(go.Scatter(x=spd_rpm, y=fn_mat[:, i], name=f"Mode {i+1}"))
            
            fig.update_layout(title="Campbell du système chargé", xaxis_title="RPM", yaxis_title="Hz")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Lancez le calcul du diagramme de Campbell.")
