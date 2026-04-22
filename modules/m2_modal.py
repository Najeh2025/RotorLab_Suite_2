# modules/m2_modal.py — Analyses Statique & Modale
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
import streamlit as st
import numpy as np
import pandas as pd

try:
    import ross as rs
    ROSS_OK = True
except ImportError:
    ROSS_OK = False


def render_m2(col_settings, col_graphics):
    """Module M2 — Analyses Statique et Modale."""
    rotor = st.session_state.get("rotor")

    with col_settings:
        _render_settings_m2(rotor)

    with col_graphics:
        _render_graphics_m2(rotor)


# =============================================================================
# PANNEAU SETTINGS
# =============================================================================
def _render_settings_m2(rotor):
    st.markdown(
        '<div class="rl-settings-title">📊 Static & Modal Analysis</div>',
        unsafe_allow_html=True
    )

    if rotor is None:
        st.warning("Aucun rotor — construisez d'abord un modèle dans M1.")
        return

    # Analyse statique
    st.markdown(
        '<div class="rl-section-header">▼ Analyse statique</div>',
        unsafe_allow_html=True
    )
    st.caption("Déflexion par gravité, réactions aux paliers, efforts internes.")
    run_static = st.button(
        "📏 Lancer l'analyse statique",
        type="primary",
        key="m2_run_static",
        use_container_width=True
    )

    # Analyse modale
    st.markdown(
        '<div class="rl-section-header">▼ Analyse modale</div>',
        unsafe_allow_html=True
    )
    speed_rpm = st.number_input(
        "Vitesse de rotation (RPM)",
        min_value=0,
        max_value=15000,
        value=0,
        step=100,
        key="m2_speed"
    )
    st.caption(
        "Ω = {:.1f} rad/s".format(speed_rpm * np.pi / 30)
    )

    # Options d'affichage — AVANT le bouton pour que la valeur soit disponible
    # au moment du clic sur "Calculer les modes propres"
    st.markdown(
        '<div class="rl-section-header">▼ Options d\'affichage</div>',
        unsafe_allow_html=True
    )
    n_modes_disp = st.number_input(
        "Nombre de modes à afficher",
        min_value=1,
        max_value=24,          # augmenté de 12 → 24
        value=6,
        step=1,
        key="m2_nmodes"
    )

    run_modal = st.button(
        "📊 Calculer les modes propres",
        type="primary",
        key="m2_run_modal",
        use_container_width=True
    )

    # Lancement des calculs
    if run_static:
        _run_static(rotor)

    if run_modal:
        _run_modal(rotor, speed_rpm, int(n_modes_disp))


# =============================================================================
# PANNEAU GRAPHICS
# =============================================================================
def _render_graphics_m2(rotor):
    st.markdown(
        '<div class="rl-graphics-title">📊 Results — Static & Modal</div>',
        unsafe_allow_html=True
    )

    if rotor is None:
        st.info("Construisez un rotor dans M1 puis lancez les analyses.")
        return

    tab_stat, tab_modal = st.tabs(
        ["📏 Analyse Statique", "🎵 Analyse Modale"]
    )

    with tab_stat:
        _display_static()

    with tab_modal:
        _display_modal()


# =============================================================================
# CALCULS
# =============================================================================
def _run_static(rotor):
    with st.spinner("Calcul statique en cours..."):
        try:
            static = rotor.run_static()
            st.session_state["res_static"] = static
            _log("Analyse statique terminée", "ok")
        except Exception as e:
            st.error("Erreur analyse statique : {}".format(e))


def _run_modal(rotor, speed_rpm, n_modes):
    """Lance run_modal en demandant au moins n_modes modes à ROSS."""
    with st.spinner("Calcul modal en cours..."):
        try:
            speed_rad = float(speed_rpm) * np.pi / 30

            # ROSS retourne les valeurs propres par paires conjuguées (FW+BW)
            # puis filtre pour ne garder que les fréquences positives uniques.
            # Ratio x4 nécessaire pour obtenir n_modes modes utiles après filtrage.
            # On plafonne à ndof-1 (limite du solveur sparse).
            ndof = rotor.ndof
            num_req = min(max(n_modes * 4, 24), ndof - 1)
            try:
                modal = rotor.run_modal(speed=speed_rad, num_modes=num_req)
            except TypeError:
                # Ancienne API : pas de num_modes
                modal = rotor.run_modal(speed=speed_rad)

            st.session_state["res_modal"]         = modal
            st.session_state["m2_nmodes_computed"] = n_modes
            st.session_state["df_modal"]           = _build_modal_table(modal, n_modes)
            _log("Modes propres calculés à {} RPM ({} modes demandés)".format(
                speed_rpm, n_modes), "ok")
        except Exception as e:
            st.error("Erreur analyse modale : {}".format(e))


