# modules/m4_unbalance.py — Balourd & Reponse Frequentielle H(jw)
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
# Couvre : ISO 1940, Bode, Polaire, Nyquist, H(jw), multi-noeuds, multi-sondes
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
def render_m4(col_settings, col_graphics):
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
        '<div class="rl-settings-title">Unbalance Response & H(jw)</div>',
        unsafe_allow_html=True
    )

    if rotor is None:
        st.warning("Aucun rotor — construisez d'abord un modele dans M1.")
        return

    n_nodes = len(rotor.nodes) - 1
    n_dof   = rotor.ndof

    tab_bal, tab_freq = st.tabs(["Balourd ISO 1940", "H(jw) Frequentielle"])

    # ── ONGLET BALOURD ────────────────────────────────────────────────────
    with tab_bal:
        st.markdown(
            '<div class="rl-section-header">Definition du balourd</div>',
            unsafe_allow_html=True
        )

        # Mode de definition
        bal_mode = st.radio(
            "Mode de definition :",
            ["Manuel (kg.m)", "Automatique ISO 1940"],
            horizontal=True,
            key="m4_bal_mode"
        )

        if bal_mode == "Automatique ISO 1940":
            c1, c2 = st.columns(2)
            with c1:
                grade = st.selectbox(
                    "Grade ISO 1940 :",
                    ["G0.4", "G1.0", "G2.5", "G6.3", "G16", "G40"],
                    index=2,
                    key="m4_grade",
                    help="G2.5 = turbines, compresseurs"
                )
                grade_val = float(grade[1:])
            with c2:
                op_rpm_iso = st.number_input(
                    "Vitesse operationnelle (RPM)",
                    100.0, 50000.0, 3000.0,
                    key="m4_op_iso"
                )
            omega_iso = op_rpm_iso * np.pi / 30
            mag_iso   = (rotor.m * grade_val) / (1000.0 * omega_iso)
            st.info(
                "Balourd tolere ({}): **{:.6f} kg.m**\n\n"
                "Masse rotor : {:.2f} kg".format(grade, mag_iso, rotor.m)
            )
            st.session_state["m4_mag_computed"] = mag_iso
        else:
            st.session_state["m4_mag_computed"] = None

        st.markdown(
            '<div class="rl-section-header">Noeuds et sondes</div>',
            unsafe_allow_html=True
        )

        # Nombre de balourds
        n_unb = st.slider(
            "Nombre de balourds simultanees",
            1, min(4, n_nodes + 1), 1,
            key="m4_n_unb"
        )

        unb_nodes = []
        unb_mags  = []
        unb_phases = []

        for i in range(n_unb):
            st.markdown("**Balourd {} :**".format(i + 1))
            c1, c2, c3 = st.columns(3)
            with c1:
                node = st.slider(
                    "Noeud",
                    0, n_nodes,
                    min(i * 2, n_nodes),
                    key="m4_un_{}".format(i)
                )
            with c2:
                if st.session_state.get("m4_mag_computed"):
                    mag = st.number_input(
                        "Magnitude (kg.m)",
                        1e-7, 1.0,
                        float(st.session_state["m4_mag_computed"]),
                        format="%.7f",
                        key="m4_mag_{}".format(i)
                    )
                else:
                    mag = st.number_input(
                        "Magnitude (kg.m)",
                        1e-7, 1.0, 0.001,
                        format="%.6f",
                        key="m4_mag_{}".format(i)
                    )
            with c3:
                phase = st.slider(
                    "Phase (deg)",
                    0, 360, i * 90,
                    key="m4_ph_{}".format(i)
                )
            unb_nodes.append(node)
            unb_mags.append(mag)
            unb_phases.append(np.radians(phase))

        st.session_state["m4_unb_nodes"]  = unb_nodes
        st.session_state["m4_unb_mags"]   = unb_mags
        st.session_state["m4_unb_phases"] = unb_phases

        st.markdown(
            '<div class="rl-section-header">Sondes de mesure</div>',
            unsafe_allow_html=True
        )

        n_probes = st.slider(
            "Nombre de sondes",
            1, min(4, n_nodes + 1), 1,
            key="m4_n_probes"
        )

        probe_nodes = []
        probe_dirs  = []
        for i in range(n_probes):
            c1, c2 = st.columns(2)
            with c1:
                pn = st.slider(
                    "Sonde {} — Noeud".format(i + 1),
                    0, n_nodes,
                    min(i + 1, n_nodes),
                    key="m4_pn_{}".format(i)
                )
            with c2:
                pd_sel = st.radio(
                    "Direction",
                    ["X", "Y"],
                    horizontal=True,
                    key="m4_pd_{}".format(i)
                )
            probe_nodes.append(pn)
            probe_dirs.append(0 if pd_sel == "X" else 1)

        st.session_state["m4_probe_nodes"] = probe_nodes
        st.session_state["m4_probe_dirs"]  = probe_dirs

        st.markdown(
            '<div class="rl-section-header">Plage de frequences</div>',
            unsafe_allow_html=True
        )

        fmax = st.slider(
            "Frequence maximale (Hz)",
            100, 5000, 2000,
            key="m4_fmax"
        )
        n_pts = st.slider(
            "Resolution (points)",
            100, 1000, 500,
            key="m4_npts"
        )

        st.button(
            "Calculer la reponse au balourd",
            type="primary",
            key="m4_run_bal",
            use_container_width=True,
            on_click=_run_unbalance
        )

    # ── ONGLET H(jw) ──────────────────────────────────────────────────────
    with tab_freq:
        st.markdown(
            '<div class="rl-section-header">Fonction de transfert H(jw)</div>',
            unsafe_allow_html=True
        )
        st.caption(
            "H(jw) entre un DDL d excitation (inp) "
            "et un DDL de reponse (out)."
        )

        c1, c2 = st.columns(2)
        with c1:
            inp_n = st.slider(
                "DDL excitation (inp)",
                0, min(n_dof - 1, 31), 0,
                key="m4_inp"
            )
            st.caption(
                "Noeud {}, DDL {}".format(inp_n // 4, inp_n % 4)
            )
        with c2:
            out_n = st.slider(
                "DDL reponse (out)",
                0, min(n_dof - 1, 31),
                min(8, n_dof - 1),
                key="m4_out"
            )
            st.caption(
                "Noeud {}, DDL {}".format(out_n // 4, out_n % 4)
            )

        fmax_h = st.slider(
            "Frequence max H(jw) (Hz)",
            100, 5000, 2000,
            key="m4_fmax_h"
        )
        n_pts_h = st.slider(
            "Resolution H(jw)",
            100, 1000, 500,
            key="m4_npts_h"
        )

        st.button(
            "Calculer H(jw)",
            type="primary",
            key="m4_run_freq",
            use_container_width=True,
            on_click=_run_freq_response
        )


# =============================================================================
# PANNEAU GRAPHICS
# =============================================================================
def _render_graphics(rotor):
    st.markdown(
        '<div class="rl-graphics-title">'
        'Unbalance Response & H(jw) — Results'
        '</div>',
        unsafe_allow_html=True
    )

    if rotor is None:
        st.info("Construisez un rotor dans M1 pour acceder aux analyses.")
        return

    tab_bode, tab_polar, tab_camp, tab_orbit, tab_hfw, tab_nyq, tab_iso = st.tabs([
        "Bode (Balourd)",
        "Polaire",
        "Camp. + Balourd",
        "Orbites",
        "H(jw) Bode",
        "Nyquist",
        "ISO 1940"
    ])

    with tab_bode:
        _display_bode_unbalance()

    with tab_polar:
        _display_polar()

    with tab_camp:
        _display_campbell_unbalance()

    with tab_orbit:
        _display_orbits()

    with tab_hfw:
        _display_freq_response_bode()

    with tab_nyq:
        _display_nyquist()

    with tab_iso:
        _display_iso1940(rotor)


# =============================================================================
# CALCUL BALOURD
# =============================================================================
def _run_unbalance():
    rotor = st.session_state.get("rotor")
    if rotor is None:
        return

    nodes  = st.session_state.get("m4_unb_nodes",  [0])
    mags   = st.session_state.get("m4_unb_mags",   [0.001])
    phases = st.session_state.get("m4_unb_phases",  [0.0])
    fmax   = float(st.session_state.get("m4_fmax",  2000))
    n_pts  = int(st.session_state.get("m4_npts",    500))

    freqs = np.linspace(0, fmax, n_pts)

    try:
        # Tentative 1 : API ROSS recente (unbalance_magnitude / unbalance_phase)
        resp = rotor.run_unbalance_response(
            node=nodes,
            unbalance_magnitude=mags,
            unbalance_phase=phases,
            frequency=freqs
        )
    except TypeError:
        try:
            # Tentative 2 : API intermediaire (magnitude / phase / frequency_range)
            resp = rotor.run_unbalance_response(
                node=nodes,
                magnitude=mags,
                phase=phases,
                frequency_range=freqs
            )
        except TypeError:
            try:
                # Tentative 3 : Scalaire + speed_range
                resp = rotor.run_unbalance_response(
                    node=nodes[0],
                    magnitude=mags[0],
                    phase=phases[0],
                    frequency_range=freqs
                )
            except Exception as e:
                _log("Erreur balourd : {}".format(e), "err")
                st.session_state["m4_unbal_error"] = str(e)
                return

    st.session_state["res_unbalance"] = resp
    st.session_state["m4_unbal_error"] = None
    _log("Reponse au balourd calculee ({} noeuds, fmax={} Hz)".format(
        len(nodes), fmax), "ok")


# =============================================================================
# CALCUL H(jw)
# =============================================================================
def _run_freq_response():
    rotor = st.session_state.get("rotor")
    if rotor is None:
        return

    fmax  = float(st.session_state.get("m4_fmax_h",  2000))
    n_pts = int(st.session_state.get("m4_npts_h",    500))
    freqs = np.linspace(0, fmax, n_pts)

    try:
        fr = rotor.run_freq_response(frequency=freqs)
    except TypeError:
        try:
            fr = rotor.run_freq_response(frequency_range=freqs)
        except Exception as e:
            _log("Erreur H(jw) : {}".format(e), "err")
            st.session_state["m4_freq_error"] = str(e)
            return

    st.session_state["res_freq"] = fr
    st.session_state["m4_freq_error"] = None
    _log("H(jw) calculee (fmax={} Hz)".format(fmax), "ok")


# =============================================================================
# EXTRACTION ROBUSTE DES DONNEES DE REPONSE
# =============================================================================
def _extract_response(res, probe_node, probe_dof):
    """
    Extrait (freqs_hz, amplitudes_m, phases_rad) depuis un objet
    UnbalanceResponse ROSS, quelle que soit la version de l API.
    """
    # Extraction des frequences
    if hasattr(res, 'speed_range') and res.speed_range is not None:
        freqs = np.array(res.speed_range) / (2 * np.pi)
    elif hasattr(res, 'frequency') and res.frequency is not None:
        freqs = np.array(res.frequency)
    elif hasattr(res, 'frequency_range') and res.frequency_range is not None:
        freqs = np.array(res.frequency_range)
    else:
        freqs = np.linspace(0, 2000, 500)

    freqs = np.atleast_1d(freqs).flatten()
    probe = [probe_node, probe_dof]

    # Plan A : methodes data_magnitude / data_phase (API moderne)
    if hasattr(res, 'data_magnitude') and callable(res.data_magnitude):
        try:
            amps   = np.atleast_1d(res.data_magnitude(probe=probe)).flatten()
            phases = np.atleast_1d(res.data_phase(probe=probe)).flatten()
            n = min(len(amps), len(freqs))
            return freqs[:n], amps[:n], phases[:n]
        except Exception:
            pass

    # Plan B : matrice forced_resp / response
    for attr in ("forced_resp", "response"):
        if hasattr(res, attr):
            arr = np.array(getattr(res, attr))
            break
    else:
        raise AttributeError(
            "Donnees vibratoires introuvables (ni data_magnitude, "
            "ni forced_resp, ni response)."
        )

    mag = np.abs(arr)
    ph  = np.angle(arr)
    mag = np.atleast_1d(mag)
    ph  = np.atleast_1d(ph)

    # Pivot si necessaire
    if mag.ndim >= 2:
        if mag.shape[0] == len(freqs) and mag.shape[1] != len(freqs):
            mag = mag.T
            ph  = ph.T

    dof      = probe_node * 4 + probe_dof
    safe_dof = min(dof, mag.shape[0] - 1) if mag.ndim > 0 else 0

    if mag.ndim == 3:
        amps   = mag[safe_dof, 0, :]
        phases = ph[safe_dof, 0, :]
    elif mag.ndim == 2:
        amps   = mag[safe_dof, :]
        phases = ph[safe_dof, :]
    else:
        amps   = mag
        phases = ph

    amps   = np.atleast_1d(amps).flatten()
    phases = np.atleast_1d(phases).flatten()
    n      = min(len(amps), len(freqs))
    return freqs[:n], amps[:n], phases[:n]


# =============================================================================
# AFFICHAGE BODE BALOURD
# =============================================================================
def _display_bode_unbalance():
    if st.session_state.get("m4_unbal_error"):
        st.error("Erreur : {}".format(st.session_state["m4_unbal_error"]))

    res = st.session_state.get("res_unbalance")
    if res is None:
        st.info(
            "Configurez et lancez le calcul dans le panneau Settings."
        )
        return

    probe_nodes = st.session_state.get("m4_probe_nodes", [1])
    probe_dirs  = st.session_state.get("m4_probe_dirs",  [0])
    modal       = st.session_state.get("res_modal")

    colors = ["#1F5C8B", "#C55A11", "#22863A", "#7B1FA2"]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=["Amplitude (µm)", "Phase (deg)"],
        vertical_spacing=0.10
    )

    all_amps = []

    for idx, (pn, pd) in enumerate(zip(probe_nodes, probe_dirs)):
        try:
            freqs, amps, phases = _extract_response(res, pn, pd)
        except Exception as e:
            st.warning("Sonde {} : {}".format(idx + 1, e))
            continue

        amps_um = amps * 1e6
        all_amps.extend(amps_um.tolist())
        color = colors[idx % len(colors)]
        label = "Sonde {} — N{} {}".format(
            idx + 1, pn, "X" if pd == 0 else "Y")

        fig.add_trace(go.Scatter(
            x=freqs, y=amps_um,
            name=label,
            line=dict(color=color, width=2),
            hovertemplate=(
                "f = %{x:.1f} Hz<br>"
                "A = %{y:.3f} µm<extra>" + label + "</extra>"
            )
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=freqs, y=np.degrees(phases),
            name=label + " (phase)",
            line=dict(color=color, width=1.5, dash="dot"),
            showlegend=False
        ), row=2, col=1)

    # Marqueurs des modes propres
    if modal is not None:
        for i, wn in enumerate(modal.wn[:6]):
            fn = wn / (2 * np.pi)
            for row in [1, 2]:
                fig.add_vline(
                    x=fn, line_dash="dot",
                    line_color="#22863A",
                    line_width=1,
                    opacity=0.6,
                    annotation_text="M{}".format(i + 1) if row == 1 else "",
                    annotation_font=dict(color="#22863A", size=10),
                    row=row, col=1
                )

    fig.update_xaxes(
        title_text="Frequence (Hz)", row=2, col=1,
        showgrid=True, gridcolor="#F0F4FF"
    )
    fig.update_yaxes(
        title_text="Amplitude (µm)", row=1, col=1,
        showgrid=True, gridcolor="#F0F4FF"
    )
    fig.update_yaxes(
        title_text="Phase (deg)", row=2, col=1,
        showgrid=True, gridcolor="#F0F4FF"
    )
    fig.update_layout(
        height=500,
        title="Diagramme de Bode — Reponse au balourd",
        plot_bgcolor="white",
        legend=dict(
            orientation="h", yanchor="bottom",
            y=1.02, xanchor="right", x=1
        )
    )

    st.plotly_chart(fig, use_container_width=True, key="m4_bode_fig")

    # Metriques
    if all_amps:
        idx_max = int(np.argmax(all_amps))
        a_max   = max(all_amps)
        try:
            freqs_0, amps_0, _ = _extract_response(
                res,
                probe_nodes[0],
                probe_dirs[0]
            )
            a_stat = float(amps_0[1]) * 1e6 if len(amps_0) > 1 else 1e-12
            a_stat = max(a_stat, 1e-12)
            daf    = a_max / a_stat

            c1, c2, c3, c4 = st.columns(4)
            c1.markdown("""
            <div class="rl-metric-card">
              <div class="rl-metric-label">Amplitude max</div>
              <div class="rl-metric-value">{:.3f}</div>
              <div class="rl-metric-unit">µm</div>
            </div>""".format(a_max), unsafe_allow_html=True)

            f_res = freqs_0[np.argmax(amps_0 * 1e6)] \
                if len(freqs_0) > 0 else 0.0
            c2.markdown("""
            <div class="rl-metric-card">
              <div class="rl-metric-label">Frequence resonance</div>
              <div class="rl-metric-value">{:.1f}</div>
              <div class="rl-metric-unit">Hz</div>
            </div>""".format(f_res), unsafe_allow_html=True)

            c3.markdown("""
            <div class="rl-metric-card">
              <div class="rl-metric-label">DAF</div>
              <div class="rl-metric-value">{:.1f}</div>
              <div class="rl-metric-unit">—</div>
            </div>""".format(daf), unsafe_allow_html=True)

            c4.markdown("""
            <div class="rl-metric-card">
              <div class="rl-metric-label">Amplitude statique</div>
              <div class="rl-metric-value">{:.4f}</div>
              <div class="rl-metric-unit">µm</div>
            </div>""".format(a_stat), unsafe_allow_html=True)

        except Exception:
            pass

    # Export CSV
    try:
        freqs_e, amps_e, phases_e = _extract_response(
            res, probe_nodes[0], probe_dirs[0])
        df_exp = pd.DataFrame({
            "Frequence (Hz)":   freqs_e,
            "Amplitude (µm)":   amps_e * 1e6,
            "Phase (deg)":      np.degrees(phases_e),
        })
        st.download_button(
            "Export CSV balourd",
            data=df_exp.to_csv(index=False).encode(),
            file_name="balourd_response.csv",
            mime="text/csv",
            key="m4_bode_csv"
        )
    except Exception:
        pass


# =============================================================================
# AFFICHAGE POLAIRE
# =============================================================================
def _display_polar():
    res = st.session_state.get("res_unbalance")
    if res is None:
        st.info("Calculez d'abord la reponse au balourd.")
        return

    probe_nodes = st.session_state.get("m4_probe_nodes", [1])
    probe_dirs  = st.session_state.get("m4_probe_dirs",  [0])
    colors      = ["#1F5C8B", "#C55A11", "#22863A", "#7B1FA2"]

    fig = go.Figure()

    for idx, (pn, pd) in enumerate(zip(probe_nodes, probe_dirs)):
        try:
            freqs, amps, phases = _extract_response(res, pn, pd)
        except Exception as e:
            continue

        x_re  = amps * np.cos(phases) * 1e6
        y_im  = amps * np.sin(phases) * 1e6
        color = colors[idx % len(colors)]
        label = "Sonde {} — N{} {}".format(
            idx + 1, pn, "X" if pd == 0 else "Y")

        fig.add_trace(go.Scatter(
            x=x_re, y=y_im,
            mode="lines+markers",
            marker=dict(
                size=4,
                color=freqs,
                colorscale="Viridis",
                colorbar=dict(title="Hz") if idx == 0 else None,
                showscale=(idx == 0)
            ),
            line=dict(color=color, width=1.5),
            name=label,
            hovertemplate=(
                "Re = %{x:.3f} µm<br>Im = %{y:.3f} µm"
                "<extra>" + label + "</extra>"
            )
        ))

        # Marqueur de resonance
        idx_res = int(np.argmax(amps))
        fig.add_trace(go.Scatter(
            x=[x_re[idx_res]], y=[y_im[idx_res]],
            mode="markers+text",
            marker=dict(size=14, color="#C00000", symbol="star"),
            text=["{:.0f} Hz".format(freqs[idx_res])],
            textposition="top center",
            name="Resonance {}".format(idx + 1),
            showlegend=True
        ))

    fig.update_layout(
        height=500,
        title="Diagramme Polaire de Bode",
        xaxis_title="Re (µm)",
        yaxis_title="Im (µm)",
        yaxis_scaleanchor="x",
        plot_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#F0F4FF", zeroline=True),
        yaxis=dict(showgrid=True, gridcolor="#F0F4FF", zeroline=True),
    )

    st.plotly_chart(fig, use_container_width=True, key="m4_polar_fig")
    st.caption(
        "Le diagramme polaire montre la trajectoire complexe de la reponse. "
        "Les cercles correspondent aux resonances (pics d amplitude)."
    )


# =============================================================================
# AFFICHAGE CAMPBELL + BALOURD SUPERPOSE
# =============================================================================
def _display_campbell_unbalance():
    res   = st.session_state.get("res_unbalance")
    camp  = st.session_state.get("res_campbell")
    rotor = st.session_state.get("rotor")

    if res is None:
        st.info("Calculez d'abord la reponse au balourd.")
        return

    probe_nodes = st.session_state.get("m4_probe_nodes", [1])
    probe_dirs  = st.session_state.get("m4_probe_dirs",  [0])

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Courbes modales Campbell (si disponibles)
    if camp is not None:
        if hasattr(camp, 'speed_range') and camp.speed_range is not None:
            spd_rad = np.array(camp.speed_range)
        else:
            vmax    = float(st.session_state.get("m3_camp_vmax", 10000))
            npts    = int(st.session_state.get("m3_camp_npts",   60))
            spd_rad = np.linspace(0, vmax * np.pi / 30, npts)

        spd_rpm = spd_rad * 30 / np.pi

        if hasattr(camp, 'wd') and camp.wd is not None:
            fn_mat = camp.wd / (2 * np.pi)
        elif hasattr(camp, 'wn') and camp.wn is not None:
            fn_mat = camp.wn / (2 * np.pi)
        else:
            fn_mat = None

        if fn_mat is not None:
            colors_m = ["#B0C4DE", "#87CEEB", "#90EE90", "#DDA0DD"]
            for i in range(min(4, fn_mat.shape[1])):
                fig.add_trace(go.Scatter(
                    x=spd_rpm, y=fn_mat[:, i],
                    name="Mode {}".format(i + 1),
                    line=dict(
                        color=colors_m[i % len(colors_m)],
                        dash="dot", width=1.5
                    ),
                    opacity=0.7
                ), secondary_y=False)

        # Droite 1X
        fig.add_trace(go.Scatter(
            x=spd_rpm, y=spd_rpm / 60,
            name="1X",
            line=dict(color="#E53935", dash="dash", width=1),
            opacity=0.6
        ), secondary_y=False)

    # Courbe de reponse au balourd
    colors_b = ["#FF6B00", "#C55A11", "#22863A", "#7B1FA2"]
    for idx, (pn, pd) in enumerate(zip(probe_nodes, probe_dirs)):
        try:
            freqs, amps, _ = _extract_response(res, pn, pd)
        except Exception:
            continue

        label = "Sonde {} N{} {}".format(
            idx + 1, pn, "X" if pd == 0 else "Y")

        fig.add_trace(go.Scatter(
            x=freqs * 60,
            y=amps * 1e6,
            name=label,
            line=dict(
                color=colors_b[idx % len(colors_b)],
                width=3
            ),
            fill="tozeroy",
            fillcolor="rgba(255,107,0,0.07)"
        ), secondary_y=True)

    fig.update_yaxes(
        title_text="Frequence modale (Hz)",
        secondary_y=False,
        showgrid=True, gridcolor="#F0F4FF"
    )
    fig.update_yaxes(
        title_text="Amplitude balourd (µm)",
        secondary_y=True,
        showgrid=False
    )
    fig.update_xaxes(
        title_text="Vitesse (RPM)",
        showgrid=True, gridcolor="#F0F4FF"
    )
    fig.update_layout(
        height=480,
        title="Campbell + Reponse au balourd superposes",
        plot_bgcolor="white",
        legend=dict(
            orientation="h", yanchor="bottom",
            y=1.02, xanchor="right", x=1
        )
    )

    st.plotly_chart(fig, use_container_width=True, key="m4_camp_unb_fig")
    st.caption(
        "Les pics de la courbe orange coincident avec les "
        "vitesses critiques (intersections 1X)."
    )


# =============================================================================
# AFFICHAGE ORBITES
# =============================================================================
def _display_orbits():
    res   = st.session_state.get("res_unbalance")
    if res is None:
        st.info("Calculez d'abord la reponse au balourd.")
        return

    probe_nodes = st.session_state.get("m4_probe_nodes", [1])
    probe_dirs  = st.session_state.get("m4_probe_dirs",  [0])

    # Tentative via methode native ROSS plot_orbit
    try:
        for method in ["plot_orbit", "plot_orbits"]:
            if hasattr(res, method):
                fig = getattr(res, method)()
                st.plotly_chart(fig, use_container_width=True,
                                key="m4_orbit_native")
                return
    except Exception:
        pass

    # Construction manuelle des orbites
    st.caption("Construction des orbites depuis les donnees de reponse.")
    n_orbits = min(len(probe_nodes), 4)
    cols = st.columns(min(n_orbits, 2))

    for idx in range(n_orbits):
        pn = probe_nodes[idx]

        # Extraire X et Y pour le meme noeud
        try:
            freqs, amps_x, phases_x = _extract_response(res, pn, 0)
            freqs, amps_y, phases_y = _extract_response(res, pn, 1)
        except Exception as e:
            st.warning("Orbite noeud {} : {}".format(pn, e))
            continue

        # Orbite a la frequence de resonance
        idx_res = int(np.argmax(amps_x))
        f_res   = freqs[idx_res]
        ax      = float(amps_x[idx_res]) * 1e6
        ay      = float(amps_y[idx_res]) * 1e6
        phx     = float(phases_x[idx_res])
        phy     = float(phases_y[idx_res])

        theta   = np.linspace(0, 2 * np.pi, 200)
        x_orb   = ax * np.cos(theta + phx)
        y_orb   = ay * np.cos(theta + phy)

        fig_orb = go.Figure()
        fig_orb.add_trace(go.Scatter(
            x=x_orb, y=y_orb,
            mode="lines",
            line=dict(color="#1F5C8B", width=2),
            name="Orbite N{}".format(pn)
        ))
        fig_orb.add_trace(go.Scatter(
            x=[0], y=[0],
            mode="markers",
            marker=dict(size=6, color="#C00000", symbol="x"),
            name="Centre"
        ))
        fig_orb.update_layout(
            height=320,
            title="Orbite Noeud {} @ {:.1f} Hz".format(pn, f_res),
            xaxis_title="X (µm)",
            yaxis_title="Y (µm)",
            yaxis_scaleanchor="x",
            plot_bgcolor="white",
            xaxis=dict(showgrid=True, gridcolor="#F0F4FF", zeroline=True),
            yaxis=dict(showgrid=True, gridcolor="#F0F4FF", zeroline=True),
        )

        with cols[idx % len(cols)]:
            st.plotly_chart(fig_orb, use_container_width=True,
                            key="m4_orbit_{}".format(idx))

    st.caption(
        "Les orbites sont tracees a la frequence de resonance. "
        "Une orbite circulaire = amortissement isotrope. "
        "Une orbite elliptique = anisotropie des paliers."
    )


# =============================================================================
# AFFICHAGE H(jw) BODE
# =============================================================================
def _display_freq_response_bode():
    if st.session_state.get("m4_freq_error"):
        st.error("Erreur : {}".format(st.session_state["m4_freq_error"]))

    fr    = st.session_state.get("res_freq")
    modal = st.session_state.get("res_modal")

    if fr is None:
        st.info("Configurez et calculez H(jw) dans le panneau Settings.")
        return

    inp_n = int(st.session_state.get("m4_inp", 0))
    out_n = int(st.session_state.get("m4_out", 8))
    fmax  = float(st.session_state.get("m4_fmax_h", 2000))

    # Tentative methode native
    for method in ["plot_bode", "plot_magnitude"]:
        if hasattr(fr, method):
            try:
                fig = getattr(fr, method)(inp=inp_n, out=out_n)
                fig.update_layout(height=480)
                st.plotly_chart(fig, use_container_width=True,
                                key="m4_hjw_native")
                return
            except TypeError:
                try:
                    fig = getattr(fr, method)()
                    fig.update_layout(height=480)
                    st.plotly_chart(fig, use_container_width=True,
                                    key="m4_hjw_native2")
                    return
                except Exception:
                    pass

    # Construction manuelle
    H_raw = None
    for attr in ("freq_resp", "response", "H"):
        if hasattr(fr, attr):
            H_raw = np.array(getattr(fr, attr))
            break

    if H_raw is None:
        st.warning("Structure FreqResponse non reconnue.")
        return

    H = H_raw[out_n, inp_n, :] if H_raw.ndim == 3 else H_raw

    freqs = None
    for attr in ("frequency", "frequency_range", "speed_range"):
        if hasattr(fr, attr) and getattr(fr, attr) is not None:
            freqs = np.array(getattr(fr, attr))
            if "speed" in attr:
                freqs = freqs / (2 * np.pi)
            break
    if freqs is None:
        freqs = np.linspace(0, fmax, len(H))

    mag_db = 20 * np.log10(np.abs(H) + 1e-30)
    phase  = np.degrees(np.unwrap(np.angle(H)))

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=["Magnitude (dB)", "Phase (deg)"],
        vertical_spacing=0.10
    )

    fig.add_trace(go.Scatter(
        x=freqs, y=mag_db,
        line=dict(color="#1F5C8B", width=2),
        name="Magnitude",
        hovertemplate="f=%{x:.1f} Hz<br>|H|=%{y:.1f} dB<extra></extra>"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=freqs, y=phase,
        line=dict(color="#C55A11", width=2),
        name="Phase"
    ), row=2, col=1)

    # Modes propres
    if modal is not None:
        for i, wn in enumerate(modal.wn[:6]):
            fn = wn / (2 * np.pi)
            for row in [1, 2]:
                fig.add_vline(
                    x=fn, line_dash="dot",
                    line_color="#22863A",
                    line_width=1,
                    opacity=0.5,
                    annotation_text="M{}".format(i + 1) if row == 1 else "",
                    annotation_font=dict(color="#22863A", size=10),
                    row=row, col=1
                )

    fig.update_xaxes(
        title_text="Frequence (Hz)", row=2, col=1,
        showgrid=True, gridcolor="#F0F4FF"
    )
    fig.update_yaxes(
        title_text="dB", row=1, col=1,
        showgrid=True, gridcolor="#F0F4FF"
    )
    fig.update_yaxes(
        title_text="deg", row=2, col=1,
        showgrid=True, gridcolor="#F0F4FF"
    )
    fig.update_layout(
        height=500,
        title="H(jw) — DDL {} -> DDL {}".format(inp_n, out_n),
        plot_bgcolor="white",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True, key="m4_hjw_manual")

    # Export
    df_h = pd.DataFrame({
        "Frequence (Hz)": freqs,
        "Magnitude (dB)": mag_db,
        "Phase (deg)":    phase,
    })
    st.download_button(
        "Export CSV H(jw)",
        data=df_h.to_csv(index=False).encode(),
        file_name="freq_response.csv",
        mime="text/csv",
        key="m4_hjw_csv"
    )


