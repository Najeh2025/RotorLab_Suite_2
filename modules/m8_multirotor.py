**`modules/m8_multirotor.py`**
```python
import streamlit as st

def render_m8(col_settings, col_graphics):
    with col_settings:
        st.markdown('<div class="rl-settings-title">⚙️ MultiRotor & GearElement</div>',
                    unsafe_allow_html=True)
        st.markdown('<span class="rl-badge rl-badge-new">NEW v2.0</span>',
                    unsafe_allow_html=True)
    with col_graphics:
        st.info("🔧 Module M8 — MultiRotor avec GearElement + Analyse torsionnelle\n\n"
                "Livraison Sprint 5 (Semaine 7).")
```

