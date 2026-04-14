# modules/m3_campbell.py — Campbell + UCS Map + API 684 Level 1
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
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
# POINT D'ENTRÉE
# =============================================================================
def render_m3(col_settings, col_graphics):
    rotor = st.session_state.get("rotor")

    with col_settings:
        _render_settings(rotor)

    with col_graphics:
        _render_graphics(rotor)


# =============================================================================
# PANNEAU SETTINGS
# =============================================================================
def _render_settings(rotor):
    st.markdown(
        '<div class="rl-settings-title">📈 Campbell + UCS Map + API 684</div>',
        unsafe_allow_html=True
    )

    if rotor is None:
        st.warning("Aucun rotor — construisez d'abord un modèle dans M1.")
        return

    # ── Onglets de paramétrage ────────────────────────────────────────────
    tab_camp, tab_ucs, tab_api = st.tabs(
        ["📈 Campbell", "🗺️ UCS Map", "📜 API 684"]
    )

    with tab_camp:
        st.markdown(
            '<div class="rl-section-header">▼ Paramètres Campbell</div>',
            unsafe_allow_html=True
        )
        st.number_input(
            "Vitesse opérationnelle (RPM)",
            min_value=100.0, max_value=50000.0,
            value=3000.0, step=100.0,
            key="m3_op_rpm"
        )
        vmax_analyse = st.number_input(
        "Vitesse maximale d'analyse (RPM)",
        min_value=2000,
        max_value=30000,
        value=10000,
        step=500,
        key="m3_vmax"
        )
        resolution_npts = st.number_input(
        "Résolution (points de calcul)",
        min_value=20,
        max_value=150,
        value=60,
        step=10,
        key="m3_npts"
        )
        st.radio(
            "Harmoniques à tracer",
            ["1X seulement", "1X + 2X", "1X + 2X + 3X"],
            index=1, horizontal=True,
            key="m3_harmonics"
        )
        st.button(
            "📈 Calculer le Campbell",
            type="primary",
            key="m3_run_camp",
            use_container_width=True,
            on_click=_run_campbell
        )

    with tab_ucs:
        st.markdown(
            '<div class="rl-section-header">▼ Undamped Critical Speed Map</div>',
            unsafe_allow_html=True
        )
        st.markdown("""
        <div class="rl-card-info">
          <small>La carte UCS montre les vitesses critiques non amorties
          en fonction de la raideur des paliers — outil clé pour le
          dimensionnement des paliers.</small>
        </div>
        """, unsafe_allow_html=True)
        st.slider(
            "Log10(K_min) [N/m]",
            3, 8, 5,
            key="m3_kmin_log"
        )
        st.slider(
            "Log10(K_max) [N/m]",
            6, 12, 9,
            key="m3_kmax_log"
        )
        st.slider(
            "Nombre de points K",
            10, 60, 20,
            key="m3_k_npts"
        )
        st.button(
            "🗺️ Générer la carte UCS",
            type="primary",
            key="m3_run_ucs",
            use_container_width=True,
            on_click=_run_ucs
        )

    with tab_api:
        st.markdown(
            '<div class="rl-section-header">▼ Vérification API 684</div>',
            unsafe_allow_html=True
        )
        st.markdown("""
        <div class="rl-card-info">
          <small>La vérification est automatique après le calcul Campbell.
          Modifiez la vitesse opérationnelle dans l'onglet Campbell,
          puis relancez le calcul.</small>
        </div>
        """, unsafe_allow_html=True)

        camp = st.session_state.get("res_campbell")
        if camp is not None:
            op_rpm = st.session_state.get("m3_op_rpm", 3000.0)
            st.info(
                "Vitesse opérationnelle : **{:.0f} RPM**\n\n"
                "Zone interdite : **{:.0f} – {:.0f} RPM**".format(
                    op_rpm, op_rpm * 0.85, op_rpm * 1.15
                )
            )
            st.button(
                "📜 Lancer la vérification API 684",
                type="primary",
                key="m3_run_api",
                use_container_width=True,
                on_click=_run_api_check
            )
        else:
            st.info("Calculez d'abord le diagramme de Campbell.")


