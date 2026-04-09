# modules/m7_faults.py — Analyse de Defauts
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
# Couvre : Fissure (Gasch/Mayes), Desalignement, Frottement, Diagnostic
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
def render_m7(col_settings, col_graphics):
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
        '<div class="rl-settings-title">Fault Analysis</div>',
        unsafe_allow_html=True
    )

    if rotor is None:
        st.warning("Aucun rotor — construisez d'abord un modele dans M1.")
        return

    n_nodes = len(rotor.nodes) - 1

    tab_crack, tab_mis, tab_rub, tab_diag = st.tabs([
        "Fissure (Crack)",
        "Desalignement",
        "Frottement (Rub)",
        "Diagnostic"
    ])

    # ── FISSURE ──────────────────────────────────────────────────────────
    with tab_crack:
        st.markdown(
            '<div class="rl-section-header">Fissure transversale</div>',
            unsafe_allow_html=True
        )
        st.markdown("""
        <div class="rl-card-info">
          <small>Modeles de Gasch et Mayes — variation periodique de la
          raideur de l arbre fissuré. Signature caracteristique : harmonique
          2X et amplification a la demi-vitesse critique.</small>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.slider(
                "Profondeur relative (alpha = a/R)",
                0.0, 0.9, 0.3, step=0.05,
                key="m7_crack_depth",
                help="Ratio profondeur/rayon. > 0.5 = critique."
            )
            st.slider(
                "Noeud de la fissure",
                1, max(1, n_nodes - 1),
                max(1, n_nodes // 2),
                key="m7_crack_node"
            )
        with c2:
            st.radio(
                "Modele de fissure",
                ["Gasch", "Mayes"],
                key="m7_crack_model",
                help="Gasch = respirante | Mayes = lineaire"
            )
            st.number_input(
                "Vitesse de rotation (RPM)",
                100.0, 10000.0, 1500.0,
                key="m7_crack_rpm"
            )

        st.slider(
            "Magnitude balourd (kg.m)",
            1e-5, 0.01, 1e-4,
            format="%.5f",
            key="m7_crack_unb"
        )
        st.slider(
            "Noeud d'observation",
            0, n_nodes,
            min(2, n_nodes),
            key="m7_crack_obs"
        )

        st.button(
            "Simuler la fissure",
            type="primary",
            key="m7_run_crack",
            use_container_width=True,
            on_click=_run_crack
        )

    # ── DESALIGNEMENT ─────────────────────────────────────────────────────
    with tab_mis:
        st.markdown(
            '<div class="rl-section-header">Desalignement d accouplement</div>',
            unsafe_allow_html=True
        )
        st.markdown("""
        <div class="rl-card-info">
          <small>Paralléle : décalage lateral des axes.<br>
          Angulaire : angle entre les axes.<br>
          Signature : harmoniques 2X (parallele) ou 1X+2X+3X (angulaire).</small>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.radio(
                "Type de desalignement",
                ["Parallele", "Angulaire"],
                key="m7_mis_type",
                horizontal=True
            )
            st.number_input(
                "Valeur du desalignement (m ou rad)",
                1e-5, 0.1, 0.001,
                format="%.5f",
                key="m7_mis_val"
            )
        with c2:
            st.slider(
                "Noeud de l accouplement",
                1, max(1, n_nodes - 1),
                max(1, n_nodes // 2),
                key="m7_mis_node"
            )
            st.number_input(
                "Vitesse de rotation (RPM)",
                100.0, 10000.0, 3000.0,
                key="m7_mis_rpm"
            )

        c1, c2 = st.columns(2)
        with c1:
            st.number_input(
                "Raideur radiale accouplement (N/m)",
                1e4, 1e9, 5e7,
                format="%.2e",
                key="m7_mis_krad"
            )
        with c2:
            st.number_input(
                "Raideur en flexion (N/m)",
                1e4, 1e9, 5e7,
                format="%.2e",
                key="m7_mis_kbend"
            )

        st.slider(
            "Noeud d'observation",
            0, n_nodes,
            min(2, n_nodes),
            key="m7_mis_obs"
        )

        st.button(
            "Simuler le desalignement",
            type="primary",
            key="m7_run_mis",
            use_container_width=True,
            on_click=_run_misalignment
        )

    # ── FROTTEMENT ────────────────────────────────────────────────────────
    with tab_rub:
        st.markdown(
            '<div class="rl-section-header">Frottement rotor-stator (Rubbing)</div>',
            unsafe_allow_html=True
        )
        st.markdown("""
        <div class="rl-card-info">
          <small>Contact non-lineaire rotor-stator. Genere des
          sous-harmoniques (0.5X, 0.33X) et peut conduire a
          un comportement chaotique.</small>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.number_input(
                "Jeu radial rotor-stator (µm)",
                10.0, 1000.0, 100.0,
                key="m7_rub_gap",
                help="Jeu en microns"
            )
            st.number_input(
                "Raideur de contact (N/m)",
                1e4, 1e10, 1e7,
                format="%.2e",
                key="m7_rub_k"
            )
        with c2:
            st.number_input(
                "Coefficient de frottement",
                0.0, 1.0, 0.1,
                key="m7_rub_mu"
            )
            st.slider(
                "Noeud de contact",
                1, max(1, n_nodes - 1),
                max(1, n_nodes // 2),
                key="m7_rub_node"
            )

        st.number_input(
            "Vitesse de rotation (RPM)",
            100.0, 10000.0, 3000.0,
            key="m7_rub_rpm"
        )
        st.slider(
            "Noeud d'observation",
            0, n_nodes,
            min(2, n_nodes),
            key="m7_rub_obs"
        )

        st.button(
            "Simuler le frottement",
            type="primary",
            key="m7_run_rub",
            use_container_width=True,
            on_click=_run_rubbing
        )

    # ── DIAGNOSTIC ────────────────────────────────────────────────────────
    with tab_diag:
        st.markdown(
            '<div class="rl-section-header">Tableau de diagnostic</div>',
            unsafe_allow_html=True
        )
        st.markdown("""
        <div class="rl-card-info">
          <small>Compare les signatures vibratoires des trois defauts
          et aide a l'identification du defaut probable.</small>
        </div>
        """, unsafe_allow_html=True)
        st.info(
            "Lancez au moins deux simulations de defauts pour "
            "activer le diagnostic comparatif."
        )


# =============================================================================
# PANNEAU GRAPHICS
# =============================================================================
def _render_graphics(rotor):
    st.markdown(
        '<div class="rl-graphics-title">Fault Analysis — Results</div>',
        unsafe_allow_html=True
    )

    if rotor is None:
        st.info("Construisez un rotor dans M1 pour acceder aux analyses.")
        return

    tab_crack, tab_mis, tab_rub, tab_diag = st.tabs([
        "Fissure",
        "Desalignement",
        "Frottement",
        "Diagnostic compare"
    ])

    with tab_crack:
        _display_fault_results("crack")

    with tab_mis:
        _display_fault_results("mis")

    with tab_rub:
        _display_fault_results("rub")

    with tab_diag:
        _display_diagnostic()


# =============================================================================
# CALCULS DEFAUTS
# =============================================================================
def _run_crack():
    rotor = st.session_state.get("rotor")
    if rotor is None or not ROSS_OK:
        return

    depth  = float(st.session_state.get("m7_crack_depth", 0.3))
    node   = int(st.session_state.get("m7_crack_node",
                                       max(1, len(rotor.nodes) // 2)))
    model  = st.session_state.get("m7_crack_model", "Gasch").lower()
    rpm    = float(st.session_state.get("m7_crack_rpm",   1500.0))
    unb    = float(st.session_state.get("m7_crack_unb",   1e-4))
    speed  = rpm * np.pi / 30
    t_arr  = np.linspace(0, 2.0, 1000)

    try:
        # Tentative 1 : API recente
        res = rotor.run_crack(
            n=node,
            depth_ratio=depth,
            model=model,
            node=[node],
            unbalance_magnitude=[unb],
            unbalance_phase=[0.0],
            speed=speed,
            t=t_arr
        )
    except Exception as e1:
        try:
            # Tentative 2 : ancienne API
            res = rotor.run_crack(
                crack_node=node,
                crack_depth=depth,
                model=model,
                speed=speed
            )
        except Exception as e2:
            st.session_state["m7_crack_error"] = (
                "API recente : {} | API ancienne : {}".format(e1, e2)
            )
            _log("Erreur fissure : {}".format(e1), "err")
            return

    st.session_state["m7_crack_res"]   = res
    st.session_state["m7_crack_t"]     = t_arr
    st.session_state["m7_crack_error"] = None
    _log("Fissure simulee (alpha={:.2f}, N={}, {:.0f} RPM)".format(
        depth, node, rpm), "ok")


def _run_misalignment():
    rotor = st.session_state.get("rotor")
    if rotor is None or not ROSS_OK:
        return

    node   = int(st.session_state.get("m7_mis_node",
                                       max(1, len(rotor.nodes) // 2)))
    val    = float(st.session_state.get("m7_mis_val",   0.001))
    m_type = st.session_state.get("m7_mis_type", "Parallele")
    rpm    = float(st.session_state.get("m7_mis_rpm",   3000.0))
    krad   = float(st.session_state.get("m7_mis_krad",  5e7))
    kbend  = float(st.session_state.get("m7_mis_kbend", 5e7))
    speed  = rpm * np.pi / 30
    t_arr  = np.linspace(0, 2.0, 1000)
    m_en   = "parallel" if "arall" in m_type else "angular"

    try:
        res = rotor.run_misalignment(
            n=node,
            node=[node],
            unbalance_magnitude=[1e-4],
            unbalance_phase=[0.0],
            t=t_arr,
            speed=speed,
            coupling="flex",
            mis_type=m_en,
            mis_distance_x=val if m_en == "parallel" else 0.0,
            mis_distance_y=0.0,
            mis_angle=val if m_en == "angular" else 0.0,
            radial_stiffness=krad,
            bending_stiffness=kbend
        )
    except Exception as e1:
        try:
            res = rotor.run_misalignment(
                node=[node],
                unbalance_magnitude=[1e-4],
                unbalance_phase=[0.0],
                t=t_arr,
                mis_type=m_en,
                misalignment=val,
                speed=speed
            )
        except Exception as e2:
            st.session_state["m7_mis_error"] = (
                "API recente : {} | API ancienne : {}".format(e1, e2)
            )
            _log("Erreur desalignement : {}".format(e1), "err")
            return

    st.session_state["m7_mis_res"]   = res
    st.session_state["m7_mis_t"]     = t_arr
    st.session_state["m7_mis_error"] = None
    _log("Desalignement simule ({}, {:.0f} RPM)".format(m_type, rpm), "ok")


def _run_rubbing():
    rotor = st.session_state.get("rotor")
    if rotor is None or not ROSS_OK:
        return

    node     = int(st.session_state.get("m7_rub_node",
                                         max(1, len(rotor.nodes) // 2)))
    gap_m    = float(st.session_state.get("m7_rub_gap", 100.0)) * 1e-6
    k_cont   = float(st.session_state.get("m7_rub_k",   1e7))
    mu       = float(st.session_state.get("m7_rub_mu",  0.1))
    rpm      = float(st.session_state.get("m7_rub_rpm", 3000.0))
    speed    = rpm * np.pi / 30
    t_arr    = np.linspace(0, 2.0, 1000)

    try:
        res = rotor.run_rubbing(
            n=node,
            distance=gap_m,
            contact_stiffness=k_cont,
            contact_damping=0.0,
            friction_coeff=mu,
            node=[node],
            unbalance_magnitude=[1e-4],
            unbalance_phase=[0.0],
            speed=speed,
            t=t_arr
        )
    except Exception as e1:
        try:
            res = rotor.run_rubbing(
                n=node,
                contact_stiffness=k_cont,
                radial_clearance=gap_m,
                speed=speed
            )
        except Exception as e2:
            st.session_state["m7_rub_error"] = (
                "API recente : {} | API ancienne : {}".format(e1, e2)
            )
            _log("Erreur frottement : {}".format(e1), "err")
            return

    st.session_state["m7_rub_res"]   = res
    st.session_state["m7_rub_t"]     = t_arr
    st.session_state["m7_rub_error"] = None
    _log("Frottement simule (jeu={:.0f}µm, {:.0f} RPM)".format(
        gap_m * 1e6, rpm), "ok")


# =============================================================================
# AFFICHAGE RESULTATS DEFAUTS
# =============================================================================
def _display_fault_results(fault_key):
    """Affichage unifie pour les trois types de defauts."""

    error_key = "m7_{}_error".format(fault_key)
    res_key   = "m7_{}_res".format(fault_key)
    t_key     = "m7_{}_t".format(fault_key)
    obs_key   = "m7_{}_obs".format(fault_key)
    rpm_key   = "m7_{}_rpm".format(fault_key)

    fault_names = {
        "crack": "Fissure transversale",
        "mis":   "Desalignement",
        "rub":   "Frottement rotor-stator"
    }
    fault_name = fault_names.get(fault_key, fault_key)

    if st.session_state.get(error_key):
        st.error("Erreur : {}".format(st.session_state[error_key]))
        st.markdown("""
        <div class="rl-card-warn">
          <strong>Note :</strong> run_{}() peut ne pas etre disponible
          dans toutes les versions de ROSS. Verifiez votre version
          avec <code>import ross; print(ross.__version__)</code>.
        </div>
        """.format(fault_key), unsafe_allow_html=True)
        _show_fault_theory(fault_key)
        return

    res = st.session_state.get(res_key)
    if res is None:
        st.info(
            "Configurez et lancez la simulation '{}' "
            "dans le panneau Settings.".format(fault_name)
        )
        _show_fault_theory(fault_key)
        return

    t_ref = st.session_state.get(t_key, np.linspace(0, 2, 1000))
    node  = int(st.session_state.get(obs_key, 2))
    rpm   = float(st.session_state.get(rpm_key, 3000.0))

    # Extraction robuste
    t_arr, resp = _extract_response_fault(res, t_ref)
    if t_arr is None or resp is None:
        st.warning("Donnees de reponse non disponibles.")
        _show_fault_theory(fault_key)
        return

    dof_x  = node * 4
    dof_y  = node * 4 + 1
    ndof   = resp.shape[0] if resp.ndim >= 1 else 1
    safe_x = min(dof_x, ndof - 1)
    safe_y = min(dof_y, ndof - 1)
    x_um   = resp[safe_x, :] * 1e6 if resp.ndim == 2 else resp * 1e6
    y_um   = resp[safe_y, :] * 1e6 if resp.ndim == 2 and safe_y < ndof \
             else x_um

    # Sous-onglets
    sub1, sub2, sub3, sub4 = st.tabs([
        "Signal temporel",
        "Orbite",
        "Spectre FFT",
        "Theorie du defaut"
    ])

    with sub1:
        _plot_time_signal(t_arr, x_um, y_um, node, rpm, fault_name)

    with sub2:
        _plot_orbit(x_um, y_um, node, rpm, fault_name)

    with sub3:
        _plot_spectrum(t_arr, x_um, y_um, rpm, fault_key, fault_name)

    with sub4:
        _show_fault_theory(fault_key)


# =============================================================================
# EXTRACTION REPONSE DEFAUT
# =============================================================================
def _extract_response_fault(res, t_ref):
    """Extrait t_arr et resp depuis un objet de reponse de defaut."""
    t_arr = None
    for attr in ("time", "t", "time_range"):
        if hasattr(res, attr) and getattr(res, attr) is not None:
            t_arr = np.array(getattr(res, attr))
            break
    if t_arr is None:
        t_arr = t_ref

    resp = None
    for attr in ("yout", "response", "disp", "y"):
        if hasattr(res, attr) and getattr(res, attr) is not None:
            resp = np.array(getattr(res, attr))
            break

    if resp is None:
        return None, None

    if resp.ndim == 2:
        if resp.shape[0] == len(t_arr) and resp.shape[1] != len(t_arr):
            resp = resp.T

    return t_arr, resp


# =============================================================================
# GRAPHIQUES COMMUNS
# =============================================================================
def _plot_time_signal(t_arr, x_um, y_um, node, rpm, title):
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=[
            "Deplacement X (µm)", "Deplacement Y (µm)"
        ],
        vertical_spacing=0.10
    )
    fig.add_trace(go.Scatter(
        x=t_arr, y=x_um,
        line=dict(color="#1F5C8B", width=1.5),
        name="X"
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=t_arr, y=y_um,
        line=dict(color="#C55A11", width=1.5),
        name="Y"
    ), row=2, col=1)

    fig.update_xaxes(
        title_text="Temps (s)", row=2, col=1,
        showgrid=True, gridcolor="#F0F4FF"
    )
    fig.update_yaxes(showgrid=True, gridcolor="#F0F4FF")
    fig.update_layout(
        height=450,
        title="{} — Noeud {} @ {:.0f} RPM".format(title, node, rpm),
        plot_bgcolor="white"
    )
    st.plotly_chart(fig, use_container_width=True,
                    key="m7_{}_time".format(title[:3]))

    c1, c2, c3 = st.columns(3)
    c1.markdown("""
    <div class="rl-metric-card">
      <div class="rl-metric-label">Amax X</div>
      <div class="rl-metric-value">{:.3f}</div>
      <div class="rl-metric-unit">µm</div>
    </div>""".format(float(np.max(np.abs(x_um)))),
        unsafe_allow_html=True)
    c2.markdown("""
    <div class="rl-metric-card">
      <div class="rl-metric-label">Amax Y</div>
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

    df_exp = pd.DataFrame({
        "Temps (s)": t_arr,
        "X (µm)":    x_um,
        "Y (µm)":    y_um
    })
    st.download_button(
        "Export CSV",
        data=df_exp.to_csv(index=False).encode(),
        file_name="defaut_{}.csv".format(title[:5]),
        mime="text/csv",
        key="m7_csv_{}".format(title[:5])
    )


def _plot_orbit(x_um, y_um, node, rpm, title):
    # Utiliser la seconde moitie (regime etabli)
    idx_start = len(x_um) // 2
    x_plot    = x_um[idx_start:]
    y_plot    = y_um[idx_start:]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_plot, y=y_plot,
        mode="lines",
        line=dict(color="#1F5C8B", width=1.5),
        name="Orbite"
    ))
    if len(x_plot) > 0:
        fig.add_trace(go.Scatter(
            x=[x_plot[0]], y=[y_plot[0]],
            mode="markers",
            marker=dict(size=8, color="#22863A"),
            name="Debut"
        ))

    fig.add_trace(go.Scatter(
        x=[0], y=[0],
        mode="markers",
        marker=dict(size=6, color="#C00000", symbol="x"),
        name="Centre"
    ))

    fig.update_layout(
        height=420,
        title="Orbite — {} — Noeud {}".format(title, node),
        xaxis_title="X (µm)",
        yaxis_title="Y (µm)",
        yaxis_scaleanchor="x",
        plot_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#F0F4FF", zeroline=True),
        yaxis=dict(showgrid=True, gridcolor="#F0F4FF", zeroline=True)
    )
    st.plotly_chart(fig, use_container_width=True,
                    key="m7_{}_orbit".format(title[:3]))


def _plot_spectrum(t_arr, x_um, y_um, rpm, fault_key, title):
    """Spectre FFT avec marqueurs des harmoniques caracteristiques."""
    n    = len(x_um)
    dt   = float(t_arr[1] - t_arr[0]) if len(t_arr) > 1 else 0.001
    fs   = 1.0 / dt

    X_fft = np.fft.rfft(x_um * np.hanning(n))
    freqs = np.fft.rfftfreq(n, d=dt)
    amp_x = 2 * np.abs(X_fft) / n

    Y_fft = np.fft.rfft(y_um * np.hanning(n))
    amp_y = 2 * np.abs(Y_fft) / n

    fn_rpm = rpm / 60

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
        fillcolor="rgba(197,90,17,0.08)"
    ))

    # Harmoniques caracteristiques selon le defaut
    harm_colors = {
        "crack": {
            0.5: ("#7B1FA2", "0.5X"),
            1.0: ("#E53935", "1X"),
            2.0: ("#FF6D00", "2X*"),
            3.0: ("#FB8C00", "3X"),
        },
        "mis": {
            1.0: ("#E53935", "1X"),
            2.0: ("#FF6D00", "2X*"),
            3.0: ("#FB8C00", "3X*"),
        },
        "rub": {
            0.5:  ("#7B1FA2", "0.5X*"),
            0.33: ("#9C27B0", "0.33X"),
            1.0:  ("#E53935", "1X"),
            2.0:  ("#FB8C00", "2X"),
        }
    }

    harmonics = harm_colors.get(fault_key, {})
    for ratio, (color, label) in harmonics.items():
        fn = ratio * fn_rpm
        if 0 < fn < fs / 2:
            fig.add_vline(
                x=fn,
                line_dash="dot" if "*" not in label else "solid",
                line_color=color,
                line_width=2 if "*" in label else 1,
                annotation_text=label,
                annotation_font=dict(color=color, size=11)
            )

    fig.update_layout(
        height=420,
        title="Spectre FFT — {} @ {:.0f} RPM".format(title, rpm),
        xaxis_title="Frequence (Hz)",
        yaxis_title="Amplitude (µm)",
        plot_bgcolor="white",
        xaxis=dict(
            showgrid=True, gridcolor="#F0F4FF",
            range=[0, min(fs / 2, fn_rpm * 8)]
        ),
        yaxis=dict(showgrid=True, gridcolor="#F0F4FF"),
        legend=dict(
            orientation="h", yanchor="bottom",
            y=1.02, xanchor="right", x=1
        )
    )
    st.plotly_chart(fig, use_container_width=True,
                    key="m7_{}_fft".format(fault_key))

    # Tableau des pics
    idx_sort = np.argsort(amp_x)[::-1][:8]
    rows = []
    for i in idx_sort:
        f_i    = freqs[i]
        ratio  = f_i / fn_rpm if fn_rpm > 0 else 0
        # Identification harmonique
        harm_label = "—"
        for r in [0.33, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]:
            if abs(ratio - r) < 0.12:
                harm_label = "{:.2f}X".format(r)
                break
        rows.append({
            "Frequence (Hz)":   "{:.2f}".format(f_i),
            "Amplitude X (µm)": "{:.5f}".format(amp_x[i]),
            "Amplitude Y (µm)": "{:.5f}".format(amp_y[i]),
            "Harmonique":       harm_label,
        })
    st.markdown("**Pics spectraux dominants :**")
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )


