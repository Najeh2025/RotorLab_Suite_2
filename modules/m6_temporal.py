import streamlit as st


def render_m6(col_settings, col_graphics):
    with col_settings:
        st.markdown(
            '<div class="rl-settings-title">Time Response</div>',
            unsafe_allow_html=True
        )
    with col_graphics:
        st.info("Module M6 - Reponse temporelle + Waterfall 3D. Livraison Sprint 5.")