# =============================================================================
# PANNEAU GRAPHICS
# =============================================================================
def _render_graphics(rotor):
    st.markdown(
        '<div class="rl-graphics-title">📈 Campbell Diagram — Results</div>',
        unsafe_allow_html=True
    )

    if rotor is None:
        st.info("Construisez un rotor dans M1 pour accéder aux analyses.")
        return

    tab_camp, tab_ucs, tab_stab, tab_api = st.tabs([
        "📈 Campbell",
        "🗺️ UCS Map",
        "📉 Stabilité",
        "📜 API 684"
    ])

    with tab_camp:
        _display_campbell()

    with tab_ucs:
        _display_ucs()

    with tab_stab:
        _display_stability()

    with tab_api:
        _display_api()


# =============================================================================
# CALCUL CAMPBELL
# =============================================================================
def _run_campbell():
    rotor = st.session_state.get("rotor")
    if rotor is None:
        return

    vmax = float(st.session_state.get("m3_vmax", 10000))
    npts = int(st.session_state.get("m3_npts", 60))

    try:
        speeds = np.linspace(0, vmax * np.pi / 30, npts)
        camp   = rotor.run_campbell(speeds, frequencies=12)
        st.session_state["res_campbell"]  = camp
        st.session_state["m3_camp_vmax"]  = vmax
        st.session_state["m3_camp_npts"]  = npts
        # Invalider l'API check précédent
        st.session_state["df_api"]        = None
        _log("Campbell calculé sur 0–{:.0f} RPM ({} pts)".format(vmax, npts), "ok")
    except Exception as e:
        st.session_state["m3_camp_error"] = str(e)
        _log("Erreur Campbell : {}".format(e), "err")


# =============================================================================
# CALCUL UCS MAP
# =============================================================================
def _run_ucs():
    rotor = st.session_state.get("rotor")
    if rotor is None:
        return

    kmin_log = int(st.session_state.get("m3_kmin_log", 5))
    kmax_log = int(st.session_state.get("m3_kmax_log", 9))
    k_npts   = int(st.session_state.get("m3_k_npts",  20))

    stiffness_range = np.logspace(kmin_log, kmax_log, k_npts)

    try:
        ucs = rotor.run_ucs(
            stiffness_range=stiffness_range,
            num_modes=6
        )
        st.session_state["res_ucs"] = ucs
        _log("UCS Map calculée ({} points K)".format(k_npts), "ok")
    except Exception as e:
        # Fallback manuel si run_ucs() non disponible dans cette version ROSS
        _run_ucs_manual(rotor, stiffness_range)


def _run_ucs_manual(rotor, stiffness_range):
    """Calcul manuel de la carte UCS si run_ucs() absent."""
    try:
        results = []
        for k in stiffness_range:
            # Reconstruction des paliers avec raideur k
            new_bears = []
            for b in rotor.bearing_elements:
                new_bears.append(rs.BearingElement(
                    n=b.n, kxx=k, kyy=k, kxy=0.0, kyx=0.0,
                    cxx=0.0, cyy=0.0
                ))
            r_tmp  = rs.Rotor(
                rotor.shaft_elements,
                rotor.disk_elements,
                new_bears
            )
            modal  = r_tmp.run_modal(speed=0)
            fn_hz  = modal.wn / (2 * np.pi)
            fn_rpm = fn_hz * 60
            results.append(fn_rpm[:6].tolist())

        st.session_state["res_ucs"] = {
            "manual"    : True,
            "stiffness" : stiffness_range,
            "fn_rpm"    : np.array(results),
        }
        _log("UCS Map calculée manuellement", "ok")
    except Exception as e:
        _log("Erreur UCS : {}".format(e), "err")
        st.session_state["m3_ucs_error"] = str(e)


