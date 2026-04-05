**`modules/m7_faults.py`**
```python
import streamlit as st

def render_m7(col_settings, col_graphics):
    with col_settings:
        st.markdown('<div class="rl-settings-title">🔧 Fault Analysis</div>',
                    unsafe_allow_html=True)
    with col_graphics:
        st.info("🔧 Module M7 — Défauts (Fissure, Désalignement, Frottement)\n\n"
                "Livraison Sprint 5 (Semaine 7).")
```
