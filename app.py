# =============================================================================
# RotorLab Suite 2.0 — Application principale
# Pr. Najeh Ben Guedria — ISTLS, Université de Sousse
# =============================================================================

import streamlit as st
import numpy as np
import pandas as pd
from pathlib import Path

from config import APP_NAME, APP_VERSION, APP_AUTHOR, APP_INST, MODEL_TREE
# En haut du fichier
#from simulation_layout import render_simulation_mode  # ← remplace l'ancienne

# Rien d'autre à changer — route_to_module et render_model_tree restent inchangés
try:
    import ross as rs
    ROSS_AVAILABLE = True
    ROSS_VERSION   = getattr(rs, '__version__', 'unknown')
except ImportError:
    ROSS_AVAILABLE = False
    ROSS_VERSION   = "non installé"

# =============================================================================
# CONFIGURATION PAGE
# =============================================================================
st.set_page_config(
    page_title=APP_NAME,
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# CSS
# =============================================================================
def load_css():
    css_path = Path("styles/theme.css")
    if css_path.exists():
        with open(css_path) as f:
            st.markdown("<style>{}</style>".format(f.read()),
                        unsafe_allow_html=True)

load_css()

# =============================================================================
# SESSION STATE
# =============================================================================
def init_session_state():
    defaults = {
        "active_node"   : "material",
        "active_module" : "M1",
        "nav_mode"      : "dashboard",
        "rotor"         : None,
        "rotor_name"    : "Nouveau rotor",
        "rotor_source"  : None,
        "df_shaft"      : _default_shaft(),
        "df_disk"       : _default_disk(),
        "df_bear"       : _default_bearing(),
        "mat_name"      : "Acier standard (AISI 1045)",
        "res_static"    : None,
        "res_modal"     : None,
        "res_campbell"  : None,
        "res_ucs"       : None,
        "res_unbalance" : None,
        "res_freq"      : None,
        "res_temporal"  : None,
        "df_modal"      : None,
        "df_campbell"   : None,
        "df_api"        : None,
        "api_params"    : None,
        "img_rotor"     : None,
        "img_campbell"  : None,
        "log_messages"  : [],
        "user_name"     : "Utilisateur",
        "chat_history"  : [],
        "tut_done"      : set(),
        "badges"        : {},
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def _default_shaft():
    return pd.DataFrame([
        {"L (m)": 0.20, "id_L (m)": 0.0, "od_L (m)": 0.05,
         "id_R (m)": 0.0, "od_R (m)": 0.05}
        for _ in range(5)
    ])

def _default_disk():
    return pd.DataFrame([
        {"nœud": 2, "Masse (kg)": 15.12,
         "Id (kg.m²)": 0.025, "Ip (kg.m²)": 0.047}
    ])

def _default_bearing():
    return pd.DataFrame([
        {"nœud": 0, "Type": "Palier",
         "kxx": 1e6, "kyy": 1e6, "kxy": 0.0, "cxx": 0.0, "cyy": 0.0},
        {"nœud": 5, "Type": "Palier",
         "kxx": 1e6, "kyy": 1e6, "kxy": 0.0, "cxx": 0.0, "cyy": 0.0},
    ])

init_session_state()

# =============================================================================
# UTILITAIRES
# =============================================================================
def add_log(message, level="info"):
    from datetime import datetime
    ts   = datetime.now().strftime("%H:%M:%S")
    icon = {"info":"ℹ️","ok":"✅","warn":"⚠️","err":"❌"}.get(level,"ℹ️")
    st.session_state["log_messages"].append(
        {"ts": ts, "icon": icon, "msg": message, "level": level}
    )
    if len(st.session_state["log_messages"]) > 20:
        st.session_state["log_messages"] = \
            st.session_state["log_messages"][-20:]

def navigate_to(node_id, module):
    st.session_state["active_node"]   = node_id
    st.session_state["active_module"] = module

def set_nav_mode(mode):
    st.session_state["nav_mode"] = mode

def get_rotor_status():
    r = st.session_state.get("rotor")
    if r is None:
        return "Aucun rotor", "#C00000"
    name = st.session_state.get("rotor_name", "Rotor")
    return "{} · {} nœuds · {:.1f} kg".format(
        name, len(r.nodes), r.m), "#22863A"

# =============================================================================
# CALLBACKS (on_click — sans st.rerun())
# =============================================================================
def _cb_tree(node_id, module):
    st.session_state["active_node"]   = node_id
    st.session_state["active_module"] = module

    # Mise à jour directe du sélecteur d'onglet M1
    # (st.radio ignore index= si la clé existe déjà en session)
    _node_to_tab = {
        "material"  : "🧱 Matériau",
        "parameters": "🧱 Matériau",
        "shaft"     : "📏 Arbre",
        "disks"     : "💿 Disques",
        "bearings"  : "⚙️ Paliers",
    }
    if node_id in _node_to_tab:
        st.session_state["m1_tab_selector"] = _node_to_tab[node_id]

def _cb_load_compressor():
    if not ROSS_AVAILABLE:
        add_log("ROSS non disponible", "err")
        return
    try:
        comp = rs.compressor_example()
        st.session_state["rotor"]        = comp
        st.session_state["rotor_name"]   = "Compresseur centrifuge (ROSS)"
        st.session_state["rotor_source"] = "compressor"
        st.session_state["active_node"]   = "shaft"
        st.session_state["active_module"] = "M1"
        st.session_state["nav_mode"]      = "simulation"

        # Synchronisation tableaux M1
        st.session_state["df_shaft"] = pd.DataFrame([
            {"L (m)": el.L, "id_L (m)": el.idl, "od_L (m)": el.odl,
             "id_R (m)": el.idr, "od_R (m)": el.odr}
            for el in comp.shaft_elements
        ])
        st.session_state["df_disk"] = pd.DataFrame([
            {"nœud": d.n, "Masse (kg)": d.m,
             "Id (kg.m²)": d.Id, "Ip (kg.m²)": d.Ip}
            for d in comp.disk_elements
        ])
        bear_data = []
        for b in comp.bearing_elements:
            def _get(attr):
                v = getattr(b, attr, 0)
                return float(v[0]) if hasattr(v, '__iter__') else float(v)
            bear_data.append({
                "nœud": b.n, "Type": "Palier",
                "kxx": _get("kxx"), "kyy": _get("kyy"),
                "kxy": _get("kxy"), "cxx": _get("cxx"), "cyy": _get("cyy")
            })
        st.session_state["df_bear"] = pd.DataFrame(bear_data)

        # Réinitialiser les résultats
        for key in ["res_static","res_modal","res_campbell","res_ucs",
                    "res_unbalance","res_freq","res_temporal"]:
            st.session_state[key] = None

        add_log("Compresseur chargé : {} nœuds, {:.1f} kg".format(
            len(comp.nodes), comp.m), "ok")

    except Exception as e:
        add_log("Erreur compresseur : {}".format(e), "err")
        st.error("Impossible de charger le compresseur : {}".format(e))

def _cb_reset_model():
    for key in ["rotor","res_static","res_modal","res_campbell","res_ucs",
                "res_unbalance","res_freq","res_temporal"]:
        st.session_state[key] = None
    st.session_state["rotor_name"] = "Nouveau rotor"
    add_log("Modèle réinitialisé", "warn")

def _cb_open_module(node, module):
    st.session_state["active_node"]   = node
    st.session_state["active_module"] = module
    st.session_state["nav_mode"]      = "simulation"

# =============================================================================
# HEADER
# =============================================================================
def render_header():
    rotor_label, rotor_color = get_rotor_status()
    ross_label = "ROSS {}".format(ROSS_VERSION) if ROSS_AVAILABLE \
                 else "ROSS absent"
    st.markdown("""
    <div class="rl-header">
      <div>
        <span class="rl-header-title">⚙️ {name}</span>
        <span style="color:rgba(255,255,255,0.4);margin:0 8px;">|</span>
        <span class="rl-header-sub">{author} — {inst}</span>
      </div>
      <div style="display:flex;gap:8px;align-items:center;">
        <span class="rl-header-badge">v{ver}</span>
        <span class="rl-header-badge">{ross}</span>
        <span class="rl-header-badge">{rotor}</span>
      </div>
    </div>
    """.format(
        name=APP_NAME, author=APP_AUTHOR, inst=APP_INST,
        ver=APP_VERSION, ross=ross_label, rotor=rotor_label
    ), unsafe_allow_html=True)

# =============================================================================
# NAVIGATION
# =============================================================================
def render_top_nav():
    mode = st.session_state["nav_mode"]
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("🏠 Tableau de Bord",
                     use_container_width=True,
                     type="primary" if mode == "dashboard" else "secondary",
                     key="nav_dash"):
            st.session_state["nav_mode"] = "dashboard"
            st.rerun()

    with c2:
        if st.button("🔬 Mode Simulation",
                     use_container_width=True,
                     type="primary" if mode == "simulation" else "secondary",
                     key="nav_sim"):
            st.session_state["nav_mode"] = "simulation"
            st.rerun()

    with c3:
        if st.button("🎓 Mode Pédagogique",
                     use_container_width=True,
                     type="primary" if mode == "tutorial" else "secondary",
                     key="nav_tut"):
            st.session_state["nav_mode"] = "tutorial"
            st.rerun()

    with c4:
        if st.button("✨ SmartRotor Copilot",
                     use_container_width=True,
                     type="primary" if mode == "copilot" else "secondary",
                     key="nav_cop"):
            st.session_state["nav_mode"] = "copilot"
            st.rerun()
# =============================================================================
# MODEL TREE
# =============================================================================
# =========================================================
# COPIER-COLLER CE BLOC DANS app.py
# Remplace UNIQUEMENT la fonction render_model_tree()
# Aucune autre fonction n'est modifiée
# =========================================================

# =============================================================================
# SNIPPET — Remplace UNIQUEMENT render_model_tree() dans app.py
# Aucune autre fonction n'est modifiée.
# =============================================================================

def render_model_tree():
    active = st.session_state.get("active_node", "shaft")

    # ── CSS ciblé : uniquement le panneau arbre ───────────────────────────
    st.markdown("""
    <style>
    /* ════════════════════════════════════════════════════════════════════
       TITRES DE SECTIONS — Bleu profond et lisible
       ════════════════════════════════════════════════════════════════════ */
    .rl-tree-section {
        display        : flex;
        align-items    : center;
        gap            : 8px;
        padding        : 12px 8px;
        font-size      : 0.85em;
        font-weight    : 800;
        color          : #1E3A8A;
        text-transform : uppercase;
        letter-spacing : 0.08em;
        border-left    : 4px solid #1E3A8A;
        background     : rgba(30, 58, 138, 0.04);
        border-radius  : 0 4px 4px 0;
        margin         : 12px 0 8px 0;
        user-select    : none;
    }

    /* ════════════════════════════════════════════════════════════════════
       ITEMS — boutons secondaires dans le panneau arbre
       ═══════════════════════════════════════════════════════════════════ */
    div[data-testid="stVerticalBlock"]
        div[data-testid="stButton"]
        > button[kind="secondary"] {
        text-align       : left           !important;
        justify-content  : flex-start     !important;
        font-size        : 0.90em         !important;
        font-weight      : 500            !important;
        background       : transparent    !important;
        border           : none           !important;
        border-left      : 3px solid transparent !important;
        border-radius    : 0 6px 6px 0    !important;
        padding          : 10px 12px      !important;
        margin           : 2px 0          !important;
        box-shadow       : none           !important;
        color            : #334155        !important;
        letter-spacing   : 0.01em         !important;
        transition       : all 0.15s ease !important;
    }
    div[data-testid="stVerticalBlock"]
        div[data-testid="stButton"]
        > button[kind="secondary"]:hover {
        background       : #F1F5F9        !important;
        border-left-color: #3B82F6        !important;
        color            : #0F172A        !important;
        transform        : translateX(2px) !important;
    }

    /* ════════════════════════════════════════════════════════════════════
       SÉPARATEUR INTERNE
       ════════════════════════════════════════════════════════════════════ */
    .rl-tree-sep {
        height     : 2px;
        background : linear-gradient(90deg, rgba(30,58,138,0.2) 0%, rgba(30,58,138,0.05) 100%);
        margin     : 16px 8px;
        border-radius: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Rendu de l'arbre ──────────────────────────────────────────────────
    for section in MODEL_TREE:
        st.markdown(
            f'<div class="rl-tree-section">{section["label"]}</div>',
            unsafe_allow_html=True,
        )

        for item in section["children"]:
            is_active = (item["id"] == active)
            is_new    = item["module"] in ("M5", "M8")
            new_tag   = " · NEW" if is_new else ""

            if is_active:
                # Élément actif : rendu HTML avec bleu vif (f-string sécurisé)
                st.markdown(
                    f'<div style="'
                    f'background: #3B82F6;'
                    f'color: #FFFFFF;'
                    f'font-weight: 700;'
                    f'padding: 10px 12px;'
                    f'border-radius: 6px;'
                    f'margin: 2px 0;'
                    f'box-shadow: 0 2px 4px rgba(59,130,246,0.3);'
                    f'font-size: 0.90em;'
                    f'letter-spacing: 0.01em;'
                    f'">{item["icon"]}&nbsp;&nbsp;{item["label"]}{new_tag}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.button(
                    f"{item['icon']}  {item['label']}{new_tag}",
                    key=f"tree_{item['id']}",
                    use_container_width=True,
                    on_click=_cb_tree,
                    args=(item["id"], item["module"]),
                )

    # ── Séparateur + Bouton Réinitialiser ─────────────────────────────────
    if st.session_state.get("rotor") is not None:
        st.markdown('<div class="rl-tree-sep"></div>', unsafe_allow_html=True)
        st.button(
            "🗑️  Réinitialiser le modèle",
            use_container_width=True,
            key="tree_reset",
            on_click=_cb_reset_model,
        )
# =============================================================================
# LOG BAR
# =============================================================================
def render_log_bar():
    logs = st.session_state.get("log_messages", [])
    if not logs:
        st.markdown(
            '<div class="rl-log-bar">▶ RotorLab Suite 2.0 — Prêt.</div>',
            unsafe_allow_html=True)
        return
    lines = ""
    for log in logs[-3:]:
        css = {"ok":"rl-log-ok","warn":"rl-log-warn",
               "err":"rl-log-err"}.get(log["level"], "")
        lines += '<span class="{}">{} [{}] {}</span><br>'.format(
            css, log["icon"], log["ts"], log["msg"])
    st.markdown('<div class="rl-log-bar">{}</div>'.format(lines),
                unsafe_allow_html=True)

# =============================================================================
# ROUTAGE MODULES
# =============================================================================
def route_to_module(module_id, node_id, col_settings, col_graphics):
    if module_id == "M1" or node_id in (
            "material","parameters","shaft","disks","bearings"):
        from modules.m1_builder import render_m1
        render_m1(col_settings, col_graphics)

    elif module_id == "M2" or node_id == "static_modal":
        from modules.m2_modal import render_m2
        render_m2(col_settings, col_graphics)

    elif module_id == "M3" or node_id in ("campbell","api_level1"):
        from modules.m3_campbell import render_m3
        render_m3(col_settings, col_graphics)

    elif module_id == "M4" or node_id in ("unbalance","freq_resp"):
        from modules.m4_unbalance import render_m4
        render_m4(col_settings, col_graphics)

    elif module_id == "M5" or node_id == "hd_bearings":
        from modules.m5_bearing import render_m5
        render_m5(col_settings, col_graphics)

    elif module_id == "M6" or node_id == "temporal":
        from modules.m6_temporal import render_m6
        render_m6(col_settings, col_graphics)

    elif module_id == "M7" or node_id == "faults":
        from modules.m7_faults import render_m7
        render_m7(col_settings, col_graphics)

    elif module_id == "M8" or node_id == "multirotor":
        from modules.m8_multirotor import render_m8
        render_m8(col_settings, col_graphics)

    elif module_id == "M9" or node_id == "report":
        from modules.m9_report import render_m9
        render_m9(col_settings, col_graphics)

    elif module_id == "AI" or node_id == "copilot":
        from modules.ai_copilot import render_copilot
        render_copilot(col_settings, col_graphics)

    else:
        from modules.m1_builder import render_m1
        render_m1(col_settings, col_graphics)

# =============================================================================
# MODES
# =============================================================================
# =============================================================================
# simulation_layout.py — Mode Simulation corrigé
# Les div HTML n'encapsulent PAS les widgets Streamlit → on cible les colonnes
# directement par CSS data-testid, et on ajoute les en-têtes séparément.
# =============================================================================

import streamlit as st


# =============================================================================
# CSS — Styler les colonnes Streamlit via data-testid (sans wrappers HTML)
# =============================================================================
def _inject_simulation_panel_css():
    st.markdown("""
    <style>

    /* ── Cibler les 5 colonnes du layout simulation ─────────────────────
       col_tree=0, col_sep1=1, col_settings=2, col_sep2=3, col_graphics=4  */

    /* --- Colonne ARBRE (index 0) ---------------------------------------- */
    section[data-testid="stMain"]
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="column"]:nth-child(1)
        > div[data-testid="stVerticalBlock"] {
        background      : #0F1923;
        border-radius   : 10px 0 0 10px;
        min-height      : 80vh;
        padding         : 0 6px 16px 6px;
        border-right    : none;
    }
    /* Texte clair dans panneau arbre */
    section[data-testid="stMain"]
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="column"]:nth-child(1)
        div[data-testid="stMarkdownContainer"] p,
    section[data-testid="stMain"]
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="column"]:nth-child(1)
        div[data-testid="stMarkdownContainer"] span {
        color : #CBD5E0 !important;
    }
    section[data-testid="stMain"]
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="column"]:nth-child(1)
        button[kind="secondary"] {
        background  : rgba(31,92,139,.30) !important;
        color       : #E2EAF4 !important;
        border      : 1px solid rgba(31,92,139,.55) !important;
        font-size   : .78em !important;
        border-radius: 5px !important;
    }
    section[data-testid="stMain"]
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="column"]:nth-child(1)
        button[kind="secondary"]:hover {
        background   : rgba(31,92,139,.60) !important;
        border-color : #93C5FD !important;
        color        : white !important;
    }

    /* --- Colonne SÉPARATEUR 1 (index 2 → nth-child(2)) ------------------ */
    section[data-testid="stMain"]
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="column"]:nth-child(2)
        > div[data-testid="stVerticalBlock"] {
        background : linear-gradient(
            180deg,
            transparent 0%,
            #1F5C8B 10%,
            #1F5C8B 90%,
            transparent 100%
        );
        min-height  : 80vh;
        width       : 4px !important;
        padding     : 0 !important;
        box-shadow  : 0 0 12px rgba(31,92,139,.40);
    }

    /* --- Colonne PARAMÈTRES (index 3 → nth-child(3)) -------------------- */
    section[data-testid="stMain"]
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="column"]:nth-child(3)
        > div[data-testid="stVerticalBlock"] {
        background    : #F7F9FC;
        min-height    : 80vh;
        padding       : 0 10px 16px 10px;
        border-left   : none;
        border-right  : none;
    }

    /* --- Colonne SÉPARATEUR 2 (index 4 → nth-child(4)) ------------------ */
    section[data-testid="stMain"]
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="column"]:nth-child(4)
        > div[data-testid="stVerticalBlock"] {
        background : linear-gradient(
            180deg,
            transparent 0%,
            #22863A 10%,
            #22863A 90%,
            transparent 100%
        );
        min-height  : 80vh;
        width       : 4px !important;
        padding     : 0 !important;
        box-shadow  : 0 0 12px rgba(34,134,58,.35);
    }

    /* --- Colonne GRAPHIQUES (index 5 → nth-child(5)) -------------------- */
    section[data-testid="stMain"]
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="column"]:nth-child(5)
        > div[data-testid="stVerticalBlock"] {
        background    : #FFFFFF;
        border-radius : 0 10px 10px 0;
        min-height    : 80vh;
        padding       : 0 10px 16px 10px;
        box-shadow    : 2px 0 18px rgba(0,0,0,.06) inset;
    }

    /* --- Bordure globale autour du bloc 5 colonnes ---------------------- */
    section[data-testid="stMain"]
        div[data-testid="stHorizontalBlock"] {
        border        : 1.5px solid #1F5C8B;
        border-radius : 10px;
        overflow      : hidden;
        box-shadow    : 0 4px 24px rgba(0,0,0,.10);
        gap           : 0 !important;
    }

    /* ── En-têtes de panneaux ─────────────────────────────────────────── */
    .ph {
        display        : flex;
        align-items    : center;
        gap            : 8px;
        padding        : 8px 14px;
        font-size      : .78em;
        font-weight    : 700;
        letter-spacing : .07em;
        text-transform : uppercase;
        color          : #fff;
        margin         : -1px -6px 10px -6px;   /* déborde du padding colonne */
        border-bottom  : 2px solid rgba(255,255,255,.15);
    }
    .ph-tree     { background : #0F2D4A; }
    .ph-settings { background : #153F62; }
    .ph-graphics { background : #1A5C3A; }
    .ph-badge {
        margin-left    : auto;
        background     : rgba(255,255,255,.18);
        border-radius  : 99px;
        padding        : 2px 9px;
        font-size      : .78em;
        font-weight    : 600;
        letter-spacing : 0;
    }

    /* ── Rail chariot ──────────────────────────────────────────────────── */
    .sim-rail {
        display         : flex;
        justify-content : center;
        align-items     : center;
        gap             : 8px;
        padding         : 6px 0 3px;
        background      : #EEF2F7;
        border-top      : 1px solid #D1DCE8;
        border-radius   : 0 0 10px 10px;
        margin-top      : 6px;
    }
    .sim-rail-item {
        display     : flex;
        align-items : center;
        gap         : 5px;
        font-size   : .70em;
        color       : #8A9BB0;
    }
    .sim-rail-dot {
        width         : 32px;
        height        : 5px;
        border-radius : 99px;
        background    : #CBD5E0;
    }
    .sim-rail-dot.t { background : #0F2D4A; }
    .sim-rail-dot.s { background : #153F62; }
    .sim-rail-dot.g { background : #1A5C3A; }

    /* ── Topbar ────────────────────────────────────────────────────────── */
    .sim-topbar {
        display         : flex;
        justify-content : space-between;
        align-items     : center;
        background      : linear-gradient(90deg, #0F1923 0%, #153F62 100%);
        padding         : 8px 18px;
        border-radius   : 10px 10px 0 0;
        border          : 1.5px solid #1F5C8B;
        border-bottom   : 2px solid #1F5C8B;
        margin-bottom   : -2px;
    }
    .sim-topbar-left  { display:flex; align-items:center; gap:8px; }
    .sim-topbar-title { font-weight:800; font-size:.85em; letter-spacing:.06em;
                        color:#E2EAF4; text-transform:uppercase; }
    .sim-topbar-sep   { color:#4A6584; }
    .sim-topbar-mod   { background:#1F5C8B; color:white; font-size:.78em;
                        font-weight:700; padding:2px 10px; border-radius:99px; }
    .sim-tab-row      { display:flex; gap:4px; }
    .sim-tab {
        color       : #8FAFC8;
        font-size   : .73em;
        font-weight : 600;
        padding     : 3px 9px;
        border-radius: 5px;
        border      : 1px solid transparent;
        cursor      : default;
    }
    .sim-tab.on { background:#1F5C8B; color:white; border-color:#93C5FD; }

    /* ── Animation d'entrée ───────────────────────────────────────────── */
    @keyframes fadeUp {
        from { opacity:0; transform:translateY(8px); }
        to   { opacity:1; transform:translateY(0);   }
    }
    section[data-testid="stMain"]
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="column"] {
        animation : fadeUp .35s ease both;
    }
    section[data-testid="stMain"]
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="column"]:nth-child(1) { animation-delay:.00s; }
    section[data-testid="stMain"]
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="column"]:nth-child(3) { animation-delay:.07s; }
    section[data-testid="stMain"]
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="column"]:nth-child(5) { animation-delay:.14s; }

    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# FONCTION PRINCIPALE — render_simulation_mode()
# =============================================================================
def render_simulation_mode():
    _inject_simulation_panel_css()

    module_id = st.session_state.get("active_module", "M1")
    node_id   = st.session_state.get("active_node",   "shaft")

    MODULES_INFO = {
        "M1": ("⚙️",  "Constructeur",    "#153F62"),
        "M2": ("📊",  "Statique & Modal","#1A5C3A"),
        "M3": ("📈",  "Campbell + UCS",  "#6B2D0F"),
        "M4": ("🌀",  "Balourd",         "#4A1F6B"),
        "M5": ("💧",  "Paliers HD",      "#004D40"),
        "M6": ("⏱️",  "Temporel",        "#4A3500"),
        "M7": ("🔧",  "Défauts",         "#1A237E"),
        "M8": ("⚙️",  "MultiRotor",      "#3E1F00"),
        "M9": ("📄",  "Rapport",         "#212121"),
        "AI": ("✨",  "Copilot",         "#1F3A5C"),
    }
    icon, label, color = MODULES_INFO.get(module_id, ("🔧", module_id, "#1F5C8B"))

    # ── Topbar ──────────────────────────────────────────────────────────
    tabs_html = "".join(
        '<span class="sim-tab{}">{} {}</span>'.format(
            " on" if mid == module_id else "",
            MODULES_INFO.get(mid, ("🔧",""))[0], mid
        )
        for mid in ["M1","M2","M3","M4","M5","M6","M7","M8","M9","AI"]
    )
    st.markdown("""
    <div class="sim-topbar">
      <div class="sim-topbar-left">
        <span style="color:#93C5FD;font-size:1.1em;">⚙</span>
        <span class="sim-topbar-title">Mode Simulation</span>
        <span class="sim-topbar-sep">›</span>
        <span class="sim-topbar-mod">{module_id}</span>
        <span style="color:#6B8AAA;font-size:.82em;margin-left:4px;">{label}</span>
      </div>
      <div class="sim-tab-row">{tabs}</div>
    </div>
    """.format(module_id=module_id, label=label, tabs=tabs_html),
    unsafe_allow_html=True)

    # ── 5 colonnes : tree | sep | settings | sep | graphics ─────────────
    col_tree, col_sep1, col_settings, col_sep2, col_graphics = st.columns(
        [1.5, 0.04, 2.1, 0.04, 3.9]
    )

    # ══ PANNEAU 1 — ARBRE ════════════════════════════════════════════════
    with col_tree:
        # En-tête uniquement (pas de div wrapper autour des widgets)
        st.markdown(
            '<div class="ph ph-tree">'
            '<span>🌳</span> Arbre de modèle'
            '<span class="ph-badge">M1</span></div>',
            unsafe_allow_html=True
        )
        render_model_tree()

    # ══ SEP 1 ════════════════════════════════════════════════════════════
    with col_sep1:
        st.markdown("&nbsp;", unsafe_allow_html=True)   # force la colonne à exister

    # ══ PANNEAU 2 — PARAMÈTRES ═══════════════════════════════════════════
    with col_settings:
        st.markdown(
            '<div class="ph ph-settings">'
            '<span>{icon}</span> Paramètres — {label}'
            '<span class="ph-badge">{mid}</span></div>'.format(
                icon=icon, label=label, mid=module_id
            ),
            unsafe_allow_html=True
        )
        # route_to_module gère lui-même les with col_settings / col_graphics
        route_to_module(module_id, node_id, col_settings, col_graphics)

    # ══ SEP 2 ════════════════════════════════════════════════════════════
    with col_sep2:
        st.markdown("&nbsp;", unsafe_allow_html=True)

    # ══ PANNEAU 3 — GRAPHIQUES ═══════════════════════════════════════════
    with col_graphics:
        st.markdown(
            '<div class="ph ph-graphics">'
            '📉 Résultats &amp; Graphiques'
            '<span class="ph-badge">{mid} · {node}</span></div>'.format(
                mid=module_id, node=node_id
            ),
            unsafe_allow_html=True
        )
        # Le contenu est injecté par route_to_module ci-dessus via col_graphics

    # ══ RAIL CHARIOT ═════════════════════════════════════════════════════
    st.markdown("""
    <div class="sim-rail">
      <div class="sim-rail-item">
        <div class="sim-rail-dot t"></div>
        <span>🌳 Arbre</span>
      </div>
      <div class="sim-rail-item">
        <div class="sim-rail-dot s"></div>
        <span>⚙️ Paramètres</span>
      </div>
      <div class="sim-rail-item">
        <div class="sim-rail-dot g"></div>
        <span>📉 Résultats</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
# ==============================================================================
# =============================================================================
# SNIPPET À INTÉGRER DANS app.py — Remplace render_dashboard()
# =============================================================================

def render_dashboard():
    # ── CSS du tableau de bord ─────────────────────────────────────────────
    st.markdown("""
    <style>
    /* ── Hero Dashboard ───────────────────────────────────────────────── */
    .dash-hero {
        background: linear-gradient(135deg, #0F1923 0%, #153F62 50%, #1F5C8B 100%);
        border-radius: 14px;
        padding: 36px 40px 30px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
        border: 1.5px solid rgba(31,92,139,0.4);
    }
    .dash-hero::before {
        content: "";
        position: absolute;
        right: -60px; top: -60px;
        width: 280px; height: 280px;
        border-radius: 50%;
        background: rgba(31,92,139,0.18);
        pointer-events: none;
    }
    .dash-hero::after {
        content: "";
        position: absolute;
        right: 60px; bottom: -80px;
        width: 200px; height: 200px;
        border-radius: 50%;
        background: rgba(34,134,58,0.12);
        pointer-events: none;
    }
    .dash-hero-title {
        font-size: 2.2em;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.5px;
        margin: 0 0 4px;
        line-height: 1.1;
    }
    .dash-hero-sub {
        color: rgba(255,255,255,0.70);
        font-size: 1.05em;
        margin: 0 0 20px;
    }
    .dash-hero-author {
        color: rgba(255,255,255,0.45);
        font-size: 0.82em;
        letter-spacing: 0.04em;
    }
    .dash-hero-badges {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 16px;
    }
    .dash-hero-badge {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.2);
        color: rgba(255,255,255,0.85);
        padding: 4px 12px;
        border-radius: 99px;
        font-size: 0.76em;
        font-weight: 600;
        letter-spacing: 0.04em;
    }
    .dash-hero-badge.ok  { background: rgba(34,134,58,0.25); border-color: rgba(34,134,58,0.5); color: #7FE5A0; }
    .dash-hero-badge.err { background: rgba(192,0,0,0.25);   border-color: rgba(192,0,0,0.5);   color: #FF8F8F; }

    /* ── Grille des métriques ──────────────────────────────────────────── */
    .dash-metrics-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 26px;
    }
    .dash-metric {
        background: #FFFFFF;
        border: 1.5px solid #D0D8E4;
        border-radius: 10px;
        padding: 16px 18px;
        position: relative;
        overflow: hidden;
        transition: box-shadow 0.2s;
    }
    .dash-metric::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
    }
    .dash-metric.blue::before  { background: #1F5C8B; }
    .dash-metric.green::before { background: #22863A; }
    .dash-metric.orange::before{ background: #C55A11; }
    .dash-metric.purple::before{ background: #7B1FA2; }
    .dash-metric-icon  { font-size: 1.6em; margin-bottom: 8px; }
    .dash-metric-label { font-size: 0.74em; font-weight: 600; color: #6B7280; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 2px; }
    .dash-metric-value { font-size: 1.6em; font-weight: 800; color: #1A1A2E; line-height: 1; }
    .dash-metric-sub   { font-size: 0.76em; color: #9CA3AF; margin-top: 3px; }
    .dash-metric-ok    { color: #22863A !important; }
    .dash-metric-err   { color: #C00000 !important; }
    .dash-metric-warn  { color: #C55A11 !important; }

    /* ── Section header ────────────────────────────────────────────────── */
    .dash-section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 0 0 16px;
        padding-bottom: 10px;
        border-bottom: 2px solid #EBF4FB;
    }
    .dash-section-title {
        font-size: 1.05em;
        font-weight: 700;
        color: #1F5C8B;
        letter-spacing: -0.2px;
    }
    .dash-section-badge {
        background: #EBF4FB;
        color: #1F5C8B;
        border: 1px solid #B5D4F4;
        border-radius: 99px;
        padding: 2px 10px;
        font-size: 0.72em;
        font-weight: 700;
        letter-spacing: 0.04em;
    }

    /* ── Cartes de modules ─────────────────────────────────────────────── */
    .dash-module-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 14px;
        margin-bottom: 28px;
    }
    .dash-module-card {
        background: #FFFFFF;
        border: 1.5px solid #D0D8E4;
        border-radius: 12px;
        padding: 0;
        overflow: hidden;
        transition: transform 0.15s, box-shadow 0.15s;
    }
    .dash-module-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(31,92,139,0.12);
    }
    .dash-module-card-header {
        height: 5px;
        width: 100%;
    }
    .dash-module-card-body {
        padding: 14px 16px 10px;
    }
    .dash-module-card-top {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 6px;
    }
    .dash-module-icon {
        font-size: 1.3em;
        width: 36px; height: 36px;
        display: flex; align-items: center; justify-content: center;
        border-radius: 8px;
        flex-shrink: 0;
    }
    .dash-module-id-badge {
        font-size: 0.68em;
        font-weight: 800;
        letter-spacing: 0.08em;
        padding: 2px 8px;
        border-radius: 99px;
        text-transform: uppercase;
    }
    .dash-module-new {
        font-size: 0.64em;
        font-weight: 700;
        background: #F3E5F5;
        color: #4A148C;
        border: 1px solid #CE93D8;
        border-radius: 99px;
        padding: 2px 7px;
        margin-left: 4px;
    }
    .dash-module-title {
        font-size: 0.92em;
        font-weight: 700;
        color: #1A1A2E;
        margin-bottom: 3px;
    }
    .dash-module-desc {
        font-size: 0.78em;
        color: #6B7280;
        line-height: 1.4;
        margin-bottom: 8px;
    }
    .dash-module-status {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.70em;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 99px;
        margin-bottom: 4px;
    }
    .dash-module-status.done { background: #E8F5E9; color: #1B5E20; border: 1px solid #A5D6A7; }
    .dash-module-status.none { background: #F3F4F6; color: #9CA3AF; border: 1px solid #E5E7EB; }

    /* ── Zone de progression globale ───────────────────────────────────── */
    .dash-progress-wrap {
        background: #FFFFFF;
        border: 1.5px solid #D0D8E4;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
    }
    .dash-progress-header {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 10px;
    }
    .dash-progress-label { font-size: 0.85em; font-weight: 700; color: #1A1A2E; }
    .dash-progress-pct   { font-size: 1.4em; font-weight: 800; color: #1F5C8B; }
    .dash-progress-bar   { height: 8px; background: #EBF4FB; border-radius: 99px; overflow: hidden; }
    .dash-progress-fill  { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #1F5C8B, #22863A); transition: width 0.6s ease; }

    /* ── Activité récente ──────────────────────────────────────────────── */
    .dash-log-wrap {
        background: #1E1E2E;
        border: 1.5px solid #2D3748;
        border-radius: 10px;
        padding: 14px 16px;
    }
    .dash-log-title {
        font-size: 0.72em;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #4A6584;
        margin-bottom: 8px;
    }
    .dash-log-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 3px 0;
        font-family: monospace;
        font-size: 0.76em;
        color: #8A9BB0;
    }
    .dash-log-item.ok   { color: #4CAF50; }
    .dash-log-item.warn { color: #FF9800; }
    .dash-log-item.err  { color: #F44336; }
    .dash-log-ts { color: #4A6584; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

    rotor   = st.session_state.get("rotor")
    n_done  = len(st.session_state.get("tut_done", set()))
    n_res   = sum(1 for k in ["res_modal","res_campbell","res_unbalance","res_temporal"]
                  if st.session_state.get(k) is not None)
    logs    = st.session_state.get("log_messages", [])

    # ── HERO ──────────────────────────────────────────────────────────────
    ross_badge_cls = "ok" if ROSS_AVAILABLE else "err"
    ross_badge_lbl = "ROSS {} actif".format(ROSS_VERSION) if ROSS_AVAILABLE else "ROSS absent"
    rotor_badge_lbl= "{} nœuds · {:.1f} kg".format(len(rotor.nodes), rotor.m) if rotor else "Aucun rotor"
    rotor_badge_cls= "ok" if rotor else "err"

    st.markdown("""
    <div class="dash-hero">
      <div class="dash-hero-title">⚙ RotorLab Suite 2.0</div>
      <div class="dash-hero-sub">Plateforme Avancée de Simulation en Dynamique des Rotors</div>
      <div class="dash-hero-author">{author} — {inst}</div>
      <div class="dash-hero-badges">
        <span class="dash-hero-badge {rc}">{rl}</span>
        <span class="dash-hero-badge {roc}">{rol}</span>
        <span class="dash-hero-badge">v{ver}</span>
        <span class="dash-hero-badge">{nd} / 6 tutoriels</span>
        <span class="dash-hero-badge">{nr} / 9 analyses</span>
      </div>
    </div>
    """.format(
        author=APP_AUTHOR, inst=APP_INST, ver=APP_VERSION,
        rc=ross_badge_cls,  rl=ross_badge_lbl,
        roc=rotor_badge_cls, rol=rotor_badge_lbl,
        nd=n_done, nr=n_res,
    ), unsafe_allow_html=True)

    # ── MÉTRIQUES ─────────────────────────────────────────────────────────
    rotor_val   = "{} nœuds".format(len(rotor.nodes)) if rotor else "Aucun"
    rotor_sub   = "{:.2f} kg · {} DDL".format(rotor.m, rotor.ndof) if rotor else "Construisez M1"
    rotor_cls   = "dash-metric-ok" if rotor else "dash-metric-err"
    ross_val    = ROSS_VERSION if ROSS_AVAILABLE else "Absent"
    ross_cls    = "dash-metric-ok" if ROSS_AVAILABLE else "dash-metric-err"
    analyses_pct= int(n_res / 9 * 100)
    tut_pct     = int(n_done / 6 * 100)

    st.markdown("""
    <div class="dash-metrics-row">
      <div class="dash-metric blue">
        <div class="dash-metric-icon">⚙</div>
        <div class="dash-metric-label">Moteur ROSS</div>
        <div class="dash-metric-value {rc}">{rv}</div>
        <div class="dash-metric-sub">ross-rotordynamics</div>
      </div>
      <div class="dash-metric green">
        <div class="dash-metric-icon">🔩</div>
        <div class="dash-metric-label">Rotor actif</div>
        <div class="dash-metric-value {rotc}">{rotv}</div>
        <div class="dash-metric-sub">{rots}</div>
      </div>
      <div class="dash-metric orange">
        <div class="dash-metric-icon">📊</div>
        <div class="dash-metric-label">Analyses calculées</div>
        <div class="dash-metric-value">{nr} <span style="font-size:0.5em;color:#9CA3AF;">/ 9</span></div>
        <div class="dash-metric-sub">Progression {ap}%</div>
      </div>
      <div class="dash-metric purple">
        <div class="dash-metric-icon">🎓</div>
        <div class="dash-metric-label">Tutoriels</div>
        <div class="dash-metric-value">{nd} <span style="font-size:0.5em;color:#9CA3AF;">/ 6</span></div>
        <div class="dash-metric-sub">Progression {tp}%</div>
      </div>
    </div>
    """.format(
        rc=ross_cls, rv=ross_val,
        rotc=rotor_cls, rotv=rotor_val, rots=rotor_sub,
        nr=n_res, ap=analyses_pct,
        nd=n_done, tp=tut_pct,
    ), unsafe_allow_html=True)

    # ── BARRE DE PROGRESSION GLOBALE ──────────────────────────────────────
    global_pct = min(100, int((n_res / 9 * 50) + (n_done / 6 * 30) + (20 if rotor else 0)))
    st.markdown("""
    <div class="dash-progress-wrap">
      <div class="dash-progress-header">
        <span class="dash-progress-label">Progression globale du projet</span>
        <span class="dash-progress-pct">{pct}%</span>
      </div>
      <div class="dash-progress-bar">
        <div class="dash-progress-fill" style="width:{pct}%"></div>
      </div>
    </div>
    """.format(pct=global_pct), unsafe_allow_html=True)

    # ── MODULES ───────────────────────────────────────────────────────────
    # ── MODULES ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="dash-section-header">
      <span class="dash-section-title">Accès rapide aux modules</span>
      <span class="dash-section-badge">9 modules</span>
    </div>
    """, unsafe_allow_html=True)

    modules_info = [
        ("M1", "🏗️", "Constructeur",      "Géométrie, matériaux, paliers",       "shaft",        "#1F5C8B", "#EBF4FB", False, "res_modal"),
        ("M2", "📊", "Statique & Modal",  "Déflexion, fréquences propres",       "static_modal", "#22863A", "#E8F5E9", False, "res_modal"),
        ("M3", "📈", "Campbell + UCS",    "Stabilité, vitesses critiques",       "campbell",     "#C55A11", "#FFF3E0", False, "res_campbell"),
        ("M4", "🌀", "Balourd & H(jω)",   "Bode, polaire, ISO 1940",             "unbalance",    "#7B1FA2", "#F3E5F5", False, "res_unbalance"),
        ("M5", "💧", "Paliers HD",        "Film fluide, coefficients",           "hd_bearings",  "#00796B", "#E0F2F1", True,  None),
        ("M6", "⏱️", "Temporel",          "Newmark, orbites, waterfall 3D",      "temporal",     "#F57C00", "#FFF3E0", False, "res_temporal"),
        ("M7", "🔧", "Défauts",           "Fissure, désalignement, frottement",  "faults",       "#C62828", "#FFEBEE", False, None),
        ("M8", "⚙️", "MultiRotor",        "GearElement, engrenages couplés",     "multirotor",   "#4527A0", "#EDE7F6", True,  None),
        ("M9", "📄", "Rapport PDF",       "Export complet multi-sections",       "report",       "#37474F", "#ECEFF1", False, None),
    ]

    # Utilisation du système de colonnes natif de Streamlit (groupées par 3)
    for i in range(0, len(modules_info), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(modules_info):
                mid, icon, title, desc, node, color, bg, is_new, res_key = modules_info[idx]
                
                has_result = st.session_state.get(res_key) is not None if res_key else False
                status_cls = "done" if has_result else "none"
                status_lbl = "Calculé" if has_result else "Non calculé"
                new_tag    = ' <span class="dash-module-new">NEW</span>' if is_new else ""
                
                # Code HTML pour UNE SEULE carte (avec une marge basse pour espacer du bouton)
                card_html = """<div class="dash-module-card" style="margin-bottom: 12px;">
<div class="dash-module-card-header" style="background:{color};"></div>
<div class="dash-module-card-body">
<div class="dash-module-card-top">
<div class="dash-module-icon" style="background:{bg};">{icon}</div>
<div>
<span class="dash-module-id-badge" style="background:{bg};color:{color};">{mid}</span>{new_tag}
</div>
</div>
<div class="dash-module-title">{title}</div>
<div class="dash-module-desc">{desc}</div>
<span class="dash-module-status {sc}">{sl}</span>
</div>
</div>
""".format(
                    color=color, bg=bg, icon=icon, mid=mid,
                    new_tag=new_tag, title=title, desc=desc,
                    sc=status_cls, sl=status_lbl
                )
                
                with col:
                    # 1. Afficher la carte HTML
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    # 2. Préparer la fonction de redirection du bouton
                    _node, _module = node, mid
                    def _make_cb(n, m):
                        def _cb():
                            st.session_state["active_node"]   = n
                            st.session_state["active_module"] = m
                            st.session_state["nav_mode"]      = "simulation"
                        return _cb
                        
                    # 3. Afficher le bouton interactif, parfaitement aligné sous sa carte
                    st.button(
                        "Ouvrir {}".format(mid),
                        key="dash2_{}".format(mid),
                        use_container_width=True,
                        type="primary",
                        on_click=_make_cb(_node, _module)
                    )

    # ── JOURNAL D'ACTIVITÉ ────────────────────────────────────────────────
    if logs:
        st.markdown("""
        <div class="dash-section-header" style="margin-top:24px;">
          <span class="dash-section-title">Journal d'activité</span>
          <span class="dash-section-badge">{n} entrées</span>
        </div>
        """.format(n=len(logs)), unsafe_allow_html=True)

        log_items = ""
        for log in reversed(logs[-6:]):
            cls = {"ok": "ok", "warn": "warn", "err": "err"}.get(log["level"], "")
            log_items += '<div class="dash-log-item {cls}"><span class="dash-log-ts">[{ts}]</span> {icon} {msg}</div>'.format(
                cls=cls, ts=log["ts"], icon=log["icon"], msg=log["msg"])

        st.markdown("""
        <div class="dash-log-wrap">
          <div class="dash-log-title">Activité récente</div>
          {items}
        </div>
        """.format(items=log_items), unsafe_allow_html=True)

def render_tutorial_mode():
    try:
        from tutorials.tutorial_data import render_tutorials
        render_tutorials()
    except ImportError as e:
        import traceback
        st.error("**Erreur d'import :** `{}`".format(e))
        with st.expander("Traceback complet"):
            st.code(traceback.format_exc(), language="python")
    except Exception as e:
        import traceback
        st.error("**Erreur mode pédagogique :** `{}`".format(e))
        with st.expander("Traceback complet"):
            st.code(traceback.format_exc(), language="python")


def render_copilot_mode():
    try:
        from modules.ai_copilot import render_copilot_fullscreen
        render_copilot_fullscreen()
    except Exception as e:
        st.error("Erreur Copilot : {}".format(e))

# =============================================================================
# MAIN
# =============================================================================
def main():
    render_header()
    render_top_nav()
    st.markdown(
        "<hr style='margin:4px 0 8px;border-color:#D0D8E4;'>",
        unsafe_allow_html=True)

    mode = st.session_state["nav_mode"]

    if mode == "simulation":
        render_simulation_mode()
    elif mode == "dashboard":
        render_dashboard()
    elif mode == "tutorial":
        render_tutorial_mode()
    elif mode == "copilot":
        render_copilot_mode()

    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ {}".format(APP_NAME))
        st.session_state["user_name"] = st.text_input(
            "👤 Nom :", st.session_state["user_name"])
        st.markdown("---")
        if ROSS_AVAILABLE:
            st.success("✅ ROSS {}".format(ROSS_VERSION))
        else:
            st.error("❌ ROSS non installé")
            st.code("pip install ross-rotordynamics")
        rotor = st.session_state.get("rotor")
        if rotor:
            st.markdown("---")
            st.markdown("**🔩 Rotor actif :**")
            st.caption(st.session_state.get("rotor_name", "—"))
            st.caption("{} nœuds · {:.2f} kg".format(
                len(rotor.nodes), rotor.m))
        st.markdown("---")
        st.caption("v{} · {}".format(APP_VERSION, APP_INST))

    render_log_bar()


if __name__ == "__main__":
    main()