# =============================================================================
# VÉRIFICATION API 684
# =============================================================================
def _run_api_check():
    camp   = st.session_state.get("res_campbell")
    op_rpm = float(st.session_state.get("m3_op_rpm", 3000.0))
    vmax   = float(st.session_state.get("m3_camp_vmax", 10000))
    npts   = int(st.session_state.get("m3_camp_npts", 60))

    if camp is None:
        return

    zl = op_rpm * 0.85
    zh = op_rpm * 1.15

    # Récupération des données Campbell
    speed_rad = np.array(camp.speed_range) \
        if hasattr(camp, 'speed_range') \
        else np.linspace(0, vmax * np.pi / 30, npts)

    if hasattr(camp, 'wd') and camp.wd is not None:
        freqs_mat = camp.wd
    elif hasattr(camp, 'wn') and camp.wn is not None:
        freqs_mat = camp.wn
    else:
        return

    whirl    = getattr(camp, 'whirl', None)
    log_dec  = getattr(camp, 'log_dec', None)
    n_modes  = freqs_mat.shape[1]
    results  = []

    for mode in range(min(10, n_modes)):
        wn_mode = freqs_mat[:, mode]
        diff    = wn_mode - speed_rad

        for i in range(len(diff) - 1):
            if diff[i] * diff[i + 1] <= 0:
                denom = diff[i + 1] - diff[i]
                if abs(denom) < 1e-12:
                    continue
                vc_rad   = speed_rad[i] - diff[i] * (
                    speed_rad[i + 1] - speed_rad[i]) / denom
                vc_rpm   = vc_rad * 30 / np.pi
                fn_exact = vc_rad / (2 * np.pi)

                # Log Dec interpolé
                ld_exact = 0.0
                if log_dec is not None:
                    ld_mode  = log_dec[:, mode]
                    ld_exact = float(np.interp(vc_rad, speed_rad, ld_mode))

                # Direction de précession
                if whirl is not None:
                    mid = len(speed_rad) // 2
                    w_v = str(whirl[mid, mode]).lower()
                    prec = "FW" if "forward" in w_v else "BW"
                else:
                    slope = wn_mode[i + 1] - wn_mode[i]
                    prec  = "FW" if slope > 0 else "BW"

                in_zone = zl <= vc_rpm <= zh
                ld_ok   = ld_exact >= 0.1
                conform = (not in_zone) and ld_ok

                results.append({
                    "Mode":          mode + 1,
                    "Précession":    prec,
                    "fn (Hz)":       "{:.2f}".format(fn_exact),
                    "Vc (RPM)":      "{:.0f}".format(vc_rpm),
                    "Log Dec":       "{:.4f}".format(ld_exact),
                    "Zone interdite": "OUI" if in_zone else "NON",
                    "Log Dec >= 0.1": "OUI" if ld_ok   else "NON",
                    "Conforme API":   "OUI" if conform  else "NON",
                })

    if results:
        df_api = pd.DataFrame(results)
        n_ok   = sum(1 for r in results if r["Conforme API"] == "OUI")
        score  = n_ok / len(results) * 100
        st.session_state["df_api"]    = df_api
        st.session_state["api_params"] = {
            "op_rpm": op_rpm,
            "zl": zl, "zh": zh,
            "score": score
        }
        _log("API 684 : score {:.0f}% ({}/{} conformes)".format(
            score, n_ok, len(results)), "ok")
    else:
        st.session_state["df_api"] = pd.DataFrame()
        _log("API 684 : aucune vitesse critique trouvée dans la plage.", "warn")


