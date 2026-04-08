# modules/m5_bearing.py — Paliers Hydrodynamiques (Fluid Film Bearings)
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
# Couvre : BearingFluidFilm, coefficients HD, carte de stabilite,
#          influence Kxy, comparaison paliers rigides vs HD
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
def render_m5(col_settings, col_graphics):
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
        '<div class="rl-settings-title">Fluid Film Bearings [NEW]</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<span class="rl-badge rl-badge-new">NEW v2.0</span>',
        unsafe_allow_html=True
    )

    if rotor is None:
        st.warning("Aucun rotor — construisez d'abord un modele dans M1.")
        return

    n_nodes = len(rotor.nodes) - 1

    tab_hd, tab_stab, tab_comp = st.tabs([
        "Paliers HD",
        "Stabilite Kxy",
        "Comparaison"
    ])

    # ── ONGLET PALIERS HD ─────────────────────────────────────────────────
    with tab_hd:
        st.markdown(
            '<div class="rl-section-header">Configuration paliers HD</div>',
            unsafe_allow_html=True
        )
        st.caption(
            "Paliers a film mince hydrodynamique — "
            "coefficients variables avec la vitesse."
        )

        n_bears = st.slider(
            "Nombre de paliers HD", 1, 4, 2, key="m5_n_bears"
        )

        bear_configs = []
        for i in range(n_bears):
            st.markdown("**Palier HD {} :**".format(i + 1))
            c1, c2 = st.columns(2)
            with c1:
                node = st.slider(
                    "Noeud", 0, n_nodes,
                    0 if i == 0 else n_nodes,
                    key="m5_bn_{}".format(i)
                )
            with c2:
                bear_type = st.selectbox(
                    "Type",
                    [
                        "Palier lisse (cylindrique)",
                        "Palier a lobes (2 lobes)",
                        "Palier a lobes (3 lobes)",
                        "Palier tilting-pad (4 patins)",
                        "Palier tilting-pad (5 patins)",
                        "Personnalise"
                    ],
                    key="m5_bt_{}".format(i)
                )

            # Presets selon le type
            presets = _get_bearing_preset(bear_type)

            c1, c2, c3 = st.columns(3)
            with c1:
                kxx = st.number_input(
                    "Kxx (N/m)", 1e4, 1e10,
                    float(presets["kxx"]),
                    format="%.2e",
                    key="m5_kxx_{}".format(i)
                )
                cxx = st.number_input(
                    "Cxx (N.s/m)", 0.0, 1e6,
                    float(presets["cxx"]),
                    format="%.1f",
                    key="m5_cxx_{}".format(i)
                )
            with c2:
                kyy = st.number_input(
                    "Kyy (N/m)", 1e4, 1e10,
                    float(presets["kyy"]),
                    format="%.2e",
                    key="m5_kyy_{}".format(i)
                )
                cyy = st.number_input(
                    "Cyy (N.s/m)", 0.0, 1e6,
                    float(presets["cyy"]),
                    format="%.1f",
                    key="m5_cyy_{}".format(i)
                )
            with c3:
                kxy = st.number_input(
                    "Kxy (N/m)", -1e9, 1e9,
                    float(presets["kxy"]),
                    format="%.2e",
                    key="m5_kxy_{}".format(i),
                    help="Kxy > 0 = destabilisant (oil whirl)"
                )
                cxy = st.number_input(
                    "Cxy (N.s/m)", -1e5, 1e5,
                    float(presets["cxy"]),
                    format="%.1f",
                    key="m5_cxy_{}".format(i)
                )

            bear_configs.append({
                "node": node,
                "type": bear_type,
                "kxx": kxx, "kyy": kyy,
                "kxy": kxy, "kyx": -kxy,
                "cxx": cxx, "cyy": cyy,
                "cxy": cxy, "cyx": cxy,
            })

        st.session_state["m5_bear_configs"] = bear_configs

        st.markdown(
            '<div class="rl-section-header">Plage de vitesse</div>',
            unsafe_allow_html=True
        )
        st.slider(
            "Vitesse max (RPM)", 1000, 30000, 10000,
            key="m5_vmax"
        )
        st.slider(
            "Resolution (points)", 10, 80, 30,
            key="m5_npts"
        )

        st.button(
            "Calculer Campbell HD",
            type="primary",
            key="m5_run_hd",
            use_container_width=True,
            on_click=_run_hd_campbell
        )

    # ── ONGLET STABILITE Kxy ──────────────────────────────────────────────
    with tab_stab:
        st.markdown(
            '<div class="rl-section-header">Analyse de stabilite</div>',
            unsafe_allow_html=True
        )
        st.markdown("""
        <div class="rl-card-info">
          <small>Cette analyse calcule le Log Decrements pour
          differentes valeurs de Kxy (raideur croisee) et montre
          l'effet destabilisant des forces fluides hydrodynamiques.</small>
        </div>
        """, unsafe_allow_html=True)

        st.number_input(
            "Vitesse d'analyse (RPM)",
            100.0, 30000.0, 3000.0,
            key="m5_stab_rpm"
        )
        c1, c2 = st.columns(2)
        with c1:
            st.number_input(
                "Kxy min (N/m)",
                0.0, 1e9, 0.0,
                format="%.2e",
                key="m5_kxy_min"
            )
        with c2:
            st.number_input(
                "Kxy max (N/m)",
                1e4, 1e10, 1e7,
                format="%.2e",
                key="m5_kxy_max"
            )
        st.slider(
            "Nombre de points Kxy", 5, 30, 15,
            key="m5_kxy_npts"
        )

        st.button(
            "Analyser la stabilite vs Kxy",
            type="primary",
            key="m5_run_stab",
            use_container_width=True,
            on_click=_run_stability_analysis
        )

    # ── ONGLET COMPARAISON ────────────────────────────────────────────────
    with tab_comp:
        st.markdown(
            '<div class="rl-section-header">Comparaison paliers</div>',
            unsafe_allow_html=True
        )
        st.markdown("""
        <div class="rl-card-info">
          <small>Compare les diagrammes de Campbell et les vitesses
          critiques entre les paliers actuels (M1) et les paliers
          HD configures ci-dessus.</small>
        </div>
        """, unsafe_allow_html=True)

        st.slider(
            "Vitesse max comparaison (RPM)",
            1000, 30000, 10000,
            key="m5_comp_vmax"
        )
        st.slider(
            "Resolution comparaison",
            10, 60, 25,
            key="m5_comp_npts"
        )

        st.button(
            "Lancer la comparaison",
            type="primary",
            key="m5_run_comp",
            use_container_width=True,
            on_click=_run_comparison
        )