# =============================================================================
# THEORIE DES DEFAUTS
# =============================================================================
def _show_fault_theory(fault_key):
    theories = {
        "crack": {
            "title": "Fissure transversale — Theorie",
            "content": """
**Modeles de fissure :**
- **Gasch (1976)** : modele respirant (breathing crack).
  La fissure s'ouvre et se ferme periodiquement au cours de la rotation,
  generant une variation de raideur non-lineaire.
- **Mayes & Davies (1984)** : approximation lineaire de la variation
  de raideur. Plus simple, utilisé pour les petites fissures (alpha < 0.3).

**Parametres caracteristiques :**
- **alpha = a/R** : ratio profondeur/rayon (0 = sain, 0.9 = critique)
- **Noeud de fissure** : position le long de l'arbre

**Signatures vibratoires :**
- Harmonique **2X** dominant (variation de raideur 2 fois/tour)
- Amplification 1X et 2X a la **demi-vitesse critique** (0.5 x Vc)
- Orbites en forme de **8** au lieu d'ellipses
- Evolution lente des amplitudes avec la profondeur

**Risque selon alpha :**
| alpha | Effet | Surveillance |
|-------|-------|--------------|
| < 0.1 | Negligeable | Annuelle |
| 0.1 - 0.3 | Detectable | Mensuelle |
| 0.3 - 0.5 | Significatif | Continue |
| > 0.5 | Critique | Arret immediat |
            """
        },
        "mis": {
            "title": "Desalignement — Theorie",
            "content": """
**Types de desalignement :**
- **Parallele** : decalage lateral des axes de rotation. Genere des forces
  radiales periodiques a chaque tour.
- **Angulaire** : angle entre les axes. Genere des moments de flexion.
- **Combine** : melange des deux, le plus frequent en pratique.

**Mecanisme :**
Le desalignement cree des forces et moments periodiques a travers
l'accouplement. Ces forces excitent les modes du rotor et generent
des harmoniques caracteristiques.

**Signatures vibratoires :**
- Desalignement parallele : forte composante **2X**
- Desalignement angulaire : composantes **1X + 2X + 3X**
- Phase axiale souvent plus significative que radiale
- Augmentation des vibrations avec la charge

**Limites de desalignement typiques :**
| Type accouplement | Limite parallele | Limite angulaire |
|-------------------|------------------|------------------|
| Flexible (elastomere) | 0.5 mm | 1 deg |
| Disque flexible | 0.1 mm | 0.3 deg |
| Accouplement rigide | 0.05 mm | 0.1 deg |
            """
        },
        "rub": {
            "title": "Frottement rotor-stator — Theorie",
            "content": """
**Mecanisme du rubbing :**
Le contact intermittent entre le rotor et le stator se produit quand
l'amplitude vibratoire depasse le jeu radial.
Ce contact est fortement non-lineaire et peut generer :

**Regimes vibratoires :**
1. **Regime periodique** : contact regulier -> sous-harmoniques 0.5X, 0.33X
2. **Regime quasi-periodique** : battements entre modes
3. **Regime chaotique** : amplitudes irregulières, spectre continu

**Signatures vibratoires :**
- **Sous-harmoniques** : 0.5X (le plus frequent), 0.33X, 0.25X
- **Sidelobes** autour de 1X
- Augmentation brutale du niveau vibratoire global
- Orbites deformees, non-elliptiques

**Facteurs influents :**
- Jeu radial (plus petit = rubbing plus facile)
- Raideur de contact (rigidite du stator)
- Coefficient de frottement
- Vitesse de rotation (sous-critique = rebond, supercritique = accrochage)

**Vitesse de rubbing instable :**
Le rubbing instable (accrochage) se produit generalement
quand omega > 0.5 x omega_critique.
            """
        }
    }

    th = theories.get(fault_key, {})
    if not th:
        return

    st.markdown("### {}".format(th["title"]))
    st.markdown(th["content"])


