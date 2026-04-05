**`modules/m9_report.py`**
```python
import streamlit as st

def render_m9(col_settings, col_graphics):
    with col_settings:
        st.markdown('<div class="rl-settings-title">📄 Report & Export</div>',
                    unsafe_allow_html=True)
    with col_graphics:
        st.info("🔧 Module M9 — Rapport PDF professionnel\n\n"
                "Livraison Sprint 6 (Semaine 8).")
```

**`tutorials/tutorial_data.py`**
```python
import streamlit as st

def render_tutorials():
    st.subheader("🎓 Mode Pédagogique")
    st.info("Les tutoriels seront migrés depuis RotorLab Suite 1.0 au Sprint 6.")
```