# =============================================================================
# PANNEAU GRAPHICS
# =============================================================================
def _render_graphics(rotor):
    st.markdown(
        '<div class="rl-graphics-title">'
        'Fluid Film Bearings — Results'
        '</div>',
        unsafe_allow_html=True
    )

    if rotor is None:
        st.info("Construisez un rotor dans M1 pour acceder aux analyses.")
        return

    tab_camp, tab_stab, tab_coeff, tab_comp = st.tabs([
        "Campbell HD",
        "Stabilite vs Kxy",
        "Coefficients HD",
        "Comparaison"
    ])

    with tab_camp:
        _display_hd_campbell()

    with tab_stab:
        _display_stability()

    with tab_coeff:
        _display_coefficients()

    with tab_comp:
        _display_comparison()


# =============================================================================
# PRESETS PALIERS
# =============================================================================
def _get_bearing_preset(bear_type):
    presets = {
        "Palier lisse (cylindrique)": {
            "kxx": 1e7, "kyy": 5e6,
            "kxy": 2e6, "cxx": 2000.0, "cyy": 2000.0, "cxy": 500.0
        },
        "Palier a lobes (2 lobes)": {
            "kxx": 8e6, "kyy": 4e6,
            "kxy": 8e5, "cxx": 1500.0, "cyy": 1500.0, "cxy": 200.0
        },
        "Palier a lobes (3 lobes)": {
            "kxx": 6e6, "kyy": 3e6,
            "kxy": 5e5, "cxx": 1200.0, "cyy": 1200.0, "cxy": 100.0
        },
        "Palier tilting-pad (4 patins)": {
            "kxx": 5e6, "kyy": 5e6,
            "kxy": 0.0, "cxx": 3000.0, "cyy": 3000.0, "cxy": 0.0
        },
        "Palier tilting-pad (5 patins)": {
            "kxx": 5e6, "kyy": 5e6,
            "kxy": 0.0, "cxx": 3500.0, "cyy": 3500.0, "cxy": 0.0
        },
        "Personnalise": {
            "kxx": 1e7, "kyy": 1e7,
            "kxy": 0.0, "cxx": 500.0, "cyy": 500.0, "cxy": 0.0
        },
    }
    return presets.get(bear_type, presets["Personnalise"])


