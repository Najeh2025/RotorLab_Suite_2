# modules/m8_multirotor.py — MultiRotor & GearElement
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
# =============================================================================

import streamlit as st
import numpy as np
import pandas as pd
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    import ross as rs
    ROSS_OK = True
except ImportError:
    ROSS_OK = False

from config import MATERIALS_DB


# =============================================================================
# POINT D'ENTRÉE
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
        '<div class="rl-settings-title">⚙️ MultiRotor & Gear Coupling</div>',
        unsafe_allow_html=True
    )

    tab_file, tab_calc = st.tabs(["📁 Modèle", "🚀 Calcul"])

    # ── CHARGEMENT DU MODÈLE JSON ─────────────────────────────────────────
    with tab_file:
        st.markdown("**Charger un système Multi-Rotor (.json)**")
        uploaded = st.file_uploader(
            "Upload JSON", type=["json"], label_visibility="collapsed", key="m8_upload"
        )
        
        if uploaded is not None:
            file_id = f"{uploaded.name}_{uploaded.size}"
            if st.session_state.get("m8_last_file_id") != file_id:
                try:
                    content = uploaded.read()
                    data = json.loads(content.decode("utf-8"))
                    
                    if "shaft_2" not in data or "gears" not in data:
                        st.error("❌ Fichier invalide : clés 'shaft_2' ou 'gears' manquantes pour un MultiRotor.")
                    else:
                        st.session_state["m8_data"] = data
                        st.session_state["m8_last_file_id"] = file_id
                        
                        # Réinitialiser les résultats précédents
                        for key in ["m8_multi", "m8_camp", "m8_modal1", "m8_modal2"]:
                            st.session_state[key] = None
                            
                        st.success(f"✅ Modèle Multi-Rotor '{data.get('name', 'Nouveau')}' chargé !")
                        st.rerun()
                except Exception as e:
                    st.error(f"Erreur de lecture : {e}")

        # Affichage rapide de ce qui est en mémoire
        data = st.session_state.get("m8_data")
        if data:
            st.info(f"Modèle actif : **{data.get('name', 'Système couplé')}**")
            with st.expander("Aperçu des données", expanded=False):
                st.json({
                    "Rotor 1": {"Elements": len(data.get("shaft", []))},
                    "Rotor 2": {"Elements": len(data.get("shaft_2", []))},
                    "Engrenage": data.get("gears", [{}])[0]
                })

    # ── PARAMÈTRES DE CALCUL ──────────────────────────────────────────────
    with tab_calc:
        st.markdown("**Paramètres de l'analyse dynamique**")
        c1, c2 = st.columns(2)
        with c1:
            st.number_input("Vitesse max Campbell (RPM)", 1000, 50000, 10000, key="m8_vmax")
            st.slider("Résolution (points)", 10, 100, 30, key="m8_npts")
        with c2:
            st.slider("Nombre de modes", 4, 20, 12, key="m8_n_modes")
            st.radio("Harmoniques", ["1X", "1X + fe"], index=1, key="m8_harm", horizontal=True)

        st.divider()
        if st.button("🚀 Assembler & Calculer", type="primary", use_container_width=True):
            if data:
                _run_multirotor()
            else:
                st.warning("Veuillez charger un fichier JSON multirotor d'abord.")


# =============================================================================
# LOGIQUE D'ASSEMBLAGE ET CALCUL
# =============================================================================
def _get_material(mat_name):
    """Récupère le matériau ou retourne un acier par défaut."""
    if mat_name in MATERIALS_DB:
        p = MATERIALS_DB[mat_name]
        return rs.Material(name=mat_name, rho=p["rho"], E=p["E"], G_s=p["G_s"])
    return rs.Material(name="Steel", rho=7810, E=211e9, G_s=81.2e9)