# =============================================================================
# AFFICHAGE CAMPBELL
# =============================================================================
def _display_campbell():
    camp = st.session_state.get("res_campbell")

    if "m3_camp_error" in st.session_state:
        st.error("Erreur : {}".format(st.session_state.pop("m3_camp_error")))

    if camp is None:
        st.info(
            "Paramétrez le calcul dans le panneau Settings "
            "puis cliquez sur **Calculer le Campbell**."
        )
        return

    vmax     = float(st.session_state.get("m3_camp_vmax", 10000))
    op_rpm   = float(st.session_state.get("m3_op_rpm",   3000.0))
    zl, zh   = op_rpm * 0.85, op_rpm * 1.15
    harmonic = st.session_state.get("m3_harmonics", "1X + 2X")

    # Récupération des fréquences
    if hasattr(camp, 'speed_range') and camp.speed_range is not None:
        speed_rad = np.array(camp.speed_range)
    else:
        npts      = int(st.session_state.get("m3_camp_npts", 60))
        speed_rad = np.linspace(0, vmax * np.pi / 30, npts)

    speed_rpm = speed_rad * 30 / np.pi

    if hasattr(camp, 'wd') and camp.wd is not None:
        freqs_mat = camp.wd / (2 * np.pi)
    elif hasattr(camp, 'wn') and camp.wn is not None:
        freqs_mat = camp.wn / (2 * np.pi)
    else:
        st.error("Données de fréquences introuvables.")
        return

    whirl   = getattr(camp, 'whirl', None)
    n_modes = freqs_mat.shape[1]

    # ── Construction du graphique Plotly ──────────────────────────────────
    fig = go.Figure()

    colors_fw = ["#1F5C8B","#1565C0","#0288D1","#0097A7","#00796B","#388E3C"]
    colors_bw = ["#C55A11","#E64A19","#F57C00","#FFA000","#C62828","#AD1457"]

    for i in range(min(8, n_modes)):
        fn_i = freqs_mat[:, i]

        # Direction de précession
        if whirl is not None:
            mid   = len(speed_rpm) // 2
            w_val = str(whirl[mid, i]).lower()
            is_fw = "forward" in w_val
        else:
            is_fw = (fn_i[-1] > fn_i[0])

        color     = colors_fw[i % len(colors_fw)] if is_fw \
                    else colors_bw[i % len(colors_bw)]
        dash_type = "solid" if is_fw else "dash"
        label     = "Mode {} ({})".format(i + 1, "FW" if is_fw else "BW")

        fig.add_trace(go.Scatter(
            x=speed_rpm, y=fn_i,
            name=label,
            line=dict(color=color, width=2, dash=dash_type),
            hovertemplate=(
                "Mode {}<br>Ω = %{{x:.0f}} RPM"
                "<br>fn = %{{y:.2f}} Hz<extra></extra>".format(i + 1)
            )
        ))

    # Harmoniques
    max_fn = freqs_mat.max()
    x_line = np.array([0, vmax])

    fig.add_trace(go.Scatter(
        x=x_line, y=x_line / 60,
        name="1X", mode="lines",
        line=dict(color="#E53935", width=1.5, dash="dot"),
    ))
    if "2X" in harmonic:
        fig.add_trace(go.Scatter(
            x=x_line, y=x_line / 30,
            name="2X", mode="lines",
            line=dict(color="#FB8C00", width=1, dash="dot"),
        ))
    if "3X" in harmonic:
        fig.add_trace(go.Scatter(
            x=x_line, y=x_line / 20,
            name="3X", mode="lines",
            line=dict(color="#FDD835", width=1, dash="dot"),
        ))

    # Zone interdite API 684
    fig.add_vrect(
        x0=zl, x1=zh,
        fillcolor="#E53935", opacity=0.08,
        line_width=1, line_color="#E53935",
        annotation_text="Zone interdite API 684",
        annotation_position="top left",
        annotation_font=dict(color="#E53935", size=11)
    )
    fig.add_vline(
        x=op_rpm, line_dash="dashdot",
        line_color="#E53935", line_width=1.5,
        annotation_text=" Nop = {:.0f} RPM".format(op_rpm),
        annotation_font=dict(color="#E53935")
    )

    fig.update_layout(
        height       = 480,
        xaxis_title  = "Vitesse de rotation (RPM)",
        yaxis_title  = "Fréquence (Hz)",
        title        = "Diagramme de Campbell",
        legend       = dict(
            orientation="h", yanchor="bottom",
            y=1.02, xanchor="right", x=1
        ),
        hovermode    = "x unified",
        plot_bgcolor = "white",
        xaxis        = dict(showgrid=True, gridcolor="#F0F4FF"),
        yaxis        = dict(showgrid=True, gridcolor="#F0F4FF"),
    )

    st.plotly_chart(fig, use_container_width=True, key="m3_camp_fig")

    # Capture pour le rapport PDF
    try:
        import kaleido  # noqa
        st.session_state["img_campbell"] = fig.to_image(
            format="png", width=700, height=450)
    except ImportError:
        pass

    # Tableau des vitesses critiques
    _display_critical_speeds(camp, speed_rad, speed_rpm, whirl, freqs_mat)