# =============================================================================
# CONSTRUCTION ROTOR HD
# =============================================================================
def _build_hd_rotor():
    """Reconstruit le rotor avec les paliers HD configures."""
    rotor = st.session_state.get("rotor")
    if rotor is None or not ROSS_OK:
        return None

    bear_configs = st.session_state.get("m5_bear_configs", [])
    if not bear_configs:
        return None

    try:
        new_bears = []
        for cfg in bear_configs:
            new_bears.append(rs.BearingElement(
                n   = int(cfg["node"]),
                kxx = float(cfg["kxx"]),
                kyy = float(cfg["kyy"]),
                kxy = float(cfg["kxy"]),
                kyx = float(cfg["kyx"]),
                cxx = float(cfg["cxx"]),
                cyy = float(cfg["cyy"]),
                cxy = float(cfg.get("cxy", 0.0)),
                cyx = float(cfg.get("cyx", 0.0)),
            ))

        rotor_hd = rs.Rotor(
            shaft_elements   = rotor.shaft_elements,
            disk_elements    = rotor.disk_elements,
            bearing_elements = new_bears
        )
        return rotor_hd
    except Exception as e:
        _log("Erreur construction rotor HD : {}".format(e), "err")
        return None


# =============================================================================
# CALCUL CAMPBELL HD
# =============================================================================
def _run_hd_campbell():
    rotor_hd = _build_hd_rotor()
    if rotor_hd is None:
        st.session_state["m5_hd_error"] = \
            "Impossible de construire le rotor HD. Verifiez les noeuds."
        return

    vmax = float(st.session_state.get("m5_vmax", 10000))
    npts = int(st.session_state.get("m5_npts",   30))

    try:
        speeds = np.linspace(0, vmax * np.pi / 30, npts)
        camp   = rotor_hd.run_campbell(speeds, frequencies=12)
        st.session_state["res_m5_camp"]  = camp
        st.session_state["m5_camp_vmax"] = vmax
        st.session_state["m5_hd_error"]  = None
        _log("Campbell HD calcule ({} pts, vmax={:.0f} RPM)".format(
            npts, vmax), "ok")
    except Exception as e:
        st.session_state["m5_hd_error"] = str(e)
        _log("Erreur Campbell HD : {}".format(e), "err")


