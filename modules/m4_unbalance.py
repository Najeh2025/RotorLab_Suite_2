**`modules/m4_unbalance.py`**
```python
import streamlit as st

def render_m4(col_settings, col_graphics):
    with col_settings:
        st.markdown('<div class="rl-settings-title">🌀 Unbalance Response & H(jω)</div>',
                    unsafe_allow_html=True)
        st.markdown('<span class="rl-badge rl-badge-new">En cours — Sprint 4</span>',
                    unsafe_allow_html=True)
    with col_graphics:
        st.info("🔧 Module M4 — Balourd + H(jω)\n\nLivraison Sprint 4 (Semaine 6).")
```
