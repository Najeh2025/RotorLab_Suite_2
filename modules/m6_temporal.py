# modules/m6_temporal.py — Reponse Temporelle & Analyse Vibratoire
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
# Couvre : Newmark, Orbites, Waterfall 3D, DFFT, Demarrage/Arret
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

try:
    from scipy import signal as scipy_signal
    SCIPY_OK = True
except ImportError:
    SCIPY_OK = False


# =============================================================================
# POINT D ENTREE
# =============================================================================
def render_m6(col_settings, col_graphics):
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
        '<div class="rl-settings-title">Time Response & Vibration Analysis</div>',
        unsafe_allow_html=True
    )

    if rotor is None:
        st.warning("Aucun rotor — construisez d'abord un modele dans M1.")
        return

    n_nodes = len(rotor.nodes) - 1

    tab_time, tab_start, tab_harm = st.tabs([
        "Reponse temporelle",
        "Demarrage / Arret",
        "Chargement harmonique"
    ])

    # ── ONGLET REPONSE TEMPORELLE ─────────────────────────────────────────
    with tab_time:
        st.markdown(
            '<div class="rl-section-header">Parametres de simulation</div>',
            unsafe_allow_html=True
        )

        c1, c2 = st.columns(2)
        with c1:
            st.slider(
                "Vitesse de rotation (RPM)",
                100, 15000, 3000,
                key="m6_rpm"
            )
            st.slider(
                "Duree de simulation (s)",
                0.1, 10.0, 1.0,
                key="m6_tend"
            )
        with c2:
            st.slider(
                "Nombre de points temporels",
                200, 3000, 1000,
                key="m6_npts"
            )
            st.slider(
                "Noeud d'observation",
                0, n_nodes,
                min(2, n_nodes),
                key="m6_node_obs"
            )

        st.markdown(
            '<div class="rl-section-header">Type de chargement</div>',
            unsafe_allow_html=True
        )

        load_type = st.radio(
            "Type de force appliquee :",
            [
                "Balourd tournant",
                "Force impulsionnelle",
                "Force harmonique",
                "Aucune force (libre)"
            ],
            key="m6_load_type"
        )

        if load_type == "Balourd tournant":
            c1, c2 = st.columns(2)
            with c1:
                st.number_input(
                    "Magnitude balourd (kg.m)",
                    1e-6, 1.0, 0.001,
                    format="%.5f",
                    key="m6_unb_mag"
                )
            with c2:
                st.slider(
                    "Noeud du balourd",
                    0, n_nodes,
                    min(2, n_nodes),
                    key="m6_unb_node"
                )

        elif load_type == "Force impulsionnelle":
            c1, c2 = st.columns(2)
            with c1:
                st.number_input(
                    "Amplitude (N)",
                    1.0, 1e6, 1000.0,
                    key="m6_imp_amp"
                )
                st.slider(
                    "Noeud d'application",
                    0, n_nodes,
                    min(2, n_nodes),
                    key="m6_imp_node"
                )
            with c2:
                st.number_input(
                    "Instant d'application (s)",
                    0.0, 5.0, 0.1,
                    key="m6_imp_t"
                )
                st.number_input(
                    "Duree impulsion (s)",
                    0.001, 1.0, 0.01,
                    key="m6_imp_dur"
                )

        elif load_type == "Force harmonique":
            c1, c2 = st.columns(2)
            with c1:
                st.number_input(
                    "Amplitude (N)",
                    1.0, 1e6, 500.0,
                    key="m6_har_amp"
                )
                st.number_input(
                    "Frequence (Hz)",
                    0.1, 5000.0, 50.0,
                    key="m6_har_freq"
                )
            with c2:
                st.slider(
                    "Noeud d'application",
                    0, n_nodes,
                    min(2, n_nodes),
                    key="m6_har_node"
                )
                st.radio(
                    "Direction",
                    ["X", "Y", "X+Y"],
                    horizontal=True,
                    key="m6_har_dir"
                )

        st.button(
            "Simuler la reponse temporelle",
            type="primary",
            key="m6_run_time",
            use_container_width=True,
            on_click=_run_temporal
        )

    # ── ONGLET DEMARRAGE / ARRET ──────────────────────────────────────────
    with tab_start:
        st.markdown(
            '<div class="rl-section-header">Simulation de demarrage</div>',
            unsafe_allow_html=True
        )
        st.markdown("""
        <div class="rl-card-info">
          <small>Simule la reponse transitoire lors d'un demarrage
          (sweep de vitesse lineaire de 0 a Nmax) ou d'un arret.</small>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.number_input(
                "Vitesse initiale (RPM)",
                0.0, 5000.0, 0.0,
                key="m6_start_rpm0"
            )
            st.number_input(
                "Vitesse finale (RPM)",
                100.0, 30000.0, 5000.0,
                key="m6_start_rpmf"
            )
        with c2:
            st.number_input(
                "Duree du sweep (s)",
                0.5, 30.0, 5.0,
                key="m6_start_dur"
            )
            st.slider(
                "Noeud d'observation",
                0, n_nodes,
                min(2, n_nodes),
                key="m6_start_node"
            )

        st.number_input(
            "Magnitude balourd (kg.m)",
            1e-6, 1.0, 0.001,
            format="%.5f",
            key="m6_start_unb"
        )

        st.button(
            "Simuler le demarrage",
            type="primary",
            key="m6_run_start",
            use_container_width=True,
            on_click=_run_startup
        )

    # ── ONGLET CHARGEMENT HARMONIQUE ──────────────────────────────────────
    with tab_harm:
        st.markdown(
            '<div class="rl-section-header">Analyse multi-harmonique</div>',
            unsafe_allow_html=True
        )
        st.markdown("""
        <div class="rl-card-info">
          <small>Applique plusieurs harmoniques simultanement
          pour simuler des chargements complexes
          (engrenages, defauts periodiques).</small>
        </div>
        """, unsafe_allow_html=True)

        n_harm = st.slider(
            "Nombre d'harmoniques", 1, 5, 3,
            key="m6_n_harm"
        )

        harm_configs = []
        for i in range(n_harm):
            st.markdown("**Harmonique {} :**".format(i + 1))
            c1, c2, c3 = st.columns(3)
            with c1:
                amp = st.number_input(
                    "Amplitude (N)",
                    0.0, 1e6, 200.0 / (i + 1),
                    key="m6_h_amp_{}".format(i)
                )
            with c2:
                freq = st.number_input(
                    "Frequence (Hz)",
                    0.1, 5000.0,
                    50.0 * (i + 1),
                    key="m6_h_freq_{}".format(i)
                )
            with c3:
                phase = st.slider(
                    "Phase (deg)",
                    0, 360, 0,
                    key="m6_h_phase_{}".format(i)
                )
            harm_configs.append({
                "amp": amp, "freq": freq,
                "phase": np.radians(phase)
            })

        st.session_state["m6_harm_configs"] = harm_configs
        st.slider(
            "Noeud d'observation (multi-harm)",
            0, n_nodes,
            min(2, n_nodes),
            key="m6_harm_node"
        )
        st.slider(
            "Duree (s)", 0.1, 10.0, 2.0,
            key="m6_harm_dur"
        )
        st.slider(
            "Points temporels", 200, 3000, 1000,
            key="m6_harm_npts"
        )

        st.button(
            "Simuler le chargement harmonique",
            type="primary",
            key="m6_run_harm",
            use_container_width=True,
            on_click=_run_harmonic
        )


# =============================================================================
# PANNEAU GRAPHICS
# =============================================================================
def _render_graphics(rotor):
    st.markdown(
        '<div class="rl-graphics-title">'
        'Time Response — Results'
        '</div>',
        unsafe_allow_html=True
    )

    if rotor is None:
        st.info("Construisez un rotor dans M1 pour acceder aux analyses.")
        return

    tab_time, tab_orbit, tab_water, tab_dfft, tab_start = st.tabs([
        "Signal temporel",
        "Orbites",
        "Waterfall 3D",
        "Spectre DFFT",
        "Demarrage"
    ])

    with tab_time:
        _display_time_signal()

    with tab_orbit:
        _display_orbits()

    with tab_water:
        _display_waterfall()

    with tab_dfft:
        _display_dfft()

    with tab_start:
        _display_startup()


# =============================================================================
# CONSTRUCTION DE LA FORCE
# =============================================================================
def _build_force(rotor, t):
    """Construit la matrice de force F(ndof, nt) selon le type de chargement."""
    ndof      = rotor.ndof
    nt        = len(t)
    F         = np.zeros((ndof, nt))
    load_type = st.session_state.get("m6_load_type", "Balourd tournant")
    rpm       = float(st.session_state.get("m6_rpm", 3000))
    omega     = rpm * np.pi / 30

    if load_type == "Balourd tournant":
        mag       = float(st.session_state.get("m6_unb_mag", 0.001))
        node      = int(st.session_state.get("m6_unb_node", 2))
        dof_x     = node * 4
        dof_y     = node * 4 + 1
        force_amp = mag * omega ** 2
        if dof_x < ndof:
            F[dof_x, :] = force_amp * np.cos(omega * t)
        if dof_y < ndof:
            F[dof_y, :] = force_amp * np.sin(omega * t)

    elif load_type == "Force impulsionnelle":
        amp   = float(st.session_state.get("m6_imp_amp",  1000.0))
        node  = int(st.session_state.get("m6_imp_node",   2))
        t0    = float(st.session_state.get("m6_imp_t",    0.1))
        dur   = float(st.session_state.get("m6_imp_dur",  0.01))
        dof_x = node * 4
        mask  = (t >= t0) & (t <= t0 + dur)
        if dof_x < ndof:
            F[dof_x, mask] = amp

    elif load_type == "Force harmonique":
        amp   = float(st.session_state.get("m6_har_amp",  500.0))
        freq  = float(st.session_state.get("m6_har_freq", 50.0))
        node  = int(st.session_state.get("m6_har_node",   2))
        direc = st.session_state.get("m6_har_dir", "X")
        dof_x = node * 4
        dof_y = node * 4 + 1
        f_sig = amp * np.sin(2 * np.pi * freq * t)
        if "X" in direc and dof_x < ndof:
            F[dof_x, :] = f_sig
        if "Y" in direc and dof_y < ndof:
            F[dof_y, :] = f_sig

    # "Aucune force" -> F reste zero
    return F


# =============================================================================
# CALCUL REPONSE TEMPORELLE
# =============================================================================
def _run_temporal():
    rotor = st.session_state.get("rotor")
    if rotor is None:
        return

    rpm   = float(st.session_state.get("m6_rpm",   3000))
    tend  = float(st.session_state.get("m6_tend",  1.0))
    npts  = int(st.session_state.get("m6_npts",    1000))
    omega = rpm * np.pi / 30
    t     = np.linspace(0, tend, npts)
    F     = _build_force(rotor, t)

    try:
        tr = _call_run_time_response(rotor, omega, F, t)
        if tr is not None:
            st.session_state["res_temporal"]     = tr
            st.session_state["m6_t_arr"]         = t
            st.session_state["m6_rpm_computed"]  = rpm
            st.session_state["m6_temporal_error"] = None
            _log("Reponse temporelle calculee ({} pts, {:.0f} RPM)".format(
                npts, rpm), "ok")
        else:
            st.session_state["m6_temporal_error"] = \
                "run_time_response a retourne None."
    except Exception as e:
        st.session_state["m6_temporal_error"] = str(e)
        _log("Erreur temporelle : {}".format(e), "err")


def _call_run_time_response(rotor, omega, F, t):
    """Appel run_time_response avec fallback multi-API."""
    last_err = ""

    # Tentative 1 : API recente (speed, F, t)
    for F_try in [F, F.T]:
        try:
            return rotor.run_time_response(speed=omega, F=F_try, t=t)
        except (TypeError, ValueError) as e:
            last_err = str(e)

    # Tentative 2 : API ancienne (speed, force, time_range)
    for F_try in [F, F.T]:
        try:
            return rotor.run_time_response(
                speed=omega, force=F_try, time_range=t)
        except (TypeError, ValueError) as e:
            last_err = str(e)

    # Tentative 3 : arguments positionnels
    for F_try in [F, F.T]:
        try:
            return rotor.run_time_response(omega, F_try, t)
        except Exception as e:
            last_err = str(e)

    raise RuntimeError("Toutes les tentatives ont echoue : {}".format(last_err))


# =============================================================================
# EXTRACTION REPONSE
# =============================================================================
def _extract_response(tr, t_ref):
    """Extrait (t, response_matrix) depuis l'objet TimeResponse."""
    t_arr = None
    for attr in ("time", "t", "time_range"):
        if hasattr(tr, attr) and getattr(tr, attr) is not None:
            t_arr = np.array(getattr(tr, attr))
            break
    if t_arr is None:
        t_arr = t_ref

    resp = None
    for attr in ("yout", "response", "disp", "y"):
        if hasattr(tr, attr) and getattr(tr, attr) is not None:
            resp = np.array(getattr(tr, attr))
            break

    if resp is None:
        raise AttributeError("Donnees de reponse introuvables.")

    # Transposition si necessaire
    if resp.ndim == 2:
        if resp.shape[0] == len(t_arr) and resp.shape[1] != len(t_arr):
            resp = resp.T
        elif resp.shape[1] == len(t_arr):
            pass  # deja correct
        elif resp.shape[0] != len(t_arr):
            # Essayer la transposee
            if resp.T.shape[1] == len(t_arr):
                resp = resp.T

    return t_arr, resp


# =============================================================================
# CALCUL DEMARRAGE
# =============================================================================
def _run_startup():
    rotor = st.session_state.get("rotor")
    if rotor is None:
        return

    rpm0  = float(st.session_state.get("m6_start_rpm0", 0.0))
    rpmf  = float(st.session_state.get("m6_start_rpmf", 5000.0))
    dur   = float(st.session_state.get("m6_start_dur",  5.0))
    node  = int(st.session_state.get("m6_start_node",   2))
    mag   = float(st.session_state.get("m6_start_unb",  0.001))
    npts  = 1000

    t     = np.linspace(0, dur, npts)
    omega_t = np.linspace(rpm0, rpmf, npts) * np.pi / 30

    # Force balourd avec vitesse variable (sweep lineaire)
    ndof  = rotor.ndof
    F     = np.zeros((ndof, npts))
    dof_x = node * 4
    dof_y = node * 4 + 1
    theta = np.cumsum(omega_t) * (dur / npts)

    if dof_x < ndof:
        F[dof_x, :] = mag * omega_t ** 2 * np.cos(theta)
    if dof_y < ndof:
        F[dof_y, :] = mag * omega_t ** 2 * np.sin(theta)

    # Utiliser vitesse moyenne pour l'integrateur
    omega_avg = (rpm0 + rpmf) / 2 * np.pi / 30

    try:
        tr = _call_run_time_response(rotor, omega_avg, F, t)
        if tr is not None:
            st.session_state["m6_startup_res"]   = tr
            st.session_state["m6_startup_t"]     = t
            st.session_state["m6_startup_omega"] = omega_t
            st.session_state["m6_startup_error"] = None
            _log("Demarrage simule ({:.0f}->{:.0f} RPM, {:.1f}s)".format(
                rpm0, rpmf, dur), "ok")
        else:
            st.session_state["m6_startup_error"] = \
                "run_time_response a retourne None."
    except Exception as e:
        st.session_state["m6_startup_error"] = str(e)
        _log("Erreur demarrage : {}".format(e), "err")


# =============================================================================
# CALCUL HARMONIQUE MULTIPLE
# =============================================================================
def _run_harmonic():
    rotor = st.session_state.get("rotor")
    if rotor is None:
        return

    harm_cfgs = st.session_state.get("m6_harm_configs", [])
    node      = int(st.session_state.get("m6_harm_node", 2))
    dur       = float(st.session_state.get("m6_harm_dur", 2.0))
    npts      = int(st.session_state.get("m6_harm_npts", 1000))
    rpm       = float(st.session_state.get("m6_rpm",     3000))
    omega     = rpm * np.pi / 30
    t         = np.linspace(0, dur, npts)

    ndof  = rotor.ndof
    F     = np.zeros((ndof, npts))
    dof_x = node * 4
    dof_y = node * 4 + 1

    for cfg in harm_cfgs:
        amp   = float(cfg["amp"])
        freq  = float(cfg["freq"])
        phase = float(cfg["phase"])
        f_sig = amp * np.sin(2 * np.pi * freq * t + phase)
        if dof_x < ndof:
            F[dof_x, :] += f_sig
        if dof_y < ndof:
            F[dof_y, :] += f_sig * 0.5

    try:
        tr = _call_run_time_response(rotor, omega, F, t)
        if tr is not None:
            st.session_state["res_temporal"]      = tr
            st.session_state["m6_t_arr"]          = t
            st.session_state["m6_rpm_computed"]   = rpm
            st.session_state["m6_temporal_error"] = None
            _log("Chargement harmonique calcule ({} harm.)".format(
                len(harm_cfgs)), "ok")
        else:
            st.session_state["m6_temporal_error"] = \
                "run_time_response a retourne None."
    except Exception as e:
        st.session_state["m6_temporal_error"] = str(e)
        _log("Erreur harmonique : {}".format(e), "err")


# =============================================================================
# AFFICHAGE SIGNAL TEMPOREL
# =============================================================================
def _display_time_signal():
    if st.session_state.get("m6_temporal_error"):
        st.error("Erreur : {}".format(
            st.session_state["m6_temporal_error"]))

    tr = st.session_state.get("res_temporal")
    if tr is None:
        st.info(
            "Configurez et lancez une simulation dans le panneau Settings."
        )
        return

    t_ref = st.session_state.get("m6_t_arr", np.linspace(0, 1, 1000))
    node  = int(st.session_state.get("m6_node_obs", 2))

    try:
        t_arr, resp = _extract_response(tr, t_ref)
    except Exception as e:
        st.error("Extraction impossible : {}".format(e))
        return

    dof_x  = node * 4
    dof_y  = node * 4 + 1
    ndof   = resp.shape[0] if resp.ndim >= 1 else 0
    safe_x = min(dof_x, ndof - 1)
    safe_y = min(dof_y, ndof - 1)

    x_um = resp[safe_x, :] * 1e6 if resp.ndim == 2 else resp * 1e6
    y_um = resp[safe_y, :] * 1e6 if resp.ndim == 2 and safe_y < ndof else x_um

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=[
            "Deplacement X (µm) — Noeud {}".format(node),
            "Deplacement Y (µm) — Noeud {}".format(node)
        ],
        vertical_spacing=0.10
    )

    fig.add_trace(go.Scatter(
        x=t_arr, y=x_um,
        name="X",
        line=dict(color="#1F5C8B", width=1.5),
        hovertemplate="t=%{x:.4f}s<br>X=%{y:.3f}µm<extra></extra>"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=t_arr, y=y_um,
        name="Y",
        line=dict(color="#C55A11", width=1.5),
        hovertemplate="t=%{x:.4f}s<br>Y=%{y:.3f}µm<extra></extra>"
    ), row=2, col=1)

    fig.update_xaxes(
        title_text="Temps (s)", row=2, col=1,
        showgrid=True, gridcolor="#F0F4FF"
    )
    fig.update_yaxes(showgrid=True, gridcolor="#F0F4FF")
    fig.update_layout(
        height=500,
        title="Reponse temporelle — Noeud {} @ {:.0f} RPM".format(
            node,
            float(st.session_state.get("m6_rpm_computed", 3000))
        ),
        plot_bgcolor="white",
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True, key="m6_time_fig")

    # Metriques
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown("""
    <div class="rl-metric-card">
      <div class="rl-metric-label">Amplitude max X</div>
      <div class="rl-metric-value">{:.3f}</div>
      <div class="rl-metric-unit">µm</div>
    </div>""".format(float(np.max(np.abs(x_um)))),
        unsafe_allow_html=True)
    c2.markdown("""
    <div class="rl-metric-card">
      <div class="rl-metric-label">Amplitude max Y</div>
      <div class="rl-metric-value">{:.3f}</div>
      <div class="rl-metric-unit">µm</div>
    </div>""".format(float(np.max(np.abs(y_um)))),
        unsafe_allow_html=True)
    c3.markdown("""
    <div class="rl-metric-card">
      <div class="rl-metric-label">RMS X</div>
      <div class="rl-metric-value">{:.3f}</div>
      <div class="rl-metric-unit">µm</div>
    </div>""".format(float(np.sqrt(np.mean(x_um ** 2)))),
        unsafe_allow_html=True)
    c4.markdown("""
    <div class="rl-metric-card">
      <div class="rl-metric-label">Duree</div>
      <div class="rl-metric-value">{:.2f}</div>
      <div class="rl-metric-unit">s</div>
    </div>""".format(float(t_arr[-1])),
        unsafe_allow_html=True)

    # Export CSV
    df_exp = pd.DataFrame({
        "Temps (s)":    t_arr,
        "X (µm)":       x_um,
        "Y (µm)":       y_um,
    })
    st.download_button(
        "Export CSV signal temporel",
        data=df_exp.to_csv(index=False).encode(),
        file_name="reponse_temporelle.csv",
        mime="text/csv",
        key="m6_time_csv"
    )


