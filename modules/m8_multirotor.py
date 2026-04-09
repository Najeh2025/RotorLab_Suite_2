# modules/m8_multirotor.py — MultiRotor & GearElement
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
# Couvre : GearElement, MultiRotor, Campbell couple, analyse torsionnelle
# =============================================================================

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    import ross as rs
    ROSS_OK = True
except ImportError:
    ROSS_OK = False


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
        unsafe_allow_html=True
    )
    st.markdown(
        '<span class="rl-badge rl-badge-new">NEW v2.0</span>',
        unsafe_allow_html=True
    )

    tab_r1, tab_r2, tab_gear, tab_run = st.tabs([
        "Rotor 1 (Moteur)",
        "Rotor 2 (Recepteur)",
        "Engrenage",
        "Calcul"
    ])

    # ── ROTOR 1 ───────────────────────────────────────────────────────────
    with tab_r1:
        st.markdown(
            '<div class="rl-section-header">Geometrie Rotor 1</div>',
            unsafe_allow_html=True
        )
        c1, c2 = st.columns(2)
        with c1:
            st.slider(
                "Nombre d elements d arbre",
                2, 10, 4,
                key="m8_r1_nel"
            )
            st.number_input(
                "Longueur par element (m)",
                0.05, 1.0, 0.25,
                key="m8_r1_L"
            )
            st.number_input(
                "Diametre arbre (m)",
                0.01, 0.3, 0.05,
                key="m8_r1_od"
            )
        with c2:
            st.selectbox(
                "Materiau",
                ["Acier standard (AISI 1045)",
                 "Acier inoxydable (316L)",
                 "Titane (Ti-6Al-4V)",
                 "Inconel 718"],
                key="m8_r1_mat"
            )
            st.number_input(
                "Vitesse operationnelle (RPM)",
                100.0, 30000.0, 3000.0,
                key="m8_r1_rpm"
            )

        st.markdown(
            '<div class="rl-section-header">Disque Rotor 1</div>',
            unsafe_allow_html=True
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            st.slider(
                "Noeud du disque",
                0,
                st.session_state.get("m8_r1_nel", 4),
                st.session_state.get("m8_r1_nel", 4) // 2,
                key="m8_r1_disk_node"
            )
        with c2:
            st.number_input(
                "Diametre disque (m)",
                0.05, 0.8, 0.25,
                key="m8_r1_disk_od"
            )
        with c3:
            st.number_input(
                "Largeur disque (m)",
                0.01, 0.3, 0.07,
                key="m8_r1_disk_w"
            )

        st.markdown(
            '<div class="rl-section-header">Paliers Rotor 1</div>',
            unsafe_allow_html=True
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            st.number_input(
                "Kxx palier (N/m)",
                1e4, 1e10, 1e7,
                format="%.2e",
                key="m8_r1_kxx"
            )
        with c2:
            st.number_input(
                "Kyy palier (N/m)",
                1e4, 1e10, 1e7,
                format="%.2e",
                key="m8_r1_kyy"
            )
        with c3:
            st.number_input(
                "Cxx palier (N.s/m)",
                0.0, 1e5, 500.0,
                key="m8_r1_cxx"
            )

    # ── ROTOR 2 ───────────────────────────────────────────────────────────
    with tab_r2:
        st.markdown(
            '<div class="rl-section-header">Geometrie Rotor 2</div>',
            unsafe_allow_html=True
        )
        c1, c2 = st.columns(2)
        with c1:
            st.slider(
                "Nombre d elements d arbre",
                2, 10, 3,
                key="m8_r2_nel"
            )
            st.number_input(
                "Longueur par element (m)",
                0.05, 1.0, 0.25,
                key="m8_r2_L"
            )
            st.number_input(
                "Diametre arbre (m)",
                0.01, 0.3, 0.04,
                key="m8_r2_od"
            )
        with c2:
            st.selectbox(
                "Materiau",
                ["Acier standard (AISI 1045)",
                 "Acier inoxydable (316L)",
                 "Titane (Ti-6Al-4V)",
                 "Inconel 718"],
                key="m8_r2_mat"
            )
            st.caption(
                "Vitesse R2 = Vitesse R1 x (dents R1 / dents R2)"
            )

        st.markdown(
            '<div class="rl-section-header">Disque Rotor 2</div>',
            unsafe_allow_html=True
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            st.slider(
                "Noeud du disque",
                0,
                st.session_state.get("m8_r2_nel", 3),
                st.session_state.get("m8_r2_nel", 3) // 2,
                key="m8_r2_disk_node"
            )
        with c2:
            st.number_input(
                "Diametre disque (m)",
                0.05, 0.8, 0.20,
                key="m8_r2_disk_od"
            )
        with c3:
            st.number_input(
                "Largeur disque (m)",
                0.01, 0.3, 0.06,
                key="m8_r2_disk_w"
            )

        st.markdown(
            '<div class="rl-section-header">Paliers Rotor 2</div>',
            unsafe_allow_html=True
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            st.number_input(
                "Kxx palier (N/m)",
                1e4, 1e10, 1e7,
                format="%.2e",
                key="m8_r2_kxx"
            )
        with c2:
            st.number_input(
                "Kyy palier (N/m)",
                1e4, 1e10, 1e7,
                format="%.2e",
                key="m8_r2_kyy"
            )
        with c3:
            st.number_input(
                "Cxx palier (N.s/m)",
                0.0, 1e5, 500.0,
                key="m8_r2_cxx"
            )

    # ── ENGRENAGE ─────────────────────────────────────────────────────────
    with tab_gear:
        st.markdown(
            '<div class="rl-section-header">Parametres de l engrenage</div>',
            unsafe_allow_html=True
        )
        st.markdown("""
        <div class="rl-card-info">
          <small>Le GearElement couple les deux rotors via la ligne
          d action des dents. Le rapport de reduction est determine
          par le nombre de dents (z1/z2) ou les diametres primitifs.</small>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Pignon (Rotor 1) :**")
            st.number_input(
                "Noeud pignon (Rotor 1)",
                0,
                st.session_state.get("m8_r1_nel", 4),
                st.session_state.get("m8_r1_nel", 4),
                step=1,
                key="m8_gear_n1"
            )
            st.number_input(
                "Diametre primitif pignon (m)",
                0.02, 1.0, 0.10,
                key="m8_gear_d1"
            )
            st.number_input(
                "Nombre de dents pignon (z1)",
                5, 200, 20,
                step=1,
                key="m8_gear_z1"
            )
        with c2:
            st.markdown("**Roue dentee (Rotor 2) :**")
            st.number_input(
                "Noeud roue (Rotor 2)",
                0,
                st.session_state.get("m8_r2_nel", 3),
                0,
                step=1,
                key="m8_gear_n2"
            )
            st.number_input(
                "Diametre primitif roue (m)",
                0.02, 1.0, 0.15,
                key="m8_gear_d2"
            )
            st.number_input(
                "Nombre de dents roue (z2)",
                5, 200, 30,
                step=1,
                key="m8_gear_z2"
            )

        st.markdown(
            '<div class="rl-section-header">Geometrie de l engrenage</div>',
            unsafe_allow_html=True
        )
        c1, c2 = st.columns(2)
        with c1:
            st.number_input(
                "Angle de pression (deg)",
                14.5, 30.0, 20.0,
                key="m8_gear_alpha"
            )
        with c2:
            st.number_input(
                "Angle d helice (deg)",
                0.0, 45.0, 0.0,
                key="m8_gear_beta",
                help="0 = engrenage droit, > 0 = helicoidale"
            )

        # Affichage du rapport de reduction calcule
        z1  = int(st.session_state.get("m8_gear_z1", 20))
        z2  = int(st.session_state.get("m8_gear_z2", 30))
        d1  = float(st.session_state.get("m8_gear_d1", 0.10))
        d2  = float(st.session_state.get("m8_gear_d2", 0.15))
        rpm1 = float(st.session_state.get("m8_r1_rpm", 3000.0))
        rpm2 = rpm1 * z1 / z2

        c1, c2, c3 = st.columns(3)
        c1.metric("Rapport i = z1/z2", "{:.3f}".format(z1 / z2))
        c2.metric("Vitesse Rotor 1", "{:.0f} RPM".format(rpm1))
        c3.metric("Vitesse Rotor 2", "{:.0f} RPM".format(rpm2))

        freq_eng = rpm1 / 60 * z1
        st.info(
            "Frequence d engrenement : **{:.1f} Hz** "
            "({:.0f} CPM)".format(freq_eng, freq_eng * 60)
        )

    # ── CALCUL ────────────────────────────────────────────────────────────
    with tab_run:
        st.markdown(
            '<div class="rl-section-header">Parametres de calcul</div>',
            unsafe_allow_html=True
        )

        c1, c2 = st.columns(2)
        with c1:
            st.slider(
                "Vitesse max Campbell (RPM)",
                1000, 30000, 10000,
                key="m8_vmax"
            )
            st.slider(
                "Resolution Campbell (points)",
                10, 80, 30,
                key="m8_npts"
            )
        with c2:
            st.slider(
                "Nombre de modes a calculer",
                4, 20, 12,
                key="m8_n_modes"
            )
            st.radio(
                "Harmoniques a afficher",
                ["1X", "1X + 2X", "1X + 2X + fe"],
                index=2,
                horizontal=True,
                key="m8_harmonics",
                help="fe = frequence d engrenement"
            )

        st.markdown("---")
        st.button(
            "Assembler et calculer le MultiRotor",
            type="primary",
            key="m8_run",
            use_container_width=True,
            on_click=_run_multirotor
        )

        # Affichage statut
        r1 = st.session_state.get("m8_rotor1")
        r2 = st.session_state.get("m8_rotor2")
        if r1 and r2:
            st.success(
                "Rotors assembles — R1: {} noeuds | "
                "R2: {} noeuds".format(
                    len(r1.nodes), len(r2.nodes))
            )
        if st.session_state.get("m8_error"):
            st.error(st.session_state["m8_error"])


# =============================================================================
# PANNEAU GRAPHICS
# =============================================================================
def _render_graphics():
    st.markdown(
        '<div class="rl-graphics-title">'
        'MultiRotor & GearElement — Results'
        '</div>',
        unsafe_allow_html=True
    )

    tab_geo, tab_camp, tab_modal, tab_theory = st.tabs([
        "Geometrie 3D",
        "Campbell couple",
        "Analyse modale",
        "Theorie"
    ])

    with tab_geo:
        _display_geometry()

    with tab_camp:
        _display_campbell()

    with tab_modal:
        _display_modal()

    with tab_theory:
        _display_theory()


# =============================================================================
# CONSTRUCTION DES ROTORS
# =============================================================================
def _get_material(mat_name):
    """Retourne un objet rs.Material selon le nom."""
    mats = {
        "Acier standard (AISI 1045)": (7810, 211e9, 81.2e9),
        "Acier inoxydable (316L)":    (7990, 193e9, 74.0e9),
        "Titane (Ti-6Al-4V)":         (4430, 114e9, 44.0e9),
        "Inconel 718":                (8220, 200e9, 77.0e9),
    }
    rho, E, G = mats.get(mat_name, (7810, 211e9, 81.2e9))
    return rs.Material(
        name=mat_name.replace(" ", "_").replace("(", "").replace(")", ""),
        rho=rho, E=E, G_s=G
    )


def _build_single_rotor(prefix):
    """Construit un rs.Rotor depuis les parametres session."""
    nel  = int(st.session_state.get("{}_nel".format(prefix),  4))
    L    = float(st.session_state.get("{}_L".format(prefix),   0.25))
    od   = float(st.session_state.get("{}_od".format(prefix),  0.05))
    mat_n = st.session_state.get("{}_mat".format(prefix),
                                  "Acier standard (AISI 1045)")
    kxx  = float(st.session_state.get("{}_kxx".format(prefix), 1e7))
    kyy  = float(st.session_state.get("{}_kyy".format(prefix), 1e7))
    cxx  = float(st.session_state.get("{}_cxx".format(prefix), 500.0))
    dn   = int(st.session_state.get("{}_disk_node".format(prefix), nel // 2))
    dod  = float(st.session_state.get("{}_disk_od".format(prefix), 0.25))
    dw   = float(st.session_state.get("{}_disk_w".format(prefix),  0.07))

    mat   = _get_material(mat_n)
    shaft = [
        rs.ShaftElement(L=L, idl=0.0, odl=od, material=mat)
        for _ in range(nel)
    ]
    disk = rs.DiskElement.from_geometry(
        n=min(dn, nel),
        material=mat,
        width=dw,
        i_d=od,
        o_d=dod
    )
    b0 = rs.BearingElement(
        n=0, kxx=kxx, kyy=kyy, kxy=0.0, kyx=0.0, cxx=cxx, cyy=cxx)
    bn = rs.BearingElement(
        n=nel, kxx=kxx, kyy=kyy, kxy=0.0, kyx=0.0, cxx=cxx, cyy=cxx)

    return rs.Rotor(shaft, [disk], [b0, bn])


# =============================================================================
# CALCUL MULTIROTOR
# =============================================================================
def _run_multirotor():
    if not ROSS_OK:
        st.session_state["m8_error"] = "ROSS non disponible."
        return

    try:
        # Construction des deux rotors
        r1 = _build_single_rotor("m8_r1")
        r2 = _build_single_rotor("m8_r2")

        st.session_state["m8_rotor1"] = r1
        st.session_state["m8_rotor2"] = r2
        st.session_state["m8_error"]  = None
        _log("Rotors construits — R1:{} noeuds, R2:{} noeuds".format(
            len(r1.nodes), len(r2.nodes)), "ok")

        # Parametres engrenage
        n1    = int(st.session_state.get("m8_gear_n1",    4))
        n2    = int(st.session_state.get("m8_gear_n2",    0))
        d1    = float(st.session_state.get("m8_gear_d1",  0.10))
        d2    = float(st.session_state.get("m8_gear_d2",  0.15))
        alpha = float(st.session_state.get("m8_gear_alpha", 20.0))
        beta  = float(st.session_state.get("m8_gear_beta",   0.0))
        vmax  = float(st.session_state.get("m8_vmax",     10000))
        npts  = int(st.session_state.get("m8_npts",       30))
        n_modes = int(st.session_state.get("m8_n_modes",  12))

        # Tentative MultiRotor avec GearElement
        try:
            gear = rs.GearElement(
                n=min(n1, len(r1.nodes) - 1),
                pitch_diameter=d1,
                pressure_angle=np.radians(alpha),
                helix_angle=np.radians(beta)
            )

            # Tentative assemblage MultiRotor
            try:
                multi = rs.MultiRotor(
                    rotors=[r1, r2],
                    gear_elements=[gear],
                    connections=[(0, n1, 1, n2)]
                )
                st.session_state["m8_multi"] = multi

                # Campbell du systeme couple
                speeds = np.linspace(0, vmax * np.pi / 30, npts)
                camp   = multi.run_campbell(speeds, frequencies=n_modes)
                st.session_state["m8_camp"]  = camp
                st.session_state["m8_camp_vmax"] = vmax
                _log("MultiRotor couple calcule ({} pts)".format(npts), "ok")

            except Exception as e_multi:
                # Fallback : Campbell individuel des deux rotors
                _log(
                    "MultiRotor non dispo ({}) — "
                    "Campbell individuel".format(e_multi), "warn"
                )
                st.session_state["m8_multi"]       = None
                st.session_state["m8_multi_error"] = str(e_multi)

                speeds = np.linspace(0, vmax * np.pi / 30, npts)
                camp1  = r1.run_campbell(speeds, frequencies=n_modes)
                camp2  = r2.run_campbell(
                    speeds * (float(st.session_state.get("m8_gear_z1", 20)) /
                              float(st.session_state.get("m8_gear_z2", 30))),
                    frequencies=n_modes
                )
                st.session_state["m8_camp1"]     = camp1
                st.session_state["m8_camp2"]     = camp2
                st.session_state["m8_camp_vmax"] = vmax
                _log("Campbell individuel R1 et R2 calcules", "ok")

        except Exception as e_gear:
            _log("GearElement non disponible : {}".format(e_gear), "warn")
            st.session_state["m8_gear_error"] = str(e_gear)
            # Fallback : analyse independante des deux rotors
            speeds = np.linspace(0, vmax * np.pi / 30, npts)
            camp1  = r1.run_campbell(speeds, frequencies=n_modes)
            camp2  = r2.run_campbell(speeds, frequencies=n_modes)
            st.session_state["m8_camp1"]     = camp1
            st.session_state["m8_camp2"]     = camp2
            st.session_state["m8_camp_vmax"] = vmax
            _log("Analyse independante des deux rotors", "ok")

        # Analyse modale des deux rotors
        modal1 = r1.run_modal(speed=0)
        modal2 = r2.run_modal(speed=0)
        st.session_state["m8_modal1"] = modal1
        st.session_state["m8_modal2"] = modal2

    except Exception as e:
        st.session_state["m8_error"] = str(e)
        _log("Erreur MultiRotor : {}".format(e), "err")


# =============================================================================
# AFFICHAGE GEOMETRIE 3D
# =============================================================================
def _display_geometry():
    r1 = st.session_state.get("m8_rotor1")
    r2 = st.session_state.get("m8_rotor2")

    if r1 is None or r2 is None:
        st.info(
            "Assemblez le MultiRotor depuis l'onglet Calcul "
            "dans le panneau Settings."
        )
        _show_multirotor_preview()
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Rotor 1 (Moteur)**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Masse", "{:.2f} kg".format(r1.m))
        c2.metric("Noeuds", str(len(r1.nodes)))
        c3.metric("RPM", "{:.0f}".format(
            float(st.session_state.get("m8_r1_rpm", 3000))))
        try:
            fig1 = r1.plot_rotor()
            fig1.update_layout(
                height=300,
                title="Rotor 1",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig1, use_container_width=True,
                            key="m8_geo_r1")
        except Exception as e:
            st.warning("Visualisation R1 : {}".format(e))

    with col2:
        z1  = int(st.session_state.get("m8_gear_z1", 20))
        z2  = int(st.session_state.get("m8_gear_z2", 30))
        rpm2 = float(st.session_state.get("m8_r1_rpm", 3000)) * z1 / z2

        st.markdown("**Rotor 2 (Recepteur)**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Masse", "{:.2f} kg".format(r2.m))
        c2.metric("Noeuds", str(len(r2.nodes)))
        c3.metric("RPM", "{:.0f}".format(rpm2))
        try:
            fig2 = r2.plot_rotor()
            fig2.update_layout(
                height=300,
                title="Rotor 2",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig2, use_container_width=True,
                            key="m8_geo_r2")
        except Exception as e:
            st.warning("Visualisation R2 : {}".format(e))

    # Infos engrenage
    d1    = float(st.session_state.get("m8_gear_d1",    0.10))
    d2    = float(st.session_state.get("m8_gear_d2",    0.15))
    alpha = float(st.session_state.get("m8_gear_alpha", 20.0))
    beta  = float(st.session_state.get("m8_gear_beta",   0.0))
    freq_eng = float(st.session_state.get("m8_r1_rpm", 3000)) / 60 * z1

    st.markdown("---")
    st.markdown("**Engrenage — Parametres de couplage :**")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("i = z1/z2", "{:.3f}".format(z1 / z2))
    c2.metric("d1 (m)", "{:.3f}".format(d1))
    c3.metric("d2 (m)", "{:.3f}".format(d2))
    c4.metric("fe (Hz)", "{:.1f}".format(freq_eng))
    c5.metric("Angle pression", "{:.1f} deg".format(alpha))

    if st.session_state.get("m8_multi_error"):
        st.markdown("""
        <div class="rl-card-warn">
          <strong>Note :</strong> MultiRotor couple non disponible
          dans cette version de ROSS ({}). Les Campbell individuels
          sont affiches.
        </div>
        """.format(st.session_state["m8_multi_error"]),
            unsafe_allow_html=True)


def _show_multirotor_preview():
    """Affiche un schema SVG du systeme MultiRotor."""
    st.markdown("""
    <div class="rl-card-info">
      <strong>Systeme MultiRotor :</strong><br>
      <small>Deux rotors couples par un engrenage. Le rapport de reduction
      i = z1/z2 determine la vitesse relative des deux arbres.
      L'analyse Campbell du systeme couple revele les modes lateraux
      de chaque rotor et les modes torsionnels couples.</small>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ```
    Palier          Pignon          Palier
      |               |               |
    --|----[Arbre 1]--[G]--[Arbre 1]--|--
                      |
                     [G]  (z1/z2)
                      |
    --|----[Arbre 2]--[G]--[Arbre 2]--|--
      |               |               |
    Palier          Roue           Palier
    ```
    """)


# =============================================================================
# AFFICHAGE CAMPBELL COUPLE
# =============================================================================
def _display_campbell():
    camp_multi = st.session_state.get("m8_camp")
    camp1      = st.session_state.get("m8_camp1")
    camp2      = st.session_state.get("m8_camp2")

    if camp_multi is None and camp1 is None:
        st.info(
            "Assemblez le MultiRotor depuis l'onglet Calcul "
            "dans le panneau Settings."
        )
        return

    vmax      = float(st.session_state.get("m8_camp_vmax", 10000))
    rpm1      = float(st.session_state.get("m8_r1_rpm",   3000.0))
    z1        = int(st.session_state.get("m8_gear_z1",    20))
    z2        = int(st.session_state.get("m8_gear_z2",    30))
    rpm2      = rpm1 * z1 / z2
    freq_eng  = rpm1 / 60 * z1
    harmonics = st.session_state.get("m8_harmonics", "1X + 2X + fe")

    fig = go.Figure()

    colors_r1 = ["#1F5C8B", "#0288D1", "#00796B", "#388E3C",
                 "#1565C0", "#006064"]
    colors_r2 = ["#C55A11", "#E64A19", "#C62828", "#AD1457",
                 "#6A1B9A", "#00695C"]

    def _add_camp_traces(camp, speed_ref_rpm, colors, label_prefix):
        if hasattr(camp, 'speed_range') and camp.speed_range is not None:
            spd_rad = np.array(camp.speed_range)
        else:
            npts    = int(st.session_state.get("m8_npts", 30))
            spd_rad = np.linspace(0, vmax * np.pi / 30, npts)
        spd_rpm = spd_rad * 30 / np.pi

        if hasattr(camp, 'wd') and camp.wd is not None:
            fn_mat = camp.wd / (2 * np.pi)
        elif hasattr(camp, 'wn') and camp.wn is not None:
            fn_mat = camp.wn / (2 * np.pi)
        else:
            return

        whirl   = getattr(camp, 'whirl', None)
        n_modes = fn_mat.shape[1]

        for i in range(min(6, n_modes)):
            fn_i  = fn_mat[:, i]
            if whirl is not None:
                mid   = len(spd_rpm) // 2
                w_val = str(whirl[mid, i]).lower()
                is_fw = "forward" in w_val
            else:
                is_fw = fn_i[-1] > fn_i[0]

            color = colors[i % len(colors)]
            dash  = "solid" if is_fw else "dash"
            lbl   = "{} M{} ({})".format(
                label_prefix, i + 1, "FW" if is_fw else "BW")

            fig.add_trace(go.Scatter(
                x=spd_rpm, y=fn_i,
                name=lbl,
                line=dict(color=color, width=2, dash=dash),
                hovertemplate=(
                    "Omega = %{x:.0f} RPM<br>"
                    "fn = %{y:.2f} Hz<extra>" + lbl + "</extra>"
                )
            ))

    if camp_multi is not None:
        _add_camp_traces(
            camp_multi, rpm1, colors_r1, "Couple")
    else:
        if camp1 is not None:
            _add_camp_traces(camp1, rpm1, colors_r1, "R1")
        if camp2 is not None:
            _add_camp_traces(camp2, rpm2, colors_r2, "R2")

    # Harmoniques
    x_line = np.array([0, vmax])
    if "1X" in harmonics:
        fig.add_trace(go.Scatter(
            x=x_line, y=x_line / 60,
            name="1X (R1)",
            line=dict(color="#E53935", width=1.5, dash="dot")
        ))
        fig.add_trace(go.Scatter(
            x=x_line, y=x_line / 60 * z1 / z2,
            name="1X (R2)",
            line=dict(color="#FB8C00", width=1.5, dash="dot")
        ))
    if "2X" in harmonics:
        fig.add_trace(go.Scatter(
            x=x_line, y=x_line / 30,
            name="2X (R1)",
            line=dict(color="#E57373", width=1, dash="dot"),
            opacity=0.7
        ))
    if "fe" in harmonics:
        # Frequence d'engrenement = rpm1/60 * z1
        fig.add_trace(go.Scatter(
            x=x_line, y=x_line / 60 * z1,
            name="fe (engrenement)",
            line=dict(color="#7B1FA2", width=2, dash="dashdot")
        ))

    # Vitesses operationnelles
    fig.add_vline(
        x=rpm1,
        line_dash="dash", line_color="#1F5C8B", line_width=1.5,
        annotation_text=" Nop R1 = {:.0f}".format(rpm1),
        annotation_font=dict(color="#1F5C8B")
    )
    fig.add_vline(
        x=rpm2,
        line_dash="dash", line_color="#C55A11", line_width=1.5,
        annotation_text=" Nop R2 = {:.0f}".format(rpm2),
        annotation_font=dict(color="#C55A11")
    )

    title_str = "Campbell MultiRotor couple" \
        if camp_multi else \
        "Campbell R1 (bleu) + R2 (orange) — independants"

    fig.update_layout(
        height=500,
        title=title_str,
        xaxis_title="Vitesse Rotor 1 (RPM)",
        yaxis_title="Frequence (Hz)",
        plot_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#F0F4FF"),
        yaxis=dict(showgrid=True, gridcolor="#F0F4FF"),
        legend=dict(
            orientation="h", yanchor="bottom",
            y=1.02, xanchor="right", x=1,
            font=dict(size=10)
        )
    )

    st.plotly_chart(fig, use_container_width=True, key="m8_camp_fig")

    # Tableau frequence d'engrenement
    st.markdown("**Frequences caracteristiques du systeme :**")
    df_freq = pd.DataFrame({
        "Grandeur": [
            "Vitesse R1 (operationnelle)",
            "Vitesse R2",
            "Rapport de reduction i",
            "Frequence d engrenement fe",
            "fe harmonique 2 (2*fe)",
            "fe harmonique 3 (3*fe)"
        ],
        "Valeur": [
            "{:.0f} RPM".format(rpm1),
            "{:.0f} RPM".format(rpm2),
            "{:.4f}".format(z1 / z2),
            "{:.2f} Hz".format(freq_eng),
            "{:.2f} Hz".format(2 * freq_eng),
            "{:.2f} Hz".format(3 * freq_eng)
        ],
        "Note": [
            "Reference",
            "R1 x z1/z2",
            "z1/z2 = {}/{}".format(z1, z2),
            "rpm1/60 x z1",
            "Harmonique 2",
            "Harmonique 3"
        ]
    })
    st.dataframe(df_freq, use_container_width=True, hide_index=True)


# =============================================================================
# AFFICHAGE MODAL
# =============================================================================
def _display_modal():
    modal1 = st.session_state.get("m8_modal1")
    modal2 = st.session_state.get("m8_modal2")

    if modal1 is None and modal2 is None:
        st.info(
            "Assemblez le MultiRotor pour calculer les modes propres."
        )
        return

    col1, col2 = st.columns(2)

    def _make_modal_df(modal, label):
        fn = modal.wn / (2 * np.pi)
        ld = getattr(modal, 'log_dec', np.zeros(len(fn)))
        n  = min(8, len(fn))
        rows = []
        for i in range(n):
            rows.append({
                "Mode":      i + 1,
                "fn (Hz)":   "{:.3f}".format(fn[i]),
                "Log Dec":   "{:.4f}".format(ld[i]),
                "Statut":    (
                    "INSTABLE" if ld[i] <= 0 else
                    "Marginal" if ld[i] < 0.1 else "OK"
                )
            })
        return pd.DataFrame(rows)

    with col1:
        if modal1 is not None:
            r1 = st.session_state.get("m8_rotor1")
            rpm1 = float(st.session_state.get("m8_r1_rpm", 3000))
            st.markdown(
                "**Rotor 1 — {:.0f} RPM | {:.2f} kg**".format(
                    rpm1, r1.m if r1 else 0)
            )
            df1 = _make_modal_df(modal1, "R1")
            st.dataframe(df1, use_container_width=True, hide_index=True)

            # Deformee mode 0
            n_modes1 = min(6, len(modal1.wn))
            mode_sel1 = st.selectbox(
                "Mode R1 a visualiser :",
                list(range(n_modes1)),
                format_func=lambda x: "Mode {} — {:.2f} Hz".format(
                    x + 1, modal1.wn[x] / (2 * np.pi)),
                key="m8_mode_sel1"
            )
            for m in ["plot_mode_3d", "plot_mode_shape"]:
                if hasattr(modal1, m):
                    try:
                        fig = getattr(modal1, m)(mode=mode_sel1)
                        fig.update_layout(height=320, title="R1 Mode {}".format(
                            mode_sel1 + 1))
                        st.plotly_chart(fig, use_container_width=True,
                                        key="m8_mode_r1")
                        break
                    except Exception:
                        continue

    with col2:
        if modal2 is not None:
            r2   = st.session_state.get("m8_rotor2")
            z1   = int(st.session_state.get("m8_gear_z1", 20))
            z2   = int(st.session_state.get("m8_gear_z2", 30))
            rpm2 = float(st.session_state.get("m8_r1_rpm", 3000)) * z1 / z2
            st.markdown(
                "**Rotor 2 — {:.0f} RPM | {:.2f} kg**".format(
                    rpm2, r2.m if r2 else 0)
            )
            df2 = _make_modal_df(modal2, "R2")
            st.dataframe(df2, use_container_width=True, hide_index=True)

            n_modes2 = min(6, len(modal2.wn))
            mode_sel2 = st.selectbox(
                "Mode R2 a visualiser :",
                list(range(n_modes2)),
                format_func=lambda x: "Mode {} — {:.2f} Hz".format(
                    x + 1, modal2.wn[x] / (2 * np.pi)),
                key="m8_mode_sel2"
            )
            for m in ["plot_mode_3d", "plot_mode_shape"]:
                if hasattr(modal2, m):
                    try:
                        fig = getattr(modal2, m)(mode=mode_sel2)
                        fig.update_layout(height=320, title="R2 Mode {}".format(
                            mode_sel2 + 1))
                        st.plotly_chart(fig, use_container_width=True,
                                        key="m8_mode_r2")
                        break
                    except Exception:
                        continue

    # Comparaison frequences propres
    if modal1 is not None and modal2 is not None:
        st.markdown("---")
        st.markdown("**Comparaison frequences propres R1 vs R2 :**")

        fn1 = modal1.wn[:6] / (2 * np.pi)
        fn2 = modal2.wn[:6] / (2 * np.pi)
        n   = min(len(fn1), len(fn2))

        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            name="Rotor 1",
            x=["Mode {}".format(i + 1) for i in range(n)],
            y=fn1[:n],
            marker_color="#1F5C8B"
        ))
        fig_comp.add_trace(go.Bar(
            name="Rotor 2",
            x=["Mode {}".format(i + 1) for i in range(n)],
            y=fn2[:n],
            marker_color="#C55A11"
        ))

        # Frequence d'engrenement
        freq_eng = float(st.session_state.get("m8_r1_rpm", 3000)) / 60 * \
                   int(st.session_state.get("m8_gear_z1", 20))
        fig_comp.add_hline(
            y=freq_eng,
            line_dash="dot", line_color="#7B1FA2", line_width=2,
            annotation_text="fe = {:.1f} Hz".format(freq_eng),
            annotation_font=dict(color="#7B1FA2")
        )

        fig_comp.update_layout(
            height=360,
            barmode="group",
            title="Frequences propres — Couplage avec fe = {:.1f} Hz".format(
                freq_eng),
            xaxis_title="Mode",
            yaxis_title="Frequence (Hz)",
            plot_bgcolor="white",
            yaxis=dict(showgrid=True, gridcolor="#F0F4FF")
        )
        st.plotly_chart(fig_comp, use_container_width=True,
                        key="m8_modal_comp")
        st.caption(
            "Risque de resonance si une frequence propre coincide "
            "avec la frequence d engrenement fe ou ses harmoniques."
        )


# =============================================================================
# THEORIE MULTIROTOR
# =============================================================================
def _display_theory():
    st.markdown("### Theorie des systemes Multi-Rotors couples par engrenage")

    st.markdown("""
**Equation du mouvement du systeme couple :**

Le systeme MultiRotor est decrit par les matrices globales assemblee
depuis les deux sous-systemes et la matrice de couplage de l engrenage :

```
[M_global] {q_ddot} + ([C_global] + [G_global]) {q_dot}
+ [K_global] {q} = {F(t)}
```

Ou `[K_global]` inclut la rigidite de la ligne d action des dents.

**GearElement — Ligne d action :**

Le couplage est assure par la raideur de la ligne d action,
projetee sur les DDL lateraux des noeuds de contact :

```python
gear = rs.GearElement(
    n=noeud_pignon,
    pitch_diameter=d1,          # Diametre primitif (m)
    pressure_angle=radians(20), # Angle de pression (rad)
    helix_angle=radians(0)      # 0 = engrenage droit
)
```

**Rapport de reduction et vitesses :**
- Rapport i = z1/z2 = d1/d2 = omega2/omega1
- Vitesse R2 = Vitesse R1 / i
- Frequence d engrenement : fe = n1/60 * z1 = n2/60 * z2

**Modes du systeme couple :**

| Type de mode | Description | Source |
|---|---|---|
| Mode lateral R1 | Flexion de l arbre 1 | Gyroscopique |
| Mode lateral R2 | Flexion de l arbre 2 | Gyroscopique |
| Mode torsionnel | Torsion couple des 2 arbres | Engrenage |
| Mode couple lat-tors | Interaction flexion-torsion | Engrenage |

**Excitations caracteristiques :**
- **1X** (synchrone R1) : balourd sur R1
- **1X R2** : balourd sur R2 (= 1X * i)
- **fe = z1 * n1/60** : frequence d engrenement
- **2fe, 3fe** : harmoniques d engrenement
- **Sidelobes** : fe +/- fn (modes lateraux)

**Critere API 684 pour systemes multi-arbres :**
Verifier pour CHAQUE arbre independamment que ses vitesses critiques
sont a +/-15% de sa propre vitesse operationnelle.
    """)

    st.markdown("---")
    st.markdown("### Types d'engrenages et leurs caracteristiques")

    df_types = pd.DataFrame({
        "Type":          ["Droit (spur)", "Helicoidal", "Conique",
                          "Epicycloidal"],
        "Angle helice":  ["0 deg", "15-45 deg", "Variable", "0 deg"],
        "Rapport i max": ["1:10", "1:8", "1:5", "1:12"],
        "Bruit":         ["Eleve", "Faible", "Moyen", "Tres faible"],
        "Force axiale":  ["Nulle", "Presente", "Presente", "Nulle"],
        "Application":   [
            "Boites de vitesses industrielles",
            "Turbines, reducteurs haute vitesse",
            "Transmission a 90 deg",
            "Reducteurs epicycloidaux"
        ]
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
