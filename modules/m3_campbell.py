### Stubs pour les modules restants

Créez ces fichiers **exactement comme suit** (ils s'affichent proprement sans crasher, on les complète sprint par sprint) :

**`modules/m3_campbell.py`**
```python
import streamlit as st

def render_m3(col_settings, col_graphics):
    with col_settings:
        st.markdown('<div class="rl-settings-title">📈 Campbell + UCS + API Level 1</div>',
                    unsafe_allow_html=True)
        st.markdown('<span class="rl-badge rl-badge-new">En cours de développement — Sprint 3</span>',
                    unsafe_allow_html=True)
    with col_graphics:
        st.info("🔧 Module M3 — Campbell + UCS Map + API 684 Level 1\n\n"
                "Ce module sera livré au Sprint 3 (Semaine 5).")
```