# =============================================================================
# AFFICHAGE NYQUIST
# =============================================================================
def _display_nyquist():
    fr = st.session_state.get("res_freq")

    if fr is None:
        st.info("Calculez d'abord H(jw) dans le panneau Settings.")
        return

    inp_n = int(st.session_state.get("m4_inp", 0))
    out_n = int(st.session_state.get("m4_out", 8))

    H_raw = None
    for attr in ("freq_resp", "response", "H"):
        if hasattr(fr, attr):
            H_raw = np.array(getattr(fr, attr))
            break

    if H_raw is None:
        st.warning("Donnees H(jw) non disponibles.")
        return

    H = H_raw[out_n, inp_n, :] if H_raw.ndim == 3 else H_raw

    freqs = None
    for attr in ("frequency", "frequency_range", "speed_range"):
        if hasattr(fr, attr) and getattr(fr, attr) is not None:
            freqs = np.array(getattr(fr, attr))
            if "speed" in attr:
                freqs = freqs / (2 * np.pi)
            break
    if freqs is None:
        freqs = np.linspace(0, 2000, len(H))

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=H.real, y=H.imag,
        mode="lines",
        line=dict(color="#1F5C8B", width=2),
        name="H(jw)",
        hovertemplate=(
            "Re = %{x:.3e}<br>Im = %{y:.3e}<extra></extra>"
        ),
        customdata=freqs,
    ))

    # Point de depart (f=0) et d arrivee
    fig.add_trace(go.Scatter(
        x=[H.real[0]], y=[H.imag[0]],
        mode="markers+text",
        marker=dict(size=10, color="#22863A", symbol="circle"),
        text=["f=0"],
        textposition="top right",
        name="Debut"
    ))
    fig.add_trace(go.Scatter(
        x=[H.real[-1]], y=[H.imag[-1]],
        mode="markers+text",
        marker=dict(size=10, color="#C00000", symbol="square"),
        text=["f=fmax"],
        textposition="top right",
        name="Fin"
    ))

    # Point critique -1+0j
    fig.add_trace(go.Scatter(
        x=[-1], y=[0],
        mode="markers",
        marker=dict(size=12, color="#C00000", symbol="x"),
        name="Point critique (-1, 0)"
    ))

    fig.update_layout(
        height=480,
        title="Diagramme de Nyquist — H(jw) DDL {} -> DDL {}".format(
            inp_n, out_n),
        xaxis_title="Re[H(jw)]",
        yaxis_title="Im[H(jw)]",
        yaxis_scaleanchor="x",
        plot_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#F0F4FF", zeroline=True),
        yaxis=dict(showgrid=True, gridcolor="#F0F4FF", zeroline=True),
    )

    st.plotly_chart(fig, use_container_width=True, key="m4_nyq_fig")
    st.caption(
        "Le diagramme de Nyquist montre H(jw) dans le plan complexe. "
        "L encerclement du point -1 indique une instabilite en boucle fermee."
    )


