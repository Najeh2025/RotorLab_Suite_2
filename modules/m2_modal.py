### `modules/m2_modal.py`
```python
# modules/m2_modal.py — Analyses Statique & Modale
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

try:
    import ross as rs
    ROSS_OK = True
except ImportError:
    ROSS_OK = False


def render_m2(col_settings, col_graphics):
    rotor = st.session_state.get("rotor")

    with col_settings:
        st.markdown('<div class="rl-settings-title">📊 Static & Modal Analysis</div>',
                    unsafe_allow_html=True)
        if rotor is None:
            st.warning("⚠️ Aucun rotor — construisez d'abord un modèle dans M1.")
            return

        st.markdown('<div class="rl-section-header">▼ Analyse statique</div>',
                    unsafe_allow_html=True)
        run_static = st.button("📏 Lancer l'analyse statique",
                               type="primary", key="m2_run_static",
                               use_container_width=True)

        st.markdown('<div class="rl-section-header">▼ Analyse modale</div>',
                    unsafe_allow_html=True)
        speed_rpm = st.slider("Vitesse (RPM)", 0, 15000, 0, key="m2_speed")
        st.caption(f"ω = {speed_rpm * np.pi / 30:.1f} rad/s")
        run_modal = st.button("📊 Calculer les modes propres",
                              type="primary", key="m2_run_modal",
                              use_container_width=True)

        st.markdown('<div class="rl-section-header">▼ Visualisation</div>',
                    unsafe_allow_html=True)
        n_modes_disp = st.slider("Modes à afficher", 1, 10, 6, key="m2_nmodes")

    with col_graphics:
        st.markdown('<div class="rl-graphics-title">📊 Results — Static & Modal</div>',
                    unsafe_allow_html=True)

        tab_stat, tab_modal = st.tabs(["📏 Statique", "🎵 Modal"])

        with tab_stat:
            if run_static:
                with st.spinner("Calcul statique..."):
                    try:
                        static = rotor.run_static()
                        st.session_state["res_static"] = static
                        from app import add_log
                        add_log("Analyse statique terminée", "ok")
                    except Exception as e:
                        st.error(f"Erreur : {e}")

            static = st.session_state.get("res_static")
            if static:
                st.success("✅ Analyse statique disponible")
                plot_choice = st.radio(
                    "Diagramme :",
                    ["📐 Déformée", "🔄 Moment fléchissant",
                     "✂️ Effort tranchant", "⚖️ Corps libre"],
                    horizontal=True, key="m2_plot_choice"
                )
                try:
                    if "Déformée" in plot_choice:
                        st.plotly_chart(static.plot_deformation(),
                                        use_container_width=True)
                    elif "Moment" in plot_choice:
                        st.plotly_chart(static.plot_bending_moment(),
                                        use_container_width=True)
                    elif "Effort" in plot_choice:
                        st.plotly_chart(static.plot_shearing_force(),
                                        use_container_width=True)
                    elif "Corps" in plot_choice:
                        st.plotly_chart(static.plot_free_body_diagram(),
                                        use_container_width=True)
                except Exception as e:
                    st.warning(f"Visualisation : {e}")
            else:
                st.info("Cliquez sur 'Lancer l'analyse statique' dans le panneau Settings.")

        with tab_modal:
            if run_modal:
                with st.spinner("Calcul modal..."):
                    try:
                        modal = rotor.run_modal(
                            speed=float(speed_rpm) * np.pi / 30)
                        st.session_state["res_modal"] = modal
                        st.session_state["df_modal"]  = _modal_table(modal)
                        from app import add_log
                        add_log(f"Modal calculé à {speed_rpm} RPM", "ok")
                    except Exception as e:
                        st.error(f"Erreur : {e}")

            modal = st.session_state.get("res_modal")
            if modal:
                df = st.session_state.get("df_modal", _modal_table(modal))
                st.dataframe(df, use_container_width=True, hide_index=True)

                n_avail = min(n_modes_disp, len(modal.wn))
                mode_i  = st.selectbox(
                    "Mode à visualiser :",
                    range(n_avail),
                    format_func=lambda x:
                        f"Mode {x+1} — {modal.wn[x]/(2*np.pi):.2f} Hz",
                    key="m2_mode_sel"
                )
                for method in ["plot_mode_3d", "plot_mode_shape"]:
                    if hasattr(modal, method):
                        try:
                            st.plotly_chart(
                                getattr(modal, method)(mode=mode_i),
                                use_container_width=True)
                            break
                        except Exception:
                            continue

                st.download_button(
                    "📥 Export CSV fréquences",
                    data=df.to_csv(index=False).encode(),
                    file_name="frequences_modales.csv",
                    mime="text/csv"
                )
            else:
                st.info("Paramétrez et lancez l'analyse modale dans le panneau Settings.")


def _modal_table(modal) -> pd.DataFrame:
    fn  = modal.wn / (2 * np.pi)
    ld  = getattr(modal, 'log_dec', np.zeros(len(fn)))
    n   = min(10, len(fn))
    stab = []
    for v in ld[:n]:
        if   v > 0.3:  stab.append("✅ Très stable")
        elif v > 0.1:  stab.append("🟡 Stable (API 684)")
        elif v > 0:    stab.append("⚠️ Peu amorti")
        else:          stab.append("❌ INSTABLE")
    return pd.DataFrame({
        "Mode":      range(1, n+1),
        "fn (Hz)":   [f"{v:.3f}" for v in fn[:n]],
        "ωn (rad/s)":[f"{v:.2f}" for v in modal.wn[:n]],
        "Log Dec":   [f"{v:.4f}" for v in ld[:n]],
        "Stabilité": stab,
    })
```