def _build_rotor_from_dict(data, suffix=""):
    """Construit un rotor unitaire à partir du dictionnaire extrait du JSON."""
    mat_name = data.get("material", "Acier standard (AISI 1045)")
    mat = _get_material(mat_name)
    
    # 1. Arbre
    shaft_list = data.get(f"shaft{suffix}", [])
    shaft = [rs.ShaftElement(
                L=r["L (m)"], idl=r["id_L (m)"], odl=r["od_L (m)"],
                idr=r["id_R (m)"], odr=r["od_R (m)"], material=mat
             ) for r in shaft_list]
    
    # 2. Disques
    disks = [rs.DiskElement(
                n=r["nœud"], m=r["Masse (kg)"], Id=r["Id (kg.m²)"], Ip=r["Ip (kg.m²)"]
             ) for r in data.get(f"disks{suffix}", [])]
             
    # 3. Paliers
    bearings = []
    for r in data.get(f"bearings{suffix}", []):
        bearings.append(rs.BearingElement(
            n=r["nœud"], kxx=r.get("kxx", 1e6), kyy=r.get("kyy", 1e6),
            cxx=r.get("cxx", 0), cyy=r.get("cyy", 0)
        ))
        
    return shaft, disks, bearings

def _run_multirotor():
    if not ROSS_OK:
        st.error("❌ ROSS non disponible.")
        return

    data = st.session_state["m8_data"]
    
    with st.spinner("Assemblage des rotors et calcul matriciel..."):
        try:
            # Récupération des composants de base (sans engrenages)
            s1, d1, b1 = _build_rotor_from_dict(data, suffix="")
            s2, d2, b2 = _build_rotor_from_dict(data, suffix="_2")
            
            # Gestion de l'engrenage
            gear_data = data.get("gears", [{}])[0]
            n1 = gear_data.get("nœud_rotor_1", 0)
            n2 = gear_data.get("nœud_rotor_2", 0)
            
            # Paramètres de l'engrenage
            mg = float(gear_data.get("Masse (kg)", 5.0))
            Ig = float(gear_data.get("Id (kg.m²)", 0.002))
            Ipg = float(gear_data.get("Ip (kg.m²)", 0.004))
            
            z1 = int(gear_data.get("n_teeth", 20))
            z2 = int(gear_data.get("n_teeth_2", z1 * 1.5)) # Fallback si absent
            d1_val = float(gear_data.get("pitch_diameter", 0.1))
            d2_val = float(gear_data.get("pitch_diameter_2", d1_val * 1.5)) # Fallback si absent
            
            alpha = np.radians(float(gear_data.get("pr_angle", 20.0)))

            # ⚙️ CORRECTION: On utilise pr_angle et on crée un engrenage par arbre
            gear1 = rs.GearElement(
                n=n1, m=mg/2, Id=Ig/2, Ip=Ipg/2,
                n_teeth=z1, pitch_diameter=d1_val, pr_angle=alpha
            )
            gear2 = rs.GearElement(
                n=n2, m=mg/2, Id=Ig/2, Ip=Ipg/2,
                n_teeth=z2, pitch_diameter=d2_val, pr_angle=alpha
            )

            # ⚙️ CORRECTION: On injecte les GearElements directement dans chaque Rotor
            rotor1 = rs.Rotor(shaft_elements=s1, disk_elements=d1, bearing_elements=b1, gear_elements=[gear1])
            rotor2 = rs.Rotor(shaft_elements=s2, disk_elements=d2, bearing_elements=b2, gear_elements=[gear2])
            
            st.session_state["m8_rotor1"] = rotor1
            st.session_state["m8_rotor2"] = rotor2

            # Assemblage du système couplé
            multi = rs.MultiRotor(rotor1, rotor2)
            st.session_state["m8_multi"] = multi

            # Lancement des calculs Dynamiques
            vmax = st.session_state["m8_vmax"]
            npts = st.session_state["m8_npts"]
            n_modes = st.session_state["m8_n_modes"]
            
            speeds = np.linspace(0, vmax * np.pi / 30, npts)
            camp = multi.run_campbell(speeds, frequencies=n_modes)
            st.session_state["m8_camp"] = camp
            
            # Modes propres à l'arrêt pour vérification
            st.session_state["m8_modal1"] = rotor1.run_modal(speed=0)
            st.session_state["m8_modal2"] = rotor2.run_modal(speed=0)

            st.toast("Calculs du système couplé terminés avec succès !", icon="✅")

        except Exception as e:
            st.error(f"❌ Erreur lors du calcul MultiRotor : {e}")
            import traceback
            st.code(traceback.format_exc(), language="python")