# =============================================================================
# ANALYSE STABILITE vs Kxy
# =============================================================================
def _run_stability_analysis():
    rotor = st.session_state.get("rotor")
    if rotor is None or not ROSS_OK:
        return

    speed_rpm = float(st.session_state.get("m5_stab_rpm",   3000.0))
    kxy_min   = float(st.session_state.get("m5_kxy_min",    0.0))
    kxy_max   = float(st.session_state.get("m5_kxy_max",    1e7))
    n_kxy     = int(st.session_state.get("m5_kxy_npts",     15))
    speed_rad = speed_rpm * np.pi / 30

    kxy_vals  = np.linspace(kxy_min, kxy_max, n_kxy)
    bear_cfgs = st.session_state.get("m5_bear_configs", [])

    if not bear_cfgs:
        _log("Aucun palier HD configure", "warn")
        return

    results = []

    for kxy in kxy_vals:
        try:
            new_bears = []
            for cfg in bear_cfgs:
                new_bears.append(rs.BearingElement(
                    n   = int(cfg["node"]),
                    kxx = float(cfg["kxx"]),
                    kyy = float(cfg["kyy"]),
                    kxy = float(kxy),
                    kyx = float(-kxy),
                    cxx = float(cfg["cxx"]),
                    cyy = float(cfg["cyy"]),
                ))

            r_tmp = rs.Rotor(
                shaft_elements   = rotor.shaft_elements,
                disk_elements    = rotor.disk_elements,
                bearing_elements = new_bears
            )
            modal = r_tmp.run_modal(speed=speed_rad)
            ld    = getattr(modal, 'log_dec', np.zeros(len(modal.wn)))
            fn    = modal.wn / (2 * np.pi)
            n_modes = min(6, len(fn))

            row = {"Kxy (N/m)": kxy}
            for i in range(n_modes):
                row["Mode {} fn (Hz)".format(i + 1)]   = round(float(fn[i]), 3)
                row["Mode {} LogDec".format(i + 1)]     = round(float(ld[i]), 4)
                row["Mode {} Statut".format(i + 1)]     = (
                    "INSTABLE" if ld[i] <= 0 else
                    "Marginal" if ld[i] < 0.1 else "OK"
                )
            results.append(row)

        except Exception as e:
            _log("Erreur Kxy={:.2e} : {}".format(kxy, e), "warn")
            continue

    if results:
        st.session_state["m5_stab_results"] = pd.DataFrame(results)
        st.session_state["m5_stab_rpm_val"] = speed_rpm
        _log("Analyse stabilite terminee ({} points Kxy)".format(
            len(results)), "ok")
    else:
        _log("Aucun resultat de stabilite", "err")


# =============================================================================
# COMPARAISON PALIERS RIGIDES vs HD
# =============================================================================
def _run_comparison():
    rotor    = st.session_state.get("rotor")
    rotor_hd = _build_hd_rotor()

    if rotor is None or rotor_hd is None or not ROSS_OK:
        _log("Comparaison impossible : rotor ou paliers HD manquants", "err")
        return

    vmax = float(st.session_state.get("m5_comp_vmax", 10000))
    npts = int(st.session_state.get("m5_comp_npts",   25))

    try:
        speeds = np.linspace(0, vmax * np.pi / 30, npts)

        camp_orig = rotor.run_campbell(speeds, frequencies=8)
        camp_hd   = rotor_hd.run_campbell(speeds, frequencies=8)

        st.session_state["m5_comp_orig"] = camp_orig
        st.session_state["m5_comp_hd"]   = camp_hd
        st.session_state["m5_comp_vmax"] = vmax
        _log("Comparaison paliers calculee", "ok")
    except Exception as e:
        _log("Erreur comparaison : {}".format(e), "err")
        st.session_state["m5_comp_error"] = str(e)