# =============================================================================
# AFFICHAGE STATIQUE
# =============================================================================
def _display_static():
    static = st.session_state.get("res_static")

    if static is None:
        st.info(
            "Cliquez sur **Lancer l'analyse statique** dans le panneau Settings."
        )
        return

    st.success("Analyse statique disponible.")

    plot_choice = st.radio(
        "Diagramme à afficher :",
        [
            "Corps libre",
            "Effort tranchant",
            "Moment fléchissant",
            "Déformée de l'arbre"
        ],
        horizontal=True,
        key="m2_stat_plot"
    )

    try:
        fig = None
        if plot_choice == "Déformée de l'arbre":
            fig = static.plot_deformation()
        elif plot_choice == "Moment fléchissant":
            fig = static.plot_bending_moment()
        elif plot_choice == "Effort tranchant":
            fig = static.plot_shearing_force()
        elif plot_choice == "Corps libre":
            fig = static.plot_free_body_diagram()

        if fig is not None:
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True, key="m2_stat_fig")

    except Exception as e:
        st.warning("Visualisation non disponible : {}".format(e))


# =============================================================================
# AFFICHAGE MODAL
# =============================================================================
def _display_modal():
    modal = st.session_state.get("res_modal")

    if modal is None:
        st.info(
            "Configurez la vitesse et cliquez sur "
            "**Calculer les modes propres** dans le panneau Settings."
        )
        return

    # Nombre de modes demandé au dernier calcul
    n_modes_disp = int(st.session_state.get("m2_nmodes_computed",
                       st.session_state.get("m2_nmodes", 6)))

    # Nombre de modes réellement disponibles dans l'objet ROSS
    n_available = len(modal.wn)

    # Nombre de modes à afficher (ce que l'utilisateur a demandé,
    # plafonné par ce que ROSS a réellement calculé)
    n_show = min(n_modes_disp, n_available)

    # Information si ROSS n'a pas pu fournir assez de modes
    if n_available < n_modes_disp:
        st.info(
            "ℹ️ {} modes demandés, {} modes disponibles "
            "(limite du modèle EF ou du solveur).".format(
                n_modes_disp, n_available)
        )

    # Tableau — reconstruit si le nombre demandé a changé
    df = st.session_state.get("df_modal")
    if df is None or len(df) != n_show:
        df = _build_modal_table(modal, n_show)
        st.session_state["df_modal"] = df

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Visualisation d'un mode
    if n_show < 1:
        st.warning("Aucun mode disponible.")
        return

    mode_i = st.selectbox(
        "Mode à visualiser :",
        list(range(n_show)),
        format_func=lambda x: "Mode {} — {:.2f} Hz".format(
            x + 1, modal.wn[x] / (2 * np.pi)
        ),
        key="m2_mode_sel"
    )

    # Tentative d'affichage 3D puis 2D
    plotted = False
    for method_name in ["plot_mode_3d", "plot_mode_shape"]:
        if hasattr(modal, method_name):
            try:
                fig = getattr(modal, method_name)(mode=mode_i)
                fig.update_layout(height=420)
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key="m2_mode_fig"
                )
                plotted = True
                break
            except Exception:
                continue

    if not plotted:
        st.info("Visualisation du mode non disponible pour cette version de ROSS.")

    # Export CSV
    st.markdown("---")
    st.download_button(
        label="📥 Exporter les fréquences (CSV)",
        data=df.to_csv(index=False).encode(),
        file_name="frequences_modales.csv",
        mime="text/csv",
        key="m2_csv_export"
    )


# =============================================================================
# HELPERS
# =============================================================================
def _build_modal_table(modal, n: int = 6):
    """Construit le DataFrame de résultats modaux pour les n premiers modes."""
    fn = modal.wn / (2 * np.pi)
    ld = getattr(modal, 'log_dec', np.zeros(len(fn)))

    # Plafonner au nombre de modes réellement disponibles
    n = min(n, len(fn))

    stability = []
    for v in ld[:n]:
        if v > 0.3:
            stability.append("Très Stable")
        elif v > 0.1:
            stability.append("Stable (API 684)")
        elif v > 0:
            stability.append("Peu Amorti")
        else:
            stability.append("INSTABLE")

    return pd.DataFrame({
        "Mode":       list(range(1, n + 1)),
        "fn (Hz)":    ["{:.3f}".format(v) for v in fn[:n]],
        "wn (rad/s)": ["{:.2f}".format(v) for v in modal.wn[:n]],
        "Log Dec":    ["{:.4f}".format(v) for v in ld[:n]],
        "Stabilité":  stability,
    })


def _log(message, level="info"):
    """Ajoute un message au log de l'application."""
    try:
        from app import add_log
        add_log(message, level)
    except Exception:
        pass