# =============================================================================
# PANNEAU GRAPHICS
# =============================================================================
def _render_graphics():
    st.markdown(
        '<div class="rl-graphics-title">🏗️ MultiRotor Analysis Results</div>',
        unsafe_allow_html=True
    )

    multi = st.session_state.get("m8_multi")
    
    if multi is None:
        st.info("Veuillez charger un JSON Multi-Rotor et lancer l'assemblage.")
        return

    tab_geo, tab_camp, tab_modal = st.tabs(["Géométrie 3D", "Campbell Couplé", "Modes Individuels"])

    r1 = st.session_state["m8_rotor1"]
    r2 = st.session_state["m8_rotor2"]
    data = st.session_state["m8_data"]
    gear = data.get("gears", [{}])[0]

    with tab_geo:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Rotor 1 (Moteur)** - {r1.m:.1f} kg")
            fig1 = r1.plot_rotor()
            fig1.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig1, use_container_width=True, key="m8_geo_r1")
        with c2:
            st.markdown(f"**Rotor 2 (Mené)** - {r2.m:.1f} kg")
            fig2 = r2.plot_rotor()
            fig2.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig2, use_container_width=True, key="m8_geo_r2")
            
        st.divider()
        st.markdown("**🔗 Rapport d'engrenage (Couplage)**")
        
        d1 = gear.get("pitch_diameter", 0.1)
        z1 = gear.get("n_teeth", 20)
        
        c_ratio, _, _ = st.columns(3)
        c_ratio.metric("Diamètre Primitif (Rotor 1)", f"{d1} m")
        c_ratio.metric("Dents du pignon (Rotor 1)", str(z1))

    with tab_camp:
        camp = st.session_state.get("m8_camp")
        if camp:
            try:
                fig_c = camp.plot()
                fig_c.update_layout(
                    title="Diagramme de Campbell du système complet couplé",
                    height=500, plot_bgcolor="white"
                )
                
                # Ajout des lignes harmoniques manuelles (1X et fe)
                vmax = st.session_state["m8_vmax"]
                spd_rpm = np.array([0, vmax])
                harm_sel = st.session_state["m8_harm"]
                
                fig_c.add_trace(go.Scatter(x=spd_rpm, y=spd_rpm/60, name="1X (Rotor 1)", line=dict(dash="dot", color="red")))
                
                if "fe" in harm_sel:
                    fe = (spd_rpm/60) * z1
                    fig_c.add_trace(go.Scatter(x=spd_rpm, y=fe, name="Fréq. Engrènement (fe)", line=dict(dash="dashdot", color="purple")))

                st.plotly_chart(fig_c, use_container_width=True, key="m8_camp_plot")
            except Exception as e:
                st.warning(f"Impossible de tracer le Campbell: {e}")

    with tab_modal:
        mod1 = st.session_state.get("m8_modal1")
        mod2 = st.session_state.get("m8_modal2")
        
        if mod1 and mod2:
            st.markdown("**Comparaison des fréquences propres à l'arrêt (Hz)**")
            n = min(6, len(mod1.wn), len(mod2.wn))
            fn1 = mod1.wn[:n] / (2*np.pi)
            fn2 = mod2.wn[:n] / (2*np.pi)
            
            fig_m = go.Figure()
            fig_m.add_trace(go.Bar(name="Rotor 1", x=[f"Mode {i+1}" for i in range(n)], y=fn1, marker_color="#1F5C8B"))
            fig_m.add_trace(go.Bar(name="Rotor 2", x=[f"Mode {i+1}" for i in range(n)], y=fn2, marker_color="#C55A11"))
            fig_m.update_layout(barmode="group", height=400, plot_bgcolor="white", yaxis_title="Fréquence (Hz)")
            st.plotly_chart(fig_m, use_container_width=True, key="m8_modal_plot")
            
            st.caption("Note : Ces modes sont calculés pour les rotors isolés (non couplés) pour observer les risques de résonance individuelle.")