def _display_critical_speeds(camp, speed_rad, speed_rpm, whirl, freqs_mat):
    """Tableau des intersections 1X."""
    n_modes   = freqs_mat.shape[1]
    crits     = []

    for mode in range(min(10, n_modes)):
        fn_mode = freqs_mat[:, mode]
        diff    = fn_mode - speed_rpm / 60  # fn en Hz, speed/60 aussi

        for i in range(len(diff) - 1):
            if diff[i] * diff[i + 1] <= 0:
                denom = diff[i + 1] - diff[i]
                if abs(denom) < 1e-12:
                    continue
                vc_rpm = speed_rpm[i] - diff[i] * (
                    speed_rpm[i + 1] - speed_rpm[i]) / denom
                fn_vc  = float(np.interp(vc_rpm, speed_rpm, fn_mode))

                if whirl is not None:
                    mid   = len(speed_rpm) // 2
                    w_val = str(whirl[mid, mode]).lower()
                    prec  = "FW" if "forward" in w_val else "BW"
                else:
                    prec  = "FW" if fn_mode[-1] > fn_mode[0] else "BW"

                crits.append({
                    "Mode":     mode + 1,
                    "Précession": prec,
                    "fn (Hz)":  "{:.2f}".format(fn_vc),
                    "Vc (RPM)": "{:.0f}".format(vc_rpm),
                })

    if crits:
        df_vc = pd.DataFrame(crits)
        df_vc = df_vc.drop_duplicates(subset=["Vc (RPM)"])
        st.markdown("**Vitesses critiques (intersections 1X) :**")
        st.dataframe(df_vc, use_container_width=True, hide_index=True)
        st.session_state["df_campbell"] = df_vc
    else:
        st.info("Aucune intersection 1X détectée dans cette plage.")


# =============================================================================
# AFFICHAGE UCS MAP
# =============================================================================
def _display_ucs():
    ucs = st.session_state.get("res_ucs")

    if "m3_ucs_error" in st.session_state:
        st.error("Erreur UCS : {}".format(st.session_state.pop("m3_ucs_error")))

    if ucs is None:
        st.info(
            "Paramétrez la carte UCS dans le panneau Settings "
            "puis cliquez sur **Générer la carte UCS**."
        )
        return

    fig = go.Figure()
    colors = ["#1F5C8B","#C55A11","#22863A","#7B1FA2","#C00000","#00796B"]

    # Objet natif ROSS ou calcul manuel
    if isinstance(ucs, dict) and ucs.get("manual"):
        k_vals = ucs["stiffness"]
        fn_mat = ucs["fn_rpm"]
        n_modes = fn_mat.shape[1]
        for i in range(n_modes):
            fig.add_trace(go.Scatter(
                x=k_vals, y=fn_mat[:, i],
                name="Mode {}".format(i + 1),
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate=(
                    "K = %{x:.2e} N/m<br>"
                    "Vc = %{y:.0f} RPM<extra></extra>"
                )
            ))
    else:
        # Objet natif ROSS
        try:
            st.plotly_chart(ucs.plot(), use_container_width=True,
                            key="m3_ucs_native")
            return
        except Exception:
            st.warning("Affichage natif UCS non disponible.")
            return

    # Ligne de vitesse opérationnelle
    op_rpm = float(st.session_state.get("m3_op_rpm", 3000.0))
    fig.add_hline(
        y=op_rpm, line_dash="dash", line_color="#E53935",
        annotation_text=" Nop = {:.0f} RPM".format(op_rpm),
        annotation_font=dict(color="#E53935")
    )
    fig.add_hrect(
        y0=op_rpm * 0.85, y1=op_rpm * 1.15,
        fillcolor="#E53935", opacity=0.07,
        line_width=0
    )

    fig.update_layout(
        height       = 460,
        xaxis_title  = "Raideur des paliers K (N/m)",
        yaxis_title  = "Vitesse critique (RPM)",
        title        = "Undamped Critical Speed Map",
        xaxis_type   = "log",
        plot_bgcolor = "white",
        xaxis        = dict(showgrid=True, gridcolor="#F0F4FF"),
        yaxis        = dict(showgrid=True, gridcolor="#F0F4FF"),
    )

    st.plotly_chart(fig, use_container_width=True, key="m3_ucs_fig")
    st.caption(
        "La carte UCS permet de choisir la raideur des paliers pour "
        "que les vitesses critiques soient hors de la plage opérationnelle."
    )


