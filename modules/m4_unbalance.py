import streamlit as st


def render_m4(col_settings, col_graphics):
    with col_settings:
        st.markdown(
            '<div class="rl-settings-title">Unbalance Response & H(jw)</div>',
            unsafe_allow_html=True
        )
    with col_graphics:
        st.info("Module M4 - Balourd + H(jw). Livraison Sprint 4.")
