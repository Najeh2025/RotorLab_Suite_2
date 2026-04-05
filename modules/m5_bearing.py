**`modules/m5_bearing.py`**
```python
import streamlit as st

def render_m5(col_settings, col_graphics):
    with col_settings:
        st.markdown('<div class="rl-settings-title">💧 Fluid Film Bearings</div>',
                    unsafe_allow_html=True)
        st.markdown('<span class="rl-badge rl-badge-new">NEW — Sprint 4</span>',
                    unsafe_allow_html=True)
    with col_graphics:
        st.info("🔧 Module M5 — Paliers hydrodynamiques (BearingFluidFilm)\n\n"
                "Livraison Sprint 4 (Semaine 6).")
```