# =============================================================================
# AFFICHAGE STABILITÉ (Log Dec vs vitesse)
# =============================================================================
def _display_stability():
    camp = st.session_state.get("res_campbell")

    if camp is None:
        st.info("Calculez d'abord le Campbell.")
        return

    log_dec = getattr(camp, 'log_dec', None)
    if log_dec is None:
        st.warning("Log Décrément non disponible dans cette version de ROSS.")
        return

    vmax     = float(st.session_state.get("m3_camp_vmax", 10000))
    npts     = int(st.session_state.get("m3_camp_npts",  60))

    if hasattr(camp, 'speed_range') and camp.speed_range is not None:
        speed_rad = np.array(camp.speed_range)
    else:
        speed_rad = np.linspace(0, vmax * np.pi / 30, npts)

    speed_rpm = speed_rad * 30 / np.pi
    whirl     = getattr(camp, 'whirl', None)

    fig    = go.Figure()
    colors = ["#1F5C8B","#C55A11","#22863A","#7B1FA2","#C00000","#00796B",
              "#E64A19","#0288D1","#00897B","#6A1B9A"]

    n_modes = log_dec.shape[1]
    for i in range(min(10, n_modes)):
        if whirl is not None:
            mid   = len(speed_rpm) // 2
            w_val = str(whirl[mid, i]).lower()
            prec  = "FW" if "forward" in w_val else "BW"
        else:
            if hasattr(camp, 'wd') and camp.wd is not None:
                slope = camp.wd[-1, i] - camp.wd[0, i]
            else:
                slope = 1
            prec  = "FW" if slope > 0 else "BW"

        fig.add_trace(go.Scatter(
            x=speed_rpm,
            y=log_dec[:, i],
            name="Mode {} ({})".format(i + 1, prec),
            line=dict(color=colors[i % len(colors)], width=2),
            hovertemplate=(
                "Mode {}<br>Ω = %{{x:.0f}} RPM"
                "<br>δ = %{{y:.4f}}<extra></extra>".format(i + 1)
            )
        ))

    # Seuils
    fig.add_hline(
        y=0, line_dash="dash", line_color="#E53935", line_width=2,
        annotation_text=" Seuil instabilité (δ = 0)",
        annotation_font=dict(color="#E53935")
    )
    fig.add_hline(
        y=0.1, line_dash="dot", line_color="#FB8C00", line_width=1.5,
        annotation_text=" Seuil API 684 (δ = 0.1)",
        annotation_font=dict(color="#FB8C00")
    )

    # Zone opérationnelle
    op_rpm = float(st.session_state.get("m3_op_rpm", 3000.0))
    fig.add_vrect(
        x0=op_rpm * 0.85, x1=op_rpm * 1.15,
        fillcolor="#E53935", opacity=0.06, line_width=0
    )

    fig.update_layout(
        height       = 460,
        xaxis_title  = "Vitesse de rotation (RPM)",
        yaxis_title  = "Log Décrément (δ)",
        title        = "Carte de stabilité — Log Dec vs Vitesse",
        legend       = dict(
            orientation="h", yanchor="bottom",
            y=1.02, xanchor="right", x=1
        ),
        plot_bgcolor = "white",
        xaxis        = dict(showgrid=True, gridcolor="#F0F4FF"),
        yaxis        = dict(showgrid=True, gridcolor="#F0F4FF"),
    )

    st.plotly_chart(fig, use_container_width=True, key="m3_stab_fig")


