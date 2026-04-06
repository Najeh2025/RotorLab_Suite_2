import streamlit as st


def render_m5(col_settings, col_graphics):
    with col_settings:
        st.markdown(
            '<div class="rl-settings-title">Fluid Film Bearings</div>',
            unsafe_allow_html=True
        )
    with col_graphics:
        st.info("Module M5 - Paliers hydrodynamiques. Livraison Sprint 4.")

