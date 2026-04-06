import streamlit as st


def render_m7(col_settings, col_graphics):
    with col_settings:
        st.markdown(
            '<div class="rl-settings-title">Fault Analysis</div>',
            unsafe_allow_html=True
        )
    with col_graphics:
        st.info("Module M7 - Defauts (Fissure, Desalignement, Frottement). Livraison Sprint 5.")