# =============================================================================
# AFFICHAGE CAMPBELL HD
# =============================================================================
def _display_hd_campbell():
    if st.session_state.get("m5_hd_error"):
        st.error("Erreur : {}".format(st.session_state["m5_hd_error"]))

    camp = st.session_state.get("res_m5_camp")
    if camp is None:
        st.info(
            "Configurez les paliers HD et lancez le calcul "
            "dans le panneau Settings."
        )
        return

    vmax    = float(st.session_state.get("m5_camp_vmax", 10000))
    op_rpm  = float(st.session_state.get("m3_op_rpm",    3000.0))
    zl, zh  = op_rpm * 0.85, op_rpm * 1.15

    # Recuperation des donnees
    if hasattr(camp, 'speed_range') and camp.speed_range is not None:
        speed_rad = np.array(camp.speed_range)
    else:
        npts      = int(st.session_state.get("m5_npts", 30))
        speed_rad = np.linspace(0, vmax * np.pi / 30, npts)

    speed_rpm = speed_rad * 30 / np.pi

    if hasattr(camp, 'wd') and camp.wd is not None:
        freqs_mat = camp.wd / (2 * np.pi)
    elif hasattr(camp, 'wn') and camp.wn is not None:
        freqs_mat = camp.wn / (2 * np.pi)
    else:
        st.error("Donnees de frequences introuvables.")
        return

    whirl   = getattr(camp, 'whirl', None)
    n_modes = freqs_mat.shape[1]

    fig = go.Figure()
    colors_fw = ["#1F5C8B", "#0288D1", "#00796B", "#388E3C"]
    colors_bw = ["#C55A11", "#E64A19", "#C62828", "#AD1457"]

    for i in range(min(8, n_modes)):
        fn_i  = freqs_mat[:, i]
        if whirl is not None:
            mid   = len(speed_rpm) // 2
            w_val = str(whirl[mid, i]).lower()
            is_fw = "forward" in w_val
        else:
            is_fw = fn_i[-1] > fn_i[0]

        color = colors_fw[i % len(colors_fw)] if is_fw \
                else colors_bw[i % len(colors_bw)]
        label = "Mode {} ({})".format(i + 1, "FW" if is_fw else "BW")

        fig.add_trace(go.Scatter(
            x=speed_rpm, y=fn_i,
            name=label,
            line=dict(
                color=color, width=2,
                dash="solid" if is_fw else "dash"
            )
        ))

    # Harmoniques
    x_line = np.array([0, vmax])
    fig.add_trace(go.Scatter(
        x=x_line, y=x_line / 60,
        name="1X", mode="lines",
        line=dict(color="#E53935", width=1.5, dash="dot")
    ))
    fig.add_trace(go.Scatter(
        x=x_line, y=x_line / 30,
        name="2X", mode="lines",
        line=dict(color="#FB8C00", width=1, dash="dot")
    ))

    # Zone API 684
    fig.add_vrect(
        x0=zl, x1=zh,
        fillcolor="#E53935", opacity=0.08,
        line_width=1, line_color="#E53935",
        annotation_text="Zone interdite API 684",
        annotation_font=dict(color="#E53935", size=10)
    )
    fig.add_vline(
        x=op_rpm, line_dash="dashdot",
        line_color="#E53935", line_width=1.5,
        annotation_text=" Nop = {:.0f} RPM".format(op_rpm)
    )

    fig.update_layout(
        height=460,
        title="Campbell — Paliers Hydrodynamiques HD",
        xaxis_title="Vitesse (RPM)",
        yaxis_title="Frequence (Hz)",
        plot_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#F0F4FF"),
        yaxis=dict(showgrid=True, gridcolor="#F0F4FF"),
        legend=dict(
            orientation="h", yanchor="bottom",
            y=1.02, xanchor="right", x=1
        )
    )

    st.plotly_chart(fig, use_container_width=True, key="m5_camp_fig")

    # Tableau Log Dec a la vitesse operationnelle
    log_dec = getattr(camp, 'log_dec', None)
    if log_dec is not None:
        st.markdown("**Log Decrements a la vitesse operationnelle :**")
        idx_op = int(np.argmin(np.abs(speed_rpm - op_rpm)))
        rows   = []
        for i in range(min(8, n_modes)):
            ld = float(log_dec[idx_op, i])
            fn = float(freqs_mat[idx_op, i])
            if whirl is not None:
                mid   = len(speed_rpm) // 2
                w_val = str(whirl[mid, i]).lower()
                prec  = "FW" if "forward" in w_val else "BW"
            else:
                prec  = "FW" if freqs_mat[-1, i] > freqs_mat[0, i] else "BW"

            rows.append({
                "Mode":       i + 1,
                "Precession": prec,
                "fn (Hz)":    "{:.2f}".format(fn),
                "Log Dec":    "{:.4f}".format(ld),
                "Statut":     (
                    "INSTABLE" if ld <= 0 else
                    "Marginal" if ld < 0.1 else "Conforme API"
                )
            })
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )


