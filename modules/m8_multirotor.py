# modules/m8_multirotor.py — VERSION CORRIGÉE
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

try:
    import ross as rs
    ROSS_OK = True
except ImportError:
    ROSS_OK = False

def render_m8(col_settings, col_graphics):
    with col_settings:
        _render_settings()
    with col_graphics:
        _render_graphics()

def _render_settings():
    st.markdown('<div class="rl-settings-title">MultiRotor & GearElement</div>', unsafe_allow_html=True)

    tab_r1, tab_r2, tab_gear, tab_run = st.tabs(["Rotor 1", "Rotor 2", "Engrenage", "Calcul"])

    # --- ROTOR 1 ---
    with tab_r1:
        c1, c2 = st.columns(2)
        with c1:
            st.slider("Nombre d elements (R1)", 2, 10, 4, key="m8_r1_nel")
            st.number_input("Longueur element (m)", 0.05, 1.0, 0.25, key="m8_r1_L")
            st.number_input("Diametre arbre (m)", 0.01, 0.3, 0.05, key="m8_r1_od")
        with c2:
            st.selectbox("Materiau R1", ["Acier standard (AISI 1045)", "Titane (Ti-6Al-4V)"], key="m8_r1_mat")
            st.number_input("Vitesse (RPM)", 100.0, 30000.0, 3000.0, key="m8_r1_rpm")
        st.number_input("Noeud du disque (R1)", 0, 10, 2, key="m8_r1_disk_node")

    # --- ROTOR 2 ---
    with tab_r2:
        c1, c2 = st.columns(2)
        with c1:
            st.slider("Nombre d elements (R2)", 2, 10, 4, key="m8_r2_nel")
            st.number_input("Longueur element (m)", 0.05, 1.0, 0.25, key="m8_r2_L")
            st.number_input("Diametre arbre (m)", 0.01, 0.3, 0.04, key="m8_r2_od")
        with c2:
            st.selectbox("Materiau R2", ["Acier standard (AISI 1045)", "Titane (Ti-6Al-4V)"], key="m8_r2_mat")
        st.number_input("Noeud du disque (R2)", 0, 10, 2, key="m8_r2_disk_node")

    # --- ENGRENAGE (Aligné sur le tutoriel) ---
    with tab_gear:
        st.markdown("#### Couplage des arbres")
        c1, c2 = st.columns(2)
        with c1:
            # Sécurisation : le max est lié au nombre d'éléments du rotor 1
            nel1 = st.session_state.get("m8_r1_nel", 4)
            st.number_input("Noeud pignon (R1)", 0, nel1, nel1, key="m8_gear_n1")
            st.number_input("Diametre primitif pignon (m)", 0.02, 1.0, 0.10, key="m8_gear_d1")
            st.number_input("z1 (dents)", 5, 200, 20, key="m8_gear_z1")
        with c2:
            nel2 = st.session_state.get("m8_r2_nel", 4)
            st.number_input("Noeud roue (R2)", 0, nel2, 0, key="m8_gear_n2")
            st.number_input("Diametre primitif roue (m)", 0.02, 1.0, 0.15, key="m8_gear_d2")
            st.number_input("z2 (dents)", 5, 200, 30, key="m8_gear_z2")
        
        st.number_input("Angle de pression (deg)", 14.5, 30.0, 20.0, key="m8_gear_alpha")

    # --- CALCUL ---
    with tab_run:
        st.slider("Vitesse max (RPM)", 1000, 30000, 10000, key="m8_vmax")
        st.button("Calculer le système", type="primary", use_container_width=True, on_click=_run_multirotor)
        
        if "m8_log" in st.session_state:
            st.info(st.session_state["m8_log"])
        if "m8_error" in st.session_state and st.session_state["m8_error"]:
            st.error(st.session_state["m8_error"])

def _run_multirotor():
    if not ROSS_OK:
        st.session_state["m8_error"] = "ROSS non disponible"
        return

    try:
        st.session_state["m8_log"] = "Construction des rotors..."
        r1 = _build_rotor("m8_r1")
        r2 = _build_rotor("m8_r2")

        st.session_state["m8_log"] = "Définition de l'engrenage..."
        # Utilisation stricte des paramètres du tutoriel
        gear = rs.GearElement(
            n=st.session_state["m8_gear_n1"], 
            pitch_diameter=st.session_state["m8_gear_d1"], 
            pressure_angle=np.radians(st.session_state["m8_gear_alpha"])
        )

        st.session_state["m8_log"] = "Assemblage MultiRotor (Matrices globales)..."
        # CONNECTION : (id_rotor1, node1, id_rotor2, node2)
        multi = rs.MultiRotor(
            rotors=[r1, r2], 
            gear_elements=[gear], 
            connections=[(0, st.session_state["m8_gear_n1"], 1, st.session_state["m8_gear_n2"])]
        )

        st.session_state["m8_log"] = "Calcul du diagramme de Campbell..."
        vmax = float(st.session_state["m8_vmax"])
        speeds = np.linspace(0, vmax * np.pi / 30, 30)
        camp = multi.run_campbell(speeds, frequencies=10)

        st.session_state["m8_camp"] = camp
        st.session_state["m8_multi"] = multi
        st.session_state["m8_log"] = "Calcul terminé avec succès !"
        st.session_state["m8_error"] = None

    except Exception as e:
        st.session_state["m8_error"] = f"Erreur ROSS : {str(e)}"
        st.session_state["m8_log"] = "Échec du calcul."

def _build_rotor(prefix):
    nel = int(st.session_state[f"{prefix}_nel"])
    mat = rs.Material(name="steel", rho=7810, E=211e9, G_s=81e9)
    shaft = [rs.ShaftElement(L=st.session_state[f"{prefix}_L"], idl=0, odl=st.session_state[f"{prefix}_od"], material=mat) for _ in range(nel)]
    # On s'assure que le disque est sur un noeud existant
    disk_node = min(int(st.session_state[f"{prefix}_disk_node"]), nel)
    disk = rs.DiskElement.from_geometry(n=disk_node, material=mat, width=0.05, i_d=st.session_state[f"{prefix}_od"], o_d=0.2)
    b0 = rs.BearingElement(n=0, kxx=1e7, kyy=1e7)
    bn = rs.BearingElement(n=nel, kxx=1e7, kyy=1e7)
    return rs.Rotor(shaft, [disk], [b0, bn])

def _render_graphics():
    # Utiliser st.session_state["m8_camp"] pour tracer les courbes avec Plotly
    if "m8_camp" not in st.session_state:
        st.info("En attente de calcul...")
        return
    
    camp = st.session_state["m8_camp"]
    # Tracer camp.wd / (2*np.pi) vs speed...
    st.success("Résultats disponibles !")
