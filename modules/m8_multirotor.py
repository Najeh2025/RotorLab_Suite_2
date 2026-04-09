# modules/m8_multirotor.py — STRICT TUTORIAL 4 COMPLIANT
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import json
import traceback  # <--- Ajout pour l'investigation des erreurs

try:
    import ross as rs
    ROSS_OK = True
except ImportError:
    ROSS_OK = False

# =============================================================================
# UTILITAIRE DE COMPATIBILITÉ MULTIROTOR
# =============================================================================
def build_multirotor_safely(r1, r2, gear, conn):
    """Gère les différences de signature de l'API ROSS selon les versions."""
    try:
        return rs.MultiRotor(rotors=[r1, r2], gear_elements=[gear], connections=[conn])
    except AttributeError:
        return rs.MultiRotor(r1, r2, gear_elements=[gear], connections=[conn])
    except TypeError:
        return rs.MultiRotor([r1, r2], [gear], [conn])


# =============================================================================
# MODÈLE DE VALIDATION (SÉQUENCE EXACTE DU TUTORIEL 4)
# =============================================================================

def build_tutorial_4_model():
    """Implémentation littérale du Tutorial 4 de ROSS."""
    # 1. Matériau
    mat = rs.Material(name="Steel", rho=7810, E=211e9, G_s=81.2e9)

    # 2. ROTOR 1
    shaft1 = [
        rs.ShaftElement(0.10, 0.0, 0.30, mat),
        rs.ShaftElement(4.24, 0.0, 0.30, mat),
        rs.ShaftElement(1.16, 0.0, 0.22, mat),
        rs.ShaftElement(0.30, 0.0, 0.22, mat),
    ]
    disks1 = [
        rs.DiskElement(0, 50.0, 1.50, 3.00),
        rs.DiskElement(4, 20.0, 0.50, 1.00),
    ]
    bearings1 = [
        rs.BearingElement(0, 1.839e8, 2.004e8, 3000.0, 3000.0),
        rs.BearingElement(3, 1.839e8, 2.004e8, 3000.0, 3000.0),
    ]
    r1 = rs.Rotor(shaft1, disks1, bearings1)

    # 3. ROTOR 2
    shaft2 = [
        rs.ShaftElement(1.50, 0.0, 0.25, mat),
        rs.ShaftElement(2.50, 0.0, 0.25, mat),
        rs.ShaftElement(1.00, 0.0, 0.20, mat),
    ]
    disks2 = [
        rs.DiskElement(3, 35.0, 1.20, 2.40),
    ]
    bearings2 = [
        rs.BearingElement(0, 1.5e8, 1.5e8, 2500.0, 2500.0),
        rs.BearingElement(2, 1.5e8, 1.5e8, 2500.0, 2500.0),
    ]
    r2 = rs.Rotor(shaft2, disks2, bearings2)

    # 4. GEAR ELEMENT
    gear = rs.GearElement(2, 5.0, 0.002, 0.004, 20, 0.5, np.radians(22.5))

    # 5. MULTI ROTOR
    multi = build_multirotor_safely(r1, r2, gear, (0, 2, 1, 1))
    
    return multi, r1, r2

# =============================================================================
# CHARGEMENT JSON (SÉCURISÉ ET ALIGNÉ)
# =============================================================================

def build_rotor_from_json(shaft_data, disk_data, bearing_data, material_obj):
    shaft_elements = [rs.ShaftElement(s["L (m)"], s["id_L (m)"], s["od_L (m)"], material_obj) for s in shaft_data]
    disk_elements = [rs.DiskElement(d["nœud"], d["Masse (kg)"], d["Id (kg.m²)"], d["Ip (kg.m²)"]) for d in disk_data]
    bearing_elements = [rs.BearingElement(b["nœud"], b["kxx"], b["kyy"], b["cxx"], b["cyy"]) for b in bearing_data]
    return rs.Rotor(shaft_elements, disk_elements, bearing_elements)

def load_multirotor_from_json(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    mat = rs.Material(name="Steel", rho=7810, E=211e9, G_s=81.2e9)
    
    r1 = build_rotor_from_json(data["shaft"], data["disks"], data["bearings"], mat)
    r2 = build_rotor_from_json(data["shaft_2"], data["disks_2"], data["bearings_2"], mat)
    
    g_info = data["gears"][0]
    gear = rs.GearElement(
        g_info["nœud_rotor_1"], 
        g_info["Masse (kg)"], 
        g_info["Id (kg.m²)"], 
        g_info["Ip (kg.m²)"], 
        g_info["n_teeth"], 
        g_info["pitch_diameter"], 
        np.radians(g_info["pr_angle"])
    )
    
    conn = (0, g_info["nœud_rotor_1"], 1, g_info["nœud_rotor_2"])
    multi = build_multirotor_safely(r1, r2, gear, conn)
    
    return multi, r1, r2

# =============================================================================
# INTERFACE STREAMLIT
# =============================================================================

def render_m8(col_settings, col_graphics):
    with col_settings:
        st.markdown('<div class="rl-settings-title">MultiRotor System [TUTORIAL 4]</div>', unsafe_allow_html=True)
        
        mode = st.radio("Source", ["Validation (Tutoriel 4)", "Charger JSON"], index=0)
        
        if mode == "Charger JSON":
            uploaded_file = st.file_uploader("Fichier .json", type=["json"])
            if uploaded_file:
                with open("temp_system.json", "wb") as f:
                    f.write(uploaded_file.getbuffer())
        
        if st.button("Assembler le système", type="primary", use_container_width=True):
            if not ROSS_OK:
                st.error("ROSS non installé.")
                return
            try:
                with st.spinner("Assemblage..."):
                    if mode == "Validation (Tutoriel 4)":
                        multi, r1, r2 = build_tutorial_4_model()
                    else:
                        multi, r1, r2 = load_multirotor_from_json("temp_system.json")
                    
                    st.session_state["m8_multi"] = multi
                    st.session_state["m8_rotor1"] = r1
                    st.session_state["m8_rotor2"] = r2
                    st.success("Système assemblé avec succès !")
            except Exception as e:
                # ── MODIFICATION ICI : Affichage complet de l'erreur ──
                st.error(f"Erreur : {e}")
                st.code(traceback.format_exc(), language="python")

        st.markdown("---")
        vmax = st.slider("Vitesse max (RPM)", 1000, 20000, 10000)
        if st.button("Calculer Campbell", use_container_width=True):
            if "m8_multi" in st.session_state:
                try:
                    speeds = np.linspace(0, vmax * np.pi / 30, 30)
                    st.session_state["m8_camp"] = st.session_state["m8_multi"].run_campbell(speeds, frequencies=10)
                    st.success("Calcul terminé !")
                except Exception as e:
                    st.error(f"Erreur : {e}")
                    st.code(traceback.format_exc(), language="python")

    with col_graphics:
        _display_results()

def _display_results():
    st.markdown('<div class="rl-graphics-title">Résultats</div>', unsafe_allow_html=True)
    if "m8_multi" not in st.session_state:
        st.info("Assemblez le système pour voir les résultats.")
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