# =============================================================================
# AFFICHAGE STABILITE vs Kxy
# =============================================================================
def _display_stability():
    df = st.session_state.get("m5_stab_results")

    if df is None:
        st.info(
            "Configurez l'analyse de stabilite et lancez le calcul "
            "dans le panneau Settings."
        )
        return

    speed_rpm = float(st.session_state.get("m5_stab_rpm_val", 3000.0))
    st.markdown(
        "**Analyse a {:.0f} RPM :**".format(speed_rpm)
    )

    # Extraction des colonnes Log Dec par mode
    kxy_col    = df["Kxy (N/m)"].values
    logdec_cols = [c for c in df.columns if "LogDec" in c]

    if not logdec_cols:
        st.warning("Aucune donnee de Log Dec disponible.")
        return

    fig = go.Figure()
    colors = ["#1F5C8B", "#C55A11", "#22863A",
              "#7B1FA2", "#C00000", "#00796B"]

    for i, col in enumerate(logdec_cols):
        mode_num = col.split(" ")[1]
        fig.add_trace(go.Scatter(
            x=kxy_col,
            y=df[col].values,
            name="Mode {}".format(mode_num),
            line=dict(color=colors[i % len(colors)], width=2),
            hovertemplate=(
                "Kxy = %{x:.2e} N/m<br>"
                f"Log Dec = %{{y:.4f}}<extra>Mode {mode_num}</extra>"
            )
        ))

    # Seuils
    fig.add_hline(
        y=0, line_dash="dash",
        line_color="#E53935", line_width=2,
        annotation_text=" Seuil instabilite (delta=0)"
    )
    fig.add_hline(
        y=0.1, line_dash="dot",
        line_color="#FB8C00", line_width=1.5,
        annotation_text=" Seuil API 684 (delta=0.1)"
    )

    # Seuil d'instabilite : trouver Kxy critique
    for col in logdec_cols:
        ld_vals = df[col].values
        for j in range(len(ld_vals) - 1):
            if ld_vals[j] > 0 >= ld_vals[j + 1]:
                kxy_crit = float(kxy_col[j])
                fig.add_vline(
                    x=kxy_crit,
                    line_dash="dot",
                    line_color="#E53935",
                    opacity=0.5,
                    annotation_text="Kxy crit={:.2e}".format(kxy_crit),
                    annotation_font=dict(color="#E53935", size=9)
                )
                break

    fig.update_layout(
        height=460,
        title="Log Dec vs Kxy (raideur croisee) @ {:.0f} RPM".format(
            speed_rpm),
        xaxis_title="Kxy (N/m)",
        yaxis_title="Log Decrement",
        plot_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#F0F4FF"),
        yaxis=dict(showgrid=True, gridcolor="#F0F4FF"),
        legend=dict(
            orientation="h", yanchor="bottom",
            y=1.02, xanchor="right", x=1
        )
    )

    st.plotly_chart(fig, use_container_width=True, key="m5_stab_fig")

    # Tableau des Kxy critiques
    st.markdown("**Tableau de stabilite complet :**")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Export
    st.download_button(
        "Export CSV stabilite",
        data=df.to_csv(index=False).encode(),
        file_name="stabilite_kxy.csv",
        mime="text/csv",
        key="m5_stab_csv"
    )


