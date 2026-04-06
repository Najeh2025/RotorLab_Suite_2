import streamlit as st

st.set_page_config(page_title="Diagnostic", layout="wide")
st.title("Diagnostic RotorLab Suite 2.0")

# Test 1 — imports de base
st.subheader("1. Imports de base")
try:
    import numpy as np
    st.success("numpy OK")
except Exception as e:
    st.error("numpy : {}".format(e))

try:
    import pandas as pd
    st.success("pandas OK")
except Exception as e:
    st.error("pandas : {}".format(e))

try:
    import plotly
    st.success("plotly OK")
except Exception as e:
    st.error("plotly : {}".format(e))

try:
    import ross as rs
    st.success("ROSS OK — version {}".format(rs.__version__))
except Exception as e:
    st.error("ROSS : {}".format(e))

# Test 2 — config.py
st.subheader("2. config.py")
try:
    from config import APP_NAME, APP_VERSION, MATERIALS_DB, MODEL_TREE
    st.success("config.py OK — APP_NAME = {}".format(APP_NAME))
except Exception as e:
    st.error("config.py : {}".format(e))

# Test 3 — styles/theme.css
st.subheader("3. styles/theme.css")
from pathlib import Path
if Path("styles/theme.css").exists():
    st.success("theme.css trouvé")
else:
    st.warning("theme.css absent — vérifiez le dossier styles/")

# Test 4 — modules
st.subheader("4. Modules")
modules = [
    "modules.m1_builder",
    "modules.m2_modal",
    "modules.m3_campbell",
    "modules.m4_unbalance",
    "modules.m5_bearing",
    "modules.m6_temporal",
    "modules.m7_faults",
    "modules.m8_multirotor",
    "modules.m9_report",
    "modules.ai_copilot",
    "tutorials.tutorial_data",
]
for mod in modules:
    try:
        __import__(mod)
        st.success("{} OK".format(mod))
    except Exception as e:
        st.error("{} : {}".format(mod, e))

st.info("Diagnostic terminé. Copiez les erreurs et partagez-les.")
