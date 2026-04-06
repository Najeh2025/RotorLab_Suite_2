import streamlit as st


def render_m9(col_settings, col_graphics):
    with col_settings:
        st.markdown(
            '<div class="rl-settings-title">Report & Export</div>',
            unsafe_allow_html=True
        )
    with col_graphics:
        st.info("Module M9 - Rapport PDF professionnel. Livraison Sprint 6.")