# =============================================================================
# AFFICHAGE COEFFICIENTS HD (tableau educatif)
# =============================================================================
def _display_coefficients():
    st.markdown("### Coefficients des paliers hydrodynamiques")
    st.markdown("""
    <div class="rl-card-info">
    Les paliers hydrodynamiques sont caracterises par 8 coefficients
    lineaires : 4 de raideur [K] et 4 d'amortissement [C].
    </div>
    """, unsafe_allow_html=True)

    # Matrice des coefficients
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["Matrice de raideur [K]", "Matrice d'amortissement [C]"]
    )

    bear_cfgs = st.session_state.get("m5_bear_configs", [])
    if not bear_cfgs:
        st.info("Configurez d'abord les paliers HD dans le panneau Settings.")
        return

    cfg = bear_cfgs[0]

    # Heatmap raideur
    K_mat = np.array([
        [cfg["kxx"], cfg["kxy"]],
        [cfg["kyx"], cfg["kyy"]]
    ])
    fig.add_trace(go.Heatmap(
        z=K_mat,
        x=["X", "Y"], y=["X", "Y"],
        colorscale="RdBu_r",
        text=[["{:.2e}".format(v) for v in row] for row in K_mat],
        texttemplate="%{text}",
        showscale=True,
        colorbar=dict(x=0.45, len=0.8)
    ), row=1, col=1)

    # Heatmap amortissement
    C_mat = np.array([
        [cfg["cxx"],            cfg.get("cxy", 0.0)],
        [cfg.get("cyx", 0.0),  cfg["cyy"]]
    ])
    fig.add_trace(go.Heatmap(
        z=C_mat,
        x=["X", "Y"], y=["X", "Y"],
        colorscale="Blues",
        text=[["{:.1f}".format(v) for v in row] for row in C_mat],
        texttemplate="%{text}",
        showscale=True,
    ), row=1, col=2)

    fig.update_layout(
        height=300,
        title="Palier HD 1 — Matrices [K] et [C]"
    )
    st.plotly_chart(fig, use_container_width=True, key="m5_coeff_fig")

    # Tableau comparatif des types de paliers
    st.markdown("### Comparaison des types de paliers")
    data_comp = []
    for btype in [
        "Palier lisse (cylindrique)",
        "Palier a lobes (2 lobes)",
        "Palier a lobes (3 lobes)",
        "Palier tilting-pad (4 patins)",
        "Palier tilting-pad (5 patins)",
    ]:
        p = _get_bearing_preset(btype)
        ratio_k = abs(p["kxy"]) / p["kxx"] if p["kxx"] > 0 else 0
        data_comp.append({
            "Type":              btype,
            "Kxx (N/m)":         "{:.2e}".format(p["kxx"]),
            "Kyy (N/m)":         "{:.2e}".format(p["kyy"]),
            "Kxy (N/m)":         "{:.2e}".format(p["kxy"]),
            "Cxx (N.s/m)":       "{:.0f}".format(p["cxx"]),
            "|Kxy/Kxx| (%)":     "{:.1f}".format(ratio_k * 100),
            "Risque instabilite":"Eleve" if ratio_k > 0.2 else
                                 "Modere" if ratio_k > 0.05 else "Faible"
        })

    st.dataframe(
        pd.DataFrame(data_comp),
        use_container_width=True,
        hide_index=True
    )

    # Note pedagogique
    st.markdown("""
    <div class="rl-card-info">
    <strong>Note :</strong><br>
    - <strong>Kxy > 0</strong> est destabilisant : il genere des forces
      orthogonales a la direction de deplacement (oil whirl).<br>
    - Les paliers <strong>tilting-pad</strong> ont Kxy ≈ 0 car les patins
      s'orientent individuellement : c'est le palier le plus stable.<br>
    - Les paliers <strong>lisses</strong> ont un Kxy eleve,
      surtout a haute vitesse.<br>
    - La vitesse d'instabilite (oil whirl) se produit generalement
      a environ <strong>0.5 x Vcritique</strong>.
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# AFFICHAGE COMPARAISON
# =============================================================================
def _display_comparison():
    if st.session_state.get("m5_comp_error"):
        st.error("Erreur : {}".format(st.session_state["m5_comp_error"]))

    camp_orig = st.session_state.get("m5_comp_orig")
    camp_hd   = st.session_state.get("m5_comp_hd")

    if camp_orig is None or camp_hd is None:
        st.info(
            "Lancez la comparaison depuis l'onglet Comparaison "
            "dans le panneau Settings."
        )
        return

    vmax = float(st.session_state.get("m5_comp_vmax", 10000))
    npts = int(st.session_state.get("m5_comp_npts",   25))

    def _get_speed_rpm(camp):
        if hasattr(camp, 'speed_range') and camp.speed_range is not None:
            return np.array(camp.speed_range) * 30 / np.pi
        return np.linspace(0, vmax, npts)

    def _get_freqs(camp):
        if hasattr(camp, 'wd') and camp.wd is not None:
            return camp.wd / (2 * np.pi)
        if hasattr(camp, 'wn') and camp.wn is not None:
            return camp.wn / (2 * np.pi)
        return None

    spd_orig = _get_speed_rpm(camp_orig)
    spd_hd   = _get_speed_rpm(camp_hd)
    fn_orig  = _get_freqs(camp_orig)
    fn_hd    = _get_freqs(camp_hd)

    if fn_orig is None or fn_hd is None:
        st.warning("Donnees de frequences introuvables.")
        return

    fig = go.Figure()
    n_modes = min(6, fn_orig.shape[1], fn_hd.shape[1])

    for i in range(n_modes):
        fig.add_trace(go.Scatter(
            x=spd_orig,
            y=fn_orig[:, i],
            name="Rigide M{}".format(i + 1),
            line=dict(
                color="#1F5C8B",
                width=2, dash="solid"
            ),
            opacity=0.7
        ))
        fig.add_trace(go.Scatter(
            x=spd_hd,
            y=fn_hd[:, i],
            name="HD M{}".format(i + 1),
            line=dict(
                color="#C55A11",
                width=2, dash="dash"
            ),
            opacity=0.9
        ))

    # Harmonique 1X
    x_line = np.array([0, vmax])
    fig.add_trace(go.Scatter(
        x=x_line, y=x_line / 60,
        name="1X",
        line=dict(color="#E53935", width=1, dash="dot")
    ))

    fig.update_layout(
        height=460,
        title="Campbell : Paliers Rigides (bleu) vs HD (orange)",
        xaxis_title="Vitesse (RPM)",
        yaxis_title="Frequence (Hz)",
        plot_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#F0F4FF"),
        yaxis=dict(showgrid=True, gridcolor="#F0F4FF"),
        legend=dict(
            orientation="h", yanchor="bottom",
            y=1.02, xanchor="right", x=1
        )
    )

    st.plotly_chart(fig, use_container_width=True, key="m5_comp_fig")

    # Comparaison Log Dec
    ld_orig = getattr(camp_orig, 'log_dec', None)
    ld_hd   = getattr(camp_hd,   'log_dec', None)

    if ld_orig is not None and ld_hd is not None:
        st.markdown("### Comparaison Log Decrements")

        op_rpm = float(st.session_state.get("m3_op_rpm", 3000.0))
        idx_o  = int(np.argmin(np.abs(spd_orig - op_rpm)))
        idx_h  = int(np.argmin(np.abs(spd_hd   - op_rpm)))

        rows = []
        for i in range(n_modes):
            ld_o = float(ld_orig[idx_o, i])
            ld_h = float(ld_hd[idx_h,   i])
            rows.append({
                "Mode":           i + 1,
                "Log Dec Rigide": "{:.4f}".format(ld_o),
                "Log Dec HD":     "{:.4f}".format(ld_h),
                "Variation (%)":  "{:.1f}".format(
                    (ld_h - ld_o) / abs(ld_o) * 100
                    if abs(ld_o) > 1e-10 else 0.0
                ),
                "Statut Rigide":  "OK" if ld_o >= 0.1 else "NON",
                "Statut HD":      "OK" if ld_h >= 0.1 else "NON",
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Export comparaison CSV",
            data=pd.DataFrame(rows).to_csv(index=False).encode(),
            file_name="comparaison_paliers.csv",
            mime="text/csv",
            key="m5_comp_csv"
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