# =============================================================================
# DIAGNOSTIC COMPARE
# =============================================================================
def _display_diagnostic():
    """Tableau de diagnostic compare des trois defauts."""
    crack_res = st.session_state.get("m7_crack_res")
    mis_res   = st.session_state.get("m7_mis_res")
    rub_res   = st.session_state.get("m7_rub_res")

    available = []
    if crack_res is not None:
        available.append("crack")
    if mis_res is not None:
        available.append("mis")
    if rub_res is not None:
        available.append("rub")

    if len(available) < 1:
        st.info(
            "Lancez au moins une simulation de defaut "
            "pour activer le diagnostic."
        )
        _show_diagnostic_table()
        return

    # Tableau de signatures caracteristiques
    _show_diagnostic_table()

    if len(available) < 2:
        st.info(
            "Lancez au moins deux simulations pour "
            "la comparaison spectrale."
        )
        return

    # Comparaison spectrale
    st.markdown("### Comparaison spectrale des defauts simules")

    fault_map = {
        "crack": ("m7_crack_res", "m7_crack_t",
                  "m7_crack_obs", "m7_crack_rpm",
                  "Fissure", "#1F5C8B"),
        "mis":   ("m7_mis_res",   "m7_mis_t",
                  "m7_mis_obs",   "m7_mis_rpm",
                  "Desalignement", "#C55A11"),
        "rub":   ("m7_rub_res",   "m7_rub_t",
                  "m7_rub_obs",   "m7_rub_rpm",
                  "Frottement", "#22863A"),
    }

    fig = go.Figure()

    for fk in available:
        res_k, t_k, obs_k, rpm_k, label, color = fault_map[fk]
        res   = st.session_state.get(res_k)
        t_ref = st.session_state.get(t_k, np.linspace(0, 2, 1000))
        node  = int(st.session_state.get(obs_k, 2))
        rpm   = float(st.session_state.get(rpm_k, 3000.0))

        t_arr, resp = _extract_response_fault(res, t_ref)
        if t_arr is None or resp is None:
            continue

        dof_x  = node * 4
        ndof   = resp.shape[0] if resp.ndim >= 1 else 1
        safe_x = min(dof_x, ndof - 1)
        x_um   = resp[safe_x, :] * 1e6 if resp.ndim == 2 else resp * 1e6

        n    = len(x_um)
        dt   = float(t_arr[1] - t_arr[0]) if len(t_arr) > 1 else 0.001
        X_ff = np.fft.rfft(x_um * np.hanning(n))
        fqs  = np.fft.rfftfreq(n, d=dt)
        amp  = 2 * np.abs(X_ff) / n

        fig.add_trace(go.Scatter(
            x=fqs, y=amp,
            name=label,
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor=color.replace("#", "rgba(") + ",0.08)"
                      if "#" in color else "rgba(0,0,0,0.05)"
        ))

    # Harmoniques
    rpm_ref  = float(st.session_state.get("m7_crack_rpm", 3000.0))
    fn_rpm   = rpm_ref / 60
    for ratio, label in [(0.5, "0.5X"), (1.0, "1X"),
                         (2.0, "2X"), (3.0, "3X")]:
        fn = ratio * fn_rpm
        fig.add_vline(
            x=fn,
            line_dash="dot",
            line_color="#888888",
            line_width=1,
            annotation_text=label,
            annotation_font=dict(color="#888888", size=10)
        )

    fig.update_layout(
        height=460,
        title="Comparaison spectrale — Fissure vs Desalignement vs Frottement",
        xaxis_title="Frequence (Hz)",
        yaxis_title="Amplitude (µm)",
        plot_bgcolor="white",
        xaxis=dict(
            showgrid=True, gridcolor="#F0F4FF",
            range=[0, fn_rpm * 8]
        ),
        yaxis=dict(showgrid=True, gridcolor="#F0F4FF"),
        legend=dict(
            orientation="h", yanchor="bottom",
            y=1.02, xanchor="right", x=1
        )
    )
    st.plotly_chart(fig, use_container_width=True, key="m7_diag_comp")