# =============================================================================
# AFFICHAGE API 684
# =============================================================================
def _display_api():
    df_api     = st.session_state.get("df_api")
    api_params = st.session_state.get("api_params")

    if df_api is None:
        st.info(
            "Calculez le Campbell puis lancez la "
            "**vérification API 684** depuis le panneau Settings."
        )
        return

    if df_api.empty:
        st.success(
            "Aucune vitesse critique trouvée dans la plage analysée — "
            "pas d'intersection 1X."
        )
        return

    # Métriques
    if api_params:
        op_rpm = api_params["op_rpm"]
        zl     = api_params["zl"]
        zh     = api_params["zh"]
        score  = api_params["score"]

        c1, c2, c3 = st.columns(3)
        c1.markdown("""
        <div class="rl-metric-card">
          <div class="rl-metric-label">Vitesse opérationnelle</div>
          <div class="rl-metric-value">{:.0f}</div>
          <div class="rl-metric-unit">RPM</div>
        </div>""".format(op_rpm), unsafe_allow_html=True)
        c2.markdown("""
        <div class="rl-metric-card">
          <div class="rl-metric-label">Zone interdite</div>
          <div class="rl-metric-value" style="font-size:0.95em;">
            {:.0f} – {:.0f}
          </div>
          <div class="rl-metric-unit">RPM</div>
        </div>""".format(zl, zh), unsafe_allow_html=True)

        color_score = "#22863A" if score >= 100 \
                      else "#C55A11" if score >= 67 \
                      else "#C00000"
        c3.markdown("""
        <div class="rl-metric-card">
          <div class="rl-metric-label">Score API 684</div>
          <div class="rl-metric-value" style="color:{};">{:.0f}%</div>
        </div>""".format(color_score, score), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

    # Tableau de conformité avec coloration
    st.markdown("**Résultats détaillés :**")
    st.dataframe(df_api, use_container_width=True, hide_index=True)

    # Diagnostic
    n_nc = (df_api["Conforme API"] == "NON").sum() \
           if "Conforme API" in df_api.columns else 0

    if n_nc == 0:
        st.markdown("""
        <div class="rl-card-ok">
          <strong>Rotor conforme à la norme API 684.</strong><br>
          Toutes les vitesses critiques respectent la marge de ±15 %
          et le Log Décrément est suffisant.
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="rl-card-danger">
          <strong>{} vitesse(s) critique(s) non conforme(s).</strong><br>
          Augmentez la raideur ou l'amortissement des paliers,
          ou modifiez la géométrie de l'arbre.
        </div>""".format(n_nc), unsafe_allow_html=True)

    # Export rapport HTML
    st.download_button(
        label    = "📄 Exporter rapport API 684 (HTML)",
        data     = _generate_api_html(df_api, api_params).encode(),
        file_name= "rapport_api684.html",
        mime     = "text/html",
        key      = "m3_api_export"
    )


# =============================================================================
# EXPORT HTML API 684
# =============================================================================
def _generate_api_html(df_api, api_params):
    rows = ""
    for _, r in df_api.iterrows():
        color = "#E8F5E9" if r.get("Conforme API") == "OUI" else "#FFEBEE"
        rows += "<tr style='background:{};'>".format(color)
        for v in r:
            rows += "<td>{}</td>".format(v)
        rows += "</tr>"

    params_html = ""
    if api_params:
        params_html = """
        <p><b>Vitesse opérationnelle :</b> {:.0f} RPM</p>
        <p><b>Zone interdite :</b> {:.0f} – {:.0f} RPM</p>
        <p><b>Score de conformité :</b> {:.0f}%</p>
        """.format(
            api_params["op_rpm"],
            api_params["zl"], api_params["zh"],
            api_params["score"]
        )

    return """<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Rapport API 684 — RotorLab Suite 2.0</title>
<style>
  body {{ font-family:Arial,sans-serif; max-width:960px; margin:40px auto; }}
  h1   {{ color:#1F5C8B; border-bottom:3px solid #1F5C8B; padding-bottom:8px; }}
  h2   {{ color:#C55A11; }}
  table {{ width:100%; border-collapse:collapse; margin:12px 0; }}
  th  {{ background:#1F5C8B; color:#fff; padding:8px; text-align:center; }}
  td  {{ padding:6px 10px; border:1px solid #ddd; text-align:center; }}
  .footer {{ color:#999; font-size:.85em; margin-top:40px; }}
</style></head><body>
<h1>Rapport de conformité API 684</h1>
<h2>Paramètres</h2>
{params}
<h2>Résultats</h2>
<table>
  <tr>{headers}</tr>
  {rows}
</table>
<div class="footer">RotorLab Suite 2.0 — Pr. Najeh Ben Guedria — ISTLS</div>
</body></html>""".format(
        params  = params_html,
        headers = "".join(
            "<th>{}</th>".format(c) for c in df_api.columns),
        rows    = rows
    )


# =============================================================================
# HELPER LOG
# =============================================================================
def _log(message, level="info"):
    try:
        from app import add_log
        add_log(message, level)
    except Exception:
        pass