# =============================================================================
# TABLEAU ISO 1940
# =============================================================================
def _display_iso1940(rotor):
    st.markdown("### Verification ISO 1940 — Qualite d'equilibrage")

    op_rpm = float(st.session_state.get("m4_op_iso",
                   st.session_state.get("m3_op_rpm", 3000.0)))
    omega  = op_rpm * np.pi / 30
    m_rot  = rotor.m

    grades = [0.4, 1.0, 2.5, 6.3, 16.0, 40.0]
    apps   = [
        "Gyroscopes, turbines ultra-precision",
        "Turbines a gaz, turbines vapeur (production)",
        "Turbines vapeur, compresseurs, turbosoufflantes",
        "Machines-outils, ventilateurs industriels",
        "Vilebrequins, transmissions",
        "Machines agricoles, equipements generaux"
    ]

    rows = []
    for g, app in zip(grades, apps):
        uper  = (m_rot * g) / (1000.0 * omega)
        e_per = uper / m_rot * 1e6  # excentricite en µm
        rows.append({
            "Grade":              "G{:.1f}".format(g),
            "Application":        app,
            "Uper (kg.m)":        "{:.6f}".format(uper),
            "Excentricite (µm)":  "{:.2f}".format(e_per),
        })

    df_iso = pd.DataFrame(rows)

    # Surligner G2.5 par defaut
    st.dataframe(df_iso, use_container_width=True, hide_index=True)

    # Graphique Uper vs grade
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["G{:.1f}".format(g) for g in grades],
        y=[(m_rot * g) / (1000.0 * omega) * 1e6 for g in grades],
        marker_color=["#22863A" if g == 2.5 else "#1F5C8B"
                      for g in grades],
        name="Uper (g.mm)",
        hovertemplate="Grade %{x}<br>Uper = %{y:.4f} g.mm<extra></extra>"
    ))
    fig.update_layout(
        height=340,
        title="Balourd tolere Uper vs Grade ISO 1940 "
              "(Nop = {:.0f} RPM, m = {:.2f} kg)".format(op_rpm, m_rot),
        xaxis_title="Grade ISO 1940",
        yaxis_title="Uper (g.mm)",
        plot_bgcolor="white",
        yaxis=dict(showgrid=True, gridcolor="#F0F4FF"),
    )
    st.plotly_chart(fig, use_container_width=True, key="m4_iso_fig")

    # Comparaison avec balourd applique
    unb_mags = st.session_state.get("m4_unb_mags", [0.001])
    if unb_mags:
        u_applied = float(unb_mags[0])
        u_g25     = (m_rot * 2.5) / (1000.0 * omega)
        ratio     = u_applied / u_g25 if u_g25 > 0 else 0

        if ratio <= 1.0:
            st.markdown("""
            <div class="rl-card-ok">
              <strong>Balourd applique conforme G2.5</strong><br>
              Uper applique = {:.6f} kg.m | Uper tolere G2.5 = {:.6f} kg.m<br>
              Ratio = {:.2f} (doit etre <= 1.0)
            </div>""".format(u_applied, u_g25, ratio),
                unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="rl-card-danger">
              <strong>Balourd applique depasse le grade G2.5</strong><br>
              Uper applique = {:.6f} kg.m | Uper tolere G2.5 = {:.6f} kg.m<br>
              Ratio = {:.2f} (doit etre <= 1.0)
            </div>""".format(u_applied, u_g25, ratio),
                unsafe_allow_html=True)

    st.download_button(
        "Export tableau ISO 1940 (CSV)",
        data=df_iso.to_csv(index=False).encode(),
        file_name="iso1940_verification.csv",
        mime="text/csv",
        key="m4_iso_csv"
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