def _show_diagnostic_table():
    """Tableau de reference des signatures vibratoires."""
    st.markdown("### Guide de diagnostic vibratoire")

    data = {
        "Defaut":      ["Balourd", "Fissure", "Desalignement",
                        "Frottement", "Instabilite fluide"],
        "1X":          ["Fort", "Modere", "Modere", "Present", "Croissant"],
        "2X":          ["Faible", "Fort*", "Fort*", "Present", "Faible"],
        "0.5X / Sub":  ["Absent", "Absent", "Absent", "Fort*", "Present*"],
        "3X+":         ["Faible", "Faible", "Present", "Present", "Faible"],
        "Orbite":      ["Ellipse", "Forme 8", "Ellipse aplatie",
                        "Irreguliere", "Circulaire croissante"],
        "Phase":       ["Stable", "Variable", "Axiale elevee",
                        "Irreguliere", "Derive"],
        "Indicateur cle": [
            "A_1X proportionnel a omega^2",
            "Pic 2X a 0.5*Vc",
            "Fort axial, 2X parallele",
            "Sous-harmoniques 0.5X",
            "Frequence 0.47*omega"
        ]
    }

    df_diag = pd.DataFrame(data)
    st.dataframe(df_diag, use_container_width=True, hide_index=True)

    st.markdown("""
    <div class="rl-card-info">
    <strong>Legende :</strong> * = indicateur caracteristique du defaut.<br>
    La combinaison de plusieurs indicateurs permet l'identification fiable.
    Une analyse en phase et la comparaison temporelle sont essentielles
    pour confirmer le diagnostic.
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# HELPER LOG
# =============================================================================
def _log(message, level="info"):
    try:
        from app import add_log
        add_log(message, level)
    except Exception:
        pass