# =============================================================================
# AFFICHAGE ORBITES
# =============================================================================
def _display_orbits():
    tr = st.session_state.get("res_temporal")
    if tr is None:
        st.info("Lancez une simulation pour afficher les orbites.")
        return

    t_ref = st.session_state.get("m6_t_arr", np.linspace(0, 1, 1000))
    rotor = st.session_state.get("rotor")
    if rotor is None:
        return

    n_nodes = len(rotor.nodes) - 1

    # Tentative via methode native ROSS
    try:
        node_obs = int(st.session_state.get("m6_node_obs", 2))
        for method in ["plot_orbit", "plot_orbits"]:
            if hasattr(tr, method):
                fig = getattr(tr, method)(node=node_obs)
                st.plotly_chart(
                    fig, use_container_width=True,
                    key="m6_orbit_native")
                return
    except Exception:
        pass

    # Construction manuelle
    try:
        t_arr, resp = _extract_response(tr, t_ref)
    except Exception as e:
        st.error("Extraction impossible : {}".format(e))
        return

    # Selectionner plusieurs noeuds
    nodes_to_plot = st.multiselect(
        "Noeuds a afficher :",
        list(range(n_nodes + 1)),
        default=[min(1, n_nodes), min(2, n_nodes)],
        key="m6_orbit_nodes"
    )
    if not nodes_to_plot:
        nodes_to_plot = [min(2, n_nodes)]

    # Choix de la fenetre temporelle
    t_start_pct = st.slider(
        "Debut fenetre (%)", 0, 90, 50,
        key="m6_orb_tstart",
        help="Utiliser la seconde moitie pour le regime etabli"
    )
    idx_start = int(t_start_pct / 100 * len(t_arr))

    n_cols = min(len(nodes_to_plot), 3)
    cols   = st.columns(n_cols)

    for i, node in enumerate(nodes_to_plot):
        dof_x  = node * 4
        dof_y  = node * 4 + 1
        ndof   = resp.shape[0]
        safe_x = min(dof_x, ndof - 1)
        safe_y = min(dof_y, ndof - 1)

        x_um = resp[safe_x, idx_start:] * 1e6
        y_um = resp[safe_y, idx_start:] * 1e6

        fig_orb = go.Figure()

        # Orbite coloree par le temps
        fig_orb.add_trace(go.Scatter(
            x=x_um, y=y_um,
            mode="lines",
            line=dict(
                color="#1F5C8B",
                width=1.5
            ),
            name="Orbite N{}".format(node),
            hovertemplate=(
                "X=%{x:.3f}µm<br>"
                "Y=%{y:.3f}µm<extra></extra>"
            )
        ))

        # Point de depart
        if len(x_um) > 0:
            fig_orb.add_trace(go.Scatter(
                x=[x_um[0]], y=[y_um[0]],
                mode="markers",
                marker=dict(size=8, color="#22863A", symbol="circle"),
                name="Debut"
            ))
            fig_orb.add_trace(go.Scatter(
                x=[x_um[-1]], y=[y_um[-1]],
                mode="markers",
                marker=dict(size=8, color="#C00000", symbol="square"),
                name="Fin"
            ))

        # Ellipse de reference (cercle)
        r_max = max(np.max(np.abs(x_um)), np.max(np.abs(y_um)))
        if r_max > 0:
            theta_ref = np.linspace(0, 2 * np.pi, 100)
            fig_orb.add_trace(go.Scatter(
                x=r_max * np.cos(theta_ref),
                y=r_max * np.sin(theta_ref),
                mode="lines",
                line=dict(color="#CCCCCC", width=1, dash="dot"),
                name="Ref. circulaire",
                showlegend=False
            ))

        fig_orb.add_trace(go.Scatter(
            x=[0], y=[0],
            mode="markers",
            marker=dict(size=6, color="#888888", symbol="x"),
            name="Centre"
        ))

        fig_orb.update_layout(
            height=340,
            title="Orbite — Noeud {}".format(node),
            xaxis_title="X (µm)",
            yaxis_title="Y (µm)",
            yaxis_scaleanchor="x",
            plot_bgcolor="white",
            xaxis=dict(
                showgrid=True, gridcolor="#F0F4FF",
                zeroline=True, zerolinecolor="#CCCCCC"
            ),
            yaxis=dict(
                showgrid=True, gridcolor="#F0F4FF",
                zeroline=True, zerolinecolor="#CCCCCC"
            ),
            showlegend=False
        )

        with cols[i % n_cols]:
            st.plotly_chart(
                fig_orb, use_container_width=True,
                key="m6_orbit_{}".format(node)
            )

    # Diagnostic de la forme d'orbite
    st.markdown("---")
    st.markdown("**Interpretation des orbites :**")
    st.markdown("""
    <div class="rl-card-info">
    <small>
    - <strong>Orbite circulaire</strong> : amortissement isotrope,
      paliers symetriques.<br>
    - <strong>Orbite elliptique</strong> : anisotropie des paliers
      (Kxx ≠ Kyy).<br>
    - <strong>Orbite en forme de 8</strong> : composante 2X presente
      (fissure, desalignement).<br>
    - <strong>Orbite chaotique</strong> : non-linearite importante
      (frottement rotor-stator).
    </small>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# AFFICHAGE WATERFALL 3D
# =============================================================================
def _display_waterfall():
    tr = st.session_state.get("res_temporal")
    if tr is None:
        st.info("Lancez une simulation pour afficher le Waterfall 3D.")
        return

    t_ref = st.session_state.get("m6_t_arr", np.linspace(0, 1, 1000))
    node  = int(st.session_state.get("m6_node_obs", 2))
    rpm   = float(st.session_state.get("m6_rpm_computed", 3000))

    try:
        t_arr, resp = _extract_response(tr, t_ref)
    except Exception as e:
        st.error("Extraction impossible : {}".format(e))
        return

    dof_x  = node * 4
    ndof   = resp.shape[0]
    safe_x = min(dof_x, ndof - 1)
    x_um   = resp[safe_x, :] * 1e6 if resp.ndim == 2 else resp * 1e6

    if not SCIPY_OK:
        st.warning("SciPy non disponible — Waterfall 3D desactive.")
        return

    # Calcul du spectrogramme
    dt      = float(t_arr[1] - t_arr[0])
    fs      = 1.0 / dt
    nperseg = min(256, max(32, len(x_um) // 8))

    try:
        f_spec, t_spec, Sxx = scipy_signal.spectrogram(
            x_um, fs,
            nperseg=nperseg,
            noverlap=nperseg // 2,
            window='hann'
        )
    except Exception as e:
        st.error("Erreur spectrogramme : {}".format(e))
        return

    # Filtrage frequentiel
    f_max_plot = min(fs / 2, rpm / 60 * 10)
    valid      = f_spec <= f_max_plot
    f_plot     = f_spec[valid]
    Sxx_plot   = np.abs(Sxx[valid, :])

    if Sxx_plot.max() > 0:
        Sxx_plot = Sxx_plot / Sxx_plot.max()

    # Surface 3D Plotly
    fig = go.Figure(data=[go.Surface(
        x=f_plot,
        y=t_spec,
        z=Sxx_plot.T,
        colorscale="Jet",
        colorbar=dict(title="Amplitude norm."),
        contours=dict(
            z=dict(show=True, usecolormap=True, highlightcolor="limegreen",
                   project_z=True)
        )
    )])

    # Harmoniques 1X, 2X, 3X
    fn_rpm = rpm / 60
    for n, color in [(1, "red"), (2, "orange"), (3, "yellow")]:
        fn = n * fn_rpm
        if fn <= f_max_plot:
            fig.add_trace(go.Scatter3d(
                x=[fn, fn],
                y=[t_spec[0], t_spec[-1]],
                z=[0, 0],
                mode="lines",
                line=dict(color=color, width=3),
                name="{}X = {:.1f} Hz".format(n, fn)
            ))

    fig.update_layout(
        scene=dict(
            xaxis_title="Frequence (Hz)",
            yaxis_title="Temps (s)",
            zaxis_title="Amplitude normalisee",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        ),
        height=560,
        title="Diagramme Cascade (Waterfall 3D) — Noeud {} @ {:.0f} RPM".format(
            node, rpm),
        margin=dict(l=0, r=0, b=0, t=40)
    )

    st.plotly_chart(fig, use_container_width=True, key="m6_waterfall_fig")
    st.caption(
        "Le Waterfall 3D montre l'evolution du spectre de vibration dans "
        "le temps. Les lignes colorees indiquent les harmoniques 1X, 2X, 3X."
    )


# =============================================================================
# AFFICHAGE DFFT (Spectre)
# =============================================================================
def _display_dfft():
    tr = st.session_state.get("res_temporal")
    if tr is None:
        st.info("Lancez une simulation pour afficher le spectre DFFT.")
        return

    # Tentative via methode native ROSS
    try:
        node_obs = int(st.session_state.get("m6_node_obs", 2))
        rpm      = float(st.session_state.get("m6_rpm_computed", 3000))
        for method in ["plot_dfft"]:
            if hasattr(tr, method):
                fig = getattr(tr, method)(
                    probe=[node_obs, 0], rpm=rpm)
                st.plotly_chart(
                    fig, use_container_width=True,
                    key="m6_dfft_native")
                return
    except Exception:
        pass

    # Construction manuelle
    t_ref = st.session_state.get("m6_t_arr", np.linspace(0, 1, 1000))
    node  = int(st.session_state.get("m6_node_obs", 2))
    rpm   = float(st.session_state.get("m6_rpm_computed", 3000))

    try:
        t_arr, resp = _extract_response(tr, t_ref)
    except Exception as e:
        st.error("Extraction impossible : {}".format(e))
        return

    dof_x  = node * 4
    ndof   = resp.shape[0]
    safe_x = min(dof_x, ndof - 1)
    safe_y = min(dof_x + 1, ndof - 1)
    x_um   = resp[safe_x, :] * 1e6
    y_um   = resp[safe_y, :] * 1e6

    dt  = float(t_arr[1] - t_arr[0])
    fs  = 1.0 / dt
    n   = len(x_um)

    # FFT
    X_fft = np.fft.rfft(x_um * np.hanning(n))
    Y_fft = np.fft.rfft(y_um * np.hanning(n))
    freqs = np.fft.rfftfreq(n, d=dt)

    amp_x = 2 * np.abs(X_fft) / n
    amp_y = 2 * np.abs(Y_fft) / n

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=freqs, y=amp_x,
        name="X",
        line=dict(color="#1F5C8B", width=1.5),
        fill="tozeroy",
        fillcolor="rgba(31,92,139,0.1)"
    ))
    fig.add_trace(go.Scatter(
        x=freqs, y=amp_y,
        name="Y",
        line=dict(color="#C55A11", width=1.5),
        fill="tozeroy",
        fillcolor="rgba(197,90,17,0.1)"
    ))

    # Marqueurs harmoniques
    fn_rpm = rpm / 60
    colors_h = ["#E53935", "#FB8C00", "#FDD835", "#43A047"]
    for n_harm, color in enumerate([1, 2, 3, 4], 1):
        fn = n_harm * fn_rpm
        if fn <= fs / 2:
            fig.add_vline(
                x=fn,
                line_dash="dot",
                line_color=color,
                line_width=1.5,
                annotation_text="{}X".format(n_harm),
                annotation_font=dict(color=color, size=10)
            )

    # Modes propres
    modal = st.session_state.get("res_modal")
    if modal is not None:
        for i, wn in enumerate(modal.wn[:4]):
            fn_mode = wn / (2 * np.pi)
            if fn_mode <= fs / 2:
                fig.add_vline(
                    x=fn_mode,
                    line_dash="dot",
                    line_color="#22863A",
                    line_width=1,
                    opacity=0.6,
                    annotation_text="M{}".format(i + 1),
                    annotation_font=dict(color="#22863A", size=9)
                )

    fig.update_layout(
        height=460,
        title="Spectre DFFT — Noeud {} @ {:.0f} RPM".format(node, rpm),
        xaxis_title="Frequence (Hz)",
        yaxis_title="Amplitude (µm)",
        plot_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#F0F4FF"),
        yaxis=dict(showgrid=True, gridcolor="#F0F4FF"),
        legend=dict(
            orientation="h", yanchor="bottom",
            y=1.02, xanchor="right", x=1
        )
    )

    st.plotly_chart(fig, use_container_width=True, key="m6_dfft_fig")

    # Tableau des pics
    st.markdown("**Pics spectraux dominants :**")
    idx_sort = np.argsort(amp_x)[::-1][:10]
    df_peaks = pd.DataFrame({
        "Frequence (Hz)": ["{:.2f}".format(freqs[i]) for i in idx_sort],
        "Amplitude X (µm)": ["{:.4f}".format(amp_x[i]) for i in idx_sort],
        "Amplitude Y (µm)": ["{:.4f}".format(amp_y[i]) for i in idx_sort],
        "Harmonique": [
            "{}X".format(round(freqs[i] / fn_rpm))
            if fn_rpm > 0 and abs(freqs[i] / fn_rpm -
                                   round(freqs[i] / fn_rpm)) < 0.15
            else "—"
            for i in idx_sort
        ],
    })
    st.dataframe(df_peaks, use_container_width=True, hide_index=True)

    # Export
    df_fft = pd.DataFrame({
        "Frequence (Hz)": freqs,
        "Amplitude X (µm)": amp_x,
        "Amplitude Y (µm)": amp_y,
    })
    st.download_button(
        "Export spectre CSV",
        data=df_fft.to_csv(index=False).encode(),
        file_name="spectre_dfft.csv",
        mime="text/csv",
        key="m6_dfft_csv"
    )


# =============================================================================
# AFFICHAGE DEMARRAGE
# =============================================================================
def _display_startup():
    if st.session_state.get("m6_startup_error"):
        st.error("Erreur : {}".format(
            st.session_state["m6_startup_error"]))

    tr = st.session_state.get("m6_startup_res")
    if tr is None:
        st.info("Lancez une simulation de demarrage dans le panneau Settings.")
        return

    t_ref   = st.session_state.get("m6_startup_t",     np.linspace(0, 5, 1000))
    omega_t = st.session_state.get("m6_startup_omega",  np.ones(1000) * 100)
    node    = int(st.session_state.get("m6_start_node", 2))

    try:
        t_arr, resp = _extract_response(tr, t_ref)
    except Exception as e:
        st.error("Extraction impossible : {}".format(e))
        return

    dof_x  = node * 4
    dof_y  = node * 4 + 1
    ndof   = resp.shape[0]
    safe_x = min(dof_x, ndof - 1)
    safe_y = min(dof_y, ndof - 1)
    x_um   = resp[safe_x, :] * 1e6
    y_um   = resp[safe_y, :] * 1e6
    rpm_t  = omega_t * 30 / np.pi

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        subplot_titles=[
            "Vitesse de rotation (RPM)",
            "Deplacement X (µm)",
            "Deplacement Y (µm)"
        ],
        vertical_spacing=0.08
    )

    # Vitesse
    n_min = min(len(t_arr), len(rpm_t))
    fig.add_trace(go.Scatter(
        x=t_arr[:n_min], y=rpm_t[:n_min],
        line=dict(color="#22863A", width=2),
        name="Vitesse (RPM)"
    ), row=1, col=1)

    # Deplacement X
    fig.add_trace(go.Scatter(
        x=t_arr, y=x_um,
        line=dict(color="#1F5C8B", width=1.5),
        name="X (µm)"
    ), row=2, col=1)

    # Deplacement Y
    fig.add_trace(go.Scatter(
        x=t_arr, y=y_um,
        line=dict(color="#C55A11", width=1.5),
        name="Y (µm)"
    ), row=3, col=1)

    fig.update_xaxes(
        title_text="Temps (s)", row=3, col=1,
        showgrid=True, gridcolor="#F0F4FF"
    )
    fig.update_yaxes(showgrid=True, gridcolor="#F0F4FF")
    fig.update_layout(
        height=580,
        title="Reponse transitoire de demarrage — Noeud {}".format(node),
        plot_bgcolor="white",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True, key="m6_startup_fig")

    # Waterfall de demarrage
    if SCIPY_OK and len(x_um) > 64:
        st.markdown("### Waterfall de demarrage")
        dt      = float(t_arr[1] - t_arr[0])
        fs      = 1.0 / dt
        nperseg = min(128, len(x_um) // 8)

        try:
            f_spec, t_spec, Sxx = scipy_signal.spectrogram(
                x_um, fs,
                nperseg=nperseg,
                noverlap=nperseg // 2
            )
            rpm_max  = float(np.max(rpm_t))
            f_max_pl = min(fs / 2, rpm_max / 60 * 8)
            valid    = f_spec <= f_max_pl
            f_plot   = f_spec[valid]
            Sxx_plot = np.abs(Sxx[valid, :])
            if Sxx_plot.max() > 0:
                Sxx_plot /= Sxx_plot.max()

            fig_w = go.Figure(data=[go.Surface(
                x=f_plot, y=t_spec, z=Sxx_plot.T,
                colorscale="Jet"
            )])
            fig_w.update_layout(
                scene=dict(
                    xaxis_title="Frequence (Hz)",
                    yaxis_title="Temps (s)",
                    zaxis_title="Amplitude norm.",
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
                ),
                height=480,
                title="Waterfall — Transitoire de demarrage"
            )
            st.plotly_chart(
                fig_w, use_container_width=True,
                key="m6_start_waterfall")
        except Exception as e:
            st.warning(
                "Waterfall de demarrage non disponible : {}".format(e))


# =============================================================================
# HELPER LOG
# =============================================================================
def _log(message, level="info"):
    try:
        from app import add_log
        add_log(message, level)
    except Exception:
        pass
