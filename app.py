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
        "active_node"   : "shaft",
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

def render_model_tree():
    active = st.session_state.get("active_node", "shaft")

    # CSS UNIQUEMENT pour les boutons secondaires du tree
    # kind="secondary" est l'attribut Streamlit natif — pas de data-testid
    # → ne touche PAS aux boutons primary (bleus)
    st.markdown("""
    <style>
    div[data-testid="stVerticalBlock"]
        div[data-testid="stButton"]
        > button[kind="secondary"] {
        text-align      : left !important;
        justify-content : flex-start !important;
        font-size       : 0.82em !important;
        font-weight     : 400 !important;
        background      : transparent !important;
        border          : none !important;
        border-left     : 3px solid transparent !important;
        border-radius   : 0 !important;
        padding         : 5px 8px 5px 18px !important;
        margin          : 1px 0 !important;
        box-shadow      : none !important;
        color           : #1A1A2E !important;
    }
    div[data-testid="stVerticalBlock"]
        div[data-testid="stButton"]
        > button[kind="secondary"]:hover {
        background       : rgba(31,92,139,0.09) !important;
        border-left-color: rgba(31,92,139,0.4) !important;
        color            : #1F5C8B !important;
    }
    </style>
    """, unsafe_allow_html=True)

    for section in MODEL_TREE:
        st.markdown(
            '<div class="rl-tree-section">{} {}</div>'.format(
                section["icon"], section["label"]),
            unsafe_allow_html=True
        )
        for item in section["children"]:
            is_active = (item["id"] == active)
            is_new    = item["module"] in ("M5", "M8")
            new_tag   = " [NEW]" if is_new else ""

            if is_active:
                st.markdown(
                    '<div style="background:rgba(31,92,139,0.10);'
                    'border-left:3px solid #1F5C8B;'
                    'padding:5px 8px 5px 18px;font-size:0.82em;'
                    'font-weight:600;color:#1F5C8B;margin:1px 0;">'
                    '{} &nbsp;{}{}</div>'.format(
                        item["icon"], item["label"], new_tag),
                    unsafe_allow_html=True
                )
            else:
                node_id = item["id"]
                module  = item["module"]
                st.button(
                    "{}  {}{}".format(item["icon"], item["label"], new_tag),
                    key="tree_{}".format(item["id"]),
                    use_container_width=True,
                    on_click=_cb_tree,
                    args=(node_id, module),
                )

    # ── Exemples et actions (sans le titre "Actions rapides") ────────────
    st.markdown("---")

    if ROSS_AVAILABLE:
        st.caption("📂 Exemples")
        st.button(
            "📂 Compresseur centrifuge",
            use_container_width=True,
            key="tree_comp",
            on_click=_cb_load_compressor,
        )

    if st.session_state.get("rotor") is not None:
        st.button(
            "🗑️ Réinitialiser",
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
# simulation_layout.py — Mode Simulation : Mise en page 3 panneaux
# RotorLab Suite 2.0 — À coller dans app.py en remplacement de
# render_simulation_mode() et de _inject_simulation_css() (si existant).
# =============================================================================

import streamlit as st


# =============================================================================
# CSS — Panneaux avec séparateurs + en-têtes de panneau
# =============================================================================
def _inject_simulation_panel_css():
    st.markdown("""
<style>
/* ─── Variables de thème ────────────────────────────────────────────────── */
:root {
  --panel-bg-tree:      #0F1923;
  --panel-bg-settings:  #F7F9FC;
  --panel-bg-graphics:  #FFFFFF;
  --panel-border:       #1F5C8B;
  --sep-color:          #1F5C8B;
  --sep-glow:           rgba(31,92,139,.35);
  --header-bg-tree:     #1F5C8B;
  --header-bg-settings: #153F62;
  --header-bg-graphics: #22863A;
  --header-text:        #FFFFFF;
  --panel-radius:       10px;
  --panel-shadow:       0 4px 20px rgba(0,0,0,.12);
}

/* ─── Conteneur flex 3 colonnes ─────────────────────────────────────────── */
.sim-panels-wrap {
  display: flex;
  gap: 0;
  width: 100%;
  min-height: 82vh;
  border: 1.5px solid #D1DCE8;
  border-radius: var(--panel-radius);
  overflow: hidden;
  box-shadow: var(--panel-shadow);
}

/* ─── Panneau générique ──────────────────────────────────────────────────── */
.sim-panel {
  display: flex;
  flex-direction: column;
  min-height: 82vh;
  overflow: hidden;
}
.sim-panel-tree     { flex: 0 0 18%; background: var(--panel-bg-tree); }
.sim-panel-settings { flex: 0 0 27%; background: var(--panel-bg-settings); }
.sim-panel-graphics { flex: 1 1 55%;  background: var(--panel-bg-graphics); }

/* ─── Séparateurs entre panneaux ────────────────────────────────────────── */
.sim-sep {
  width: 4px;
  min-height: 82vh;
  background: linear-gradient(
    180deg,
    transparent 0%,
    var(--sep-color) 15%,
    var(--sep-color) 85%,
    transparent 100%
  );
  box-shadow: 0 0 10px var(--sep-glow);
  flex-shrink: 0;
  position: relative;
  cursor: col-resize;
}
/* Petits tirets décoratifs sur le séparateur */
.sim-sep::before,
.sim-sep::after {
  content: "⋮";
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  color: var(--sep-color);
  font-size: 14px;
  opacity: .6;
  letter-spacing: -2px;
}
.sim-sep::before { top: 42%; }
.sim-sep::after  { top: 52%; }

/* ─── En-tête de chaque panneau ─────────────────────────────────────────── */
.sim-panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 14px;
  background: var(--hbg, #1F5C8B);
  color: var(--header-text);
  font-size: .80em;
  font-weight: 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  border-bottom: 2px solid rgba(255,255,255,.12);
  flex-shrink: 0;
  user-select: none;
}
.sim-panel-header .ph-icon { font-size: 1.1em; opacity: .85; }
.sim-panel-header .ph-badge {
  margin-left: auto;
  background: rgba(255,255,255,.18);
  border-radius: 99px;
  padding: 2px 8px;
  font-size: .75em;
  font-weight: 600;
}

/* ─── Corps scrollable de chaque panneau ───────────────────────────────── */
.sim-panel-body {
  flex: 1 1 auto;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 10px 10px 16px;
  scrollbar-width: thin;
  scrollbar-color: var(--sep-color) transparent;
}
.sim-panel-body::-webkit-scrollbar       { width: 5px; }
.sim-panel-body::-webkit-scrollbar-thumb { background: var(--sep-color); border-radius: 4px; }

/* ─── Titre en pied de panneau (optionnel) ──────────────────────────────── */
.sim-panel-footer {
  padding: 6px 12px;
  background: rgba(0,0,0,.04);
  border-top: 1px solid #D1DCE8;
  font-size: .72em;
  color: #8A9BB0;
  flex-shrink: 0;
}

/* ─── Texte clair sur fond sombre (panneau arbre) ───────────────────────── */
.sim-panel-tree .sim-panel-body * { color: #CBD5E0 !important; }
.sim-panel-tree .sim-panel-body .stMarkdown h3,
.sim-panel-tree .sim-panel-body .stMarkdown h4 {
  color: #93C5FD !important;
  font-size: .82em !important;
  margin-top: 10px !important;
}
.sim-panel-tree .sim-panel-body .stButton > button {
  background: rgba(31,92,139,.35) !important;
  color: #E2EAF4 !important;
  border: 1px solid rgba(31,92,139,.6) !important;
  font-size: .78em !important;
  padding: 3px 8px !important;
  width: 100% !important;
  text-align: left !important;
  border-radius: 5px !important;
}
.sim-panel-tree .sim-panel-body .stButton > button:hover {
  background: rgba(31,92,139,.65) !important;
  border-color: #1F5C8B !important;
}
/* Sélecteur actif dans l'arbre */
.sim-panel-tree .sim-panel-body .stButton > button[kind="primary"] {
  background: #1F5C8B !important;
  border-color: #93C5FD !important;
  color: white !important;
}

/* ─── Panneau réglages ──────────────────────────────────────────────────── */
.sim-panel-settings .sim-panel-body .stSlider,
.sim-panel-settings .sim-panel-body .stNumberInput,
.sim-panel-settings .sim-panel-body .stSelectbox {
  font-size: .88em;
}

/* ─── Animation d'entrée des panneaux ──────────────────────────────────── */
@keyframes panelFadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}
.sim-panel {
  animation: panelFadeIn .3s ease both;
}
.sim-panel-tree     { animation-delay: .00s; }
.sim-panel-settings { animation-delay: .06s; }
.sim-panel-graphics { animation-delay: .12s; }

/* ─── Chariot (rail indicators en bas) ─────────────────────────────────── */
.sim-rail {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px 0 2px;
  background: #F0F4FA;
  border-top: 1px solid #D1DCE8;
}
.sim-rail-dot {
  width: 28px; height: 4px;
  border-radius: 99px;
  background: #CBD5E0;
  transition: background .2s, width .2s;
}
.sim-rail-dot.active { background: #1F5C8B; width: 42px; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# FONCTION PRINCIPALE — remplace render_simulation_mode()
# =============================================================================
def render_simulation_mode():
    _inject_simulation_panel_css()

    module_id = st.session_state.get("active_module", "M1")
    node_id   = st.session_state.get("active_node",   "shaft")

    # ── Barre de titre global (au-dessus des 3 panneaux) ─────────────────
    _render_simulation_topbar(module_id)

    # ── Les 3 colonnes Streamlit ─────────────────────────────────────────
    col_tree, col_sep1, col_settings, col_sep2, col_graphics = st.columns(
        [1.5, 0.04, 2.1, 0.04, 3.9]
    )

    # ══ PANNEAU 1 — Arbre de modèle ══════════════════════════════════════
    with col_tree:
        st.markdown("""
        <div class="sim-panel sim-panel-tree">
          <div class="sim-panel-header" style="--hbg:#0F2D4A;">
            <span class="ph-icon">🌳</span>
            Arbre de modèle
            <span class="ph-badge">M1</span>
          </div>
          <div class="sim-panel-body" id="panel-tree-body">
        """, unsafe_allow_html=True)

        render_model_tree()

        st.markdown("""
          </div>
          <div class="sim-panel-footer">Cliquez sur un nœud pour le sélectionner</div>
        </div>
        """, unsafe_allow_html=True)

    # ══ SÉPARATEUR 1 ══════════════════════════════════════════════════════
    with col_sep1:
        st.markdown("""
        <div class="sim-sep" title="Glisser pour redimensionner"></div>
        """, unsafe_allow_html=True)

    # ══ PANNEAU 2 — Paramètres / Réglages ════════════════════════════════
    with col_settings:
        MODULE_LABELS = {
            "M1": ("⚙️", "Constructeur", "#153F62"),
            "M2": ("📊", "Statique & Modal", "#1A5C3A"),
            "M3": ("📈", "Campbell & UCS",  "#6B2D0F"),
            "M4": ("🌀", "Balourd & H(jω)", "#4A1F6B"),
            "M5": ("💧", "Paliers HD",       "#004D40"),
            "M6": ("🔄", "Torsionnel",       "#5D2A0C"),
            "M7": ("⚡", "Transitoire",      "#1A237E"),
            "M8": ("🔗", "MultiRotor",       "#3E1F00"),
            "M9": ("📋", "Rapport",          "#212121"),
        }
        icon, label, color = MODULE_LABELS.get(module_id, ("🔧", module_id, "#1F5C8B"))

        st.markdown(f"""
        <div class="sim-panel sim-panel-settings">
          <div class="sim-panel-header" style="--hbg:{color};">
            <span class="ph-icon">{icon}</span>
            Paramètres — {label}
            <span class="ph-badge">{module_id}</span>
          </div>
          <div class="sim-panel-body" id="panel-settings-body">
        """, unsafe_allow_html=True)

        # Appel du module : col_settings reçoit les widgets de réglage
        route_to_module(module_id, node_id, col_settings, col_graphics)

        st.markdown("""
          </div>
          <div class="sim-panel-footer">Modifiez les paramètres puis relancez la simulation</div>
        </div>
        """, unsafe_allow_html=True)

    # ══ SÉPARATEUR 2 ══════════════════════════════════════════════════════
    with col_sep2:
        st.markdown("""
        <div class="sim-sep" title="Glisser pour redimensionner"></div>
        """, unsafe_allow_html=True)

    # ══ PANNEAU 3 — Graphiques / Résultats ═══════════════════════════════
    with col_graphics:
        st.markdown(f"""
        <div class="sim-panel sim-panel-graphics">
          <div class="sim-panel-header" style="--hbg:#1A5C3A;">
            <span class="ph-icon">📉</span>
            Résultats & Graphiques
            <span class="ph-badge">{module_id} · {node_id}</span>
          </div>
          <div class="sim-panel-body" id="panel-graphics-body">
        """, unsafe_allow_html=True)

        # Le contenu graphique est injecté par route_to_module via col_graphics
        # (déjà appelé dans col_settings ci-dessus)

        st.markdown("""
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ══ RAIL / CHARIOT en pied de page ═══════════════════════════════════
    _render_simulation_rail(module_id)


# =============================================================================
# BARRE DE TITRE GLOBALE (au-dessus des 3 panneaux)
# =============================================================================
def _render_simulation_topbar(module_id):
    MODULES_ORDER = ["M1","M2","M3","M4","M5","M6","M7","M8","M9"]
    MODULES_INFO  = {
        "M1": ("⚙️", "Constructeur"),
        "M2": ("📊", "Modal"),
        "M3": ("📈", "Campbell"),
        "M4": ("🌀", "Balourd"),
        "M5": ("💧", "Paliers HD"),
        "M6": ("🔄", "Torsionnel"),
        "M7": ("⚡", "Transitoire"),
        "M8": ("🔗", "MultiRotor"),
        "M9": ("📋", "Rapport"),
    }

    tabs_html = ""
    for mid in MODULES_ORDER:
        icon, lbl = MODULES_INFO.get(mid, ("🔧", mid))
        active_cls = "sim-tab-active" if mid == module_id else ""
        tabs_html += f"""
        <span class="sim-tab {active_cls}" onclick="
          // Streamlit ne supporte pas le click JS direct —
          // utilisez les boutons Streamlit ci-dessous
        " title="{lbl}">{icon} {mid}</span>"""

    st.markdown(f"""
    <div class="sim-topbar">
      <div class="sim-topbar-left">
        <span class="sim-topbar-icon">⚙</span>
        <span class="sim-topbar-title">Mode Simulation</span>
        <span class="sim-topbar-sep">›</span>
        <span class="sim-topbar-active">{module_id}</span>
      </div>
      <div class="sim-topbar-tabs">{tabs_html}</div>
    </div>
    <style>
    .sim-topbar {{
      display:flex; justify-content:space-between; align-items:center;
      background: linear-gradient(90deg, #0F1923 0%, #153F62 100%);
      padding: 8px 16px; border-radius: 10px 10px 0 0;
      margin-bottom: 0; border-bottom: 2px solid #1F5C8B;
    }}
    .sim-topbar-left   {{ display:flex; align-items:center; gap:8px; color:#CBD5E0; }}
    .sim-topbar-icon   {{ font-size:1.1em; color:#93C5FD; }}
    .sim-topbar-title  {{ font-weight:700; font-size:.85em; letter-spacing:.05em; color:#E2EAF4; text-transform:uppercase; }}
    .sim-topbar-sep    {{ color:#4A6584; font-size:.9em; }}
    .sim-topbar-active {{ background:#1F5C8B; color:white; font-size:.78em; font-weight:700;
                          padding:2px 10px; border-radius:99px; }}
    .sim-topbar-tabs   {{ display:flex; gap:4px; flex-wrap:wrap; }}
    .sim-tab {{
      color:#8FAFC8; font-size:.74em; font-weight:600; padding:3px 9px;
      border-radius:5px; cursor:pointer; transition:all .15s;
      border: 1px solid transparent;
    }}
    .sim-tab:hover      {{ background:rgba(31,92,139,.3); color:white; }}
    .sim-tab-active     {{ background:#1F5C8B; color:white !important;
                           border-color:#93C5FD; }}
    </style>
    """, unsafe_allow_html=True)

    # Navigation rapide entre modules (boutons Streamlit réels)
    with st.expander("🗂️ Navigation rapide entre modules", expanded=False):
        cols = st.columns(len(MODULES_ORDER))
        for i, mid in enumerate(MODULES_ORDER):
            with cols[i]:
                icon, lbl = MODULES_INFO[mid]
                btn_type = "primary" if mid == module_id else "secondary"
                if st.button(f"{icon}\n{mid}", key=f"topnav_{mid}",
                             type=btn_type, use_container_width=True):
                    st.session_state["active_module"] = mid
                    st.session_state["active_node"]   = "default"
                    st.rerun()


# =============================================================================
# CHARIOT (rail indicateur en pied de page)
# =============================================================================
def _render_simulation_rail(module_id):
    PANELS = [
        ("🌳", "Arbre",        "active"),
        ("⚙️", "Paramètres",  "active"),
        ("📉", "Résultats",    "active"),
    ]
    dots = "".join(
        f'<div class="sim-rail-dot active" title="{lbl}"></div>'
        for _, lbl, _ in PANELS
    )
    labels = "".join(
        f'<span style="font-size:.68em;color:#8A9BB0;padding:0 8px;">{icon} {lbl}</span>'
        for icon, lbl, _ in PANELS
    )
    st.markdown(f"""
    <div style="background:#F0F4FA;border:1px solid #D1DCE8;border-top:none;
                border-radius:0 0 10px 10px;padding:6px 0 4px;">
      <div style="display:flex;justify-content:center;gap:6px;">{dots}</div>
      <div style="display:flex;justify-content:center;gap:0;margin-top:3px;">{labels}</div>
    </div>
    """, unsafe_allow_html=True)
# ==============================================================================
def render_dashboard():
    st.markdown("""
    <div style="text-align:center;padding:20px 0 30px;">
      <h1 style="color:#1F5C8B;font-size:2.8em;margin:0;font-weight:800;">
        ⚙️ RotorLab Suite 2.0
      </h1>
      <p style="color:#6B7280;font-size:1.1em;margin:4px 0 0;">
        Plateforme Avancée de Simulation en Dynamique des Rotors
      </p>
      <p style="color:#9CA3AF;font-size:0.85em;">
        {} — {}
      </p>
    </div>
    """.format(APP_AUTHOR, APP_INST), unsafe_allow_html=True)

    rotor = st.session_state.get("rotor")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="rl-metric-card">
          <div class="rl-metric-label">Statut ROSS</div>
          <div class="rl-metric-value" style="font-size:1em;color:{};">{}</div>
        </div>""".format(
            "#22863A" if ROSS_AVAILABLE else "#C00000",
            "✅ " + ROSS_VERSION if ROSS_AVAILABLE else "❌ Absent"
        ), unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="rl-metric-card">
          <div class="rl-metric-label">Rotor actif</div>
          <div class="rl-metric-value" style="font-size:0.9em;color:{};">{}</div>
        </div>""".format(
            "#22863A" if rotor else "#C00000",
            "✅ {} nœuds".format(len(rotor.nodes)) if rotor else "❌ Aucun"
        ), unsafe_allow_html=True)
    with c3:
        n_done = len(st.session_state.get("tut_done", set()))
        st.markdown("""
        <div class="rl-metric-card">
          <div class="rl-metric-label">Tutoriels</div>
          <div class="rl-metric-value">{} / 6</div>
        </div>""".format(n_done), unsafe_allow_html=True)
    with c4:
        n_res = sum(1 for k in [
            "res_modal","res_campbell","res_unbalance","res_temporal"]
            if st.session_state.get(k) is not None)
        st.markdown("""
        <div class="rl-metric-card">
          <div class="rl-metric-label">Analyses calculées</div>
          <div class="rl-metric-value">{} / 9</div>
        </div>""".format(n_res), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🚀 Accès Rapide aux Modules")

    modules_grid = [
        ("M1","🏗️","Constructeur",     "Géométrie, Matériaux, Paliers",    "shaft",        False),
        ("M2","📊","Statique & Modal", "Déflexion, Fréquences propres",    "static_modal", False),
        ("M3","📈","Campbell + UCS",   "Stabilité, API 684, UCS Map",      "campbell",     False),
        ("M4","🌀","Balourd & H(jω)",  "Bode, Polaire, ISO 1940",          "unbalance",    False),
        ("M5","💧","Paliers HD",       "BearingFluidFilm, coefficients",   "hd_bearings",  True),
        ("M6","⏱️","Temporel",         "Newmark, Orbites, Waterfall 3D",   "temporal",     False),
        ("M7","🔧","Défauts",          "Fissure, Désalignement, Frottement","faults",       False),
        ("M8","⚙️","MultiRotor",       "GearElement, Torsionnel",          "multirotor",   True),
        ("M9","📄","Rapport PDF",      "Export complet multi-sections",    "report",       False),
    ]

    cols = st.columns(3)
    for i, (mid, icon, title, desc, node, is_new) in enumerate(modules_grid):
        with cols[i % 3]:
            new_badge = ' <span class="rl-badge rl-badge-new">NEW v2</span>' \
                        if is_new else ""
            st.markdown("""
            <div class="rl-card-info" style="margin-bottom:4px;">
              <strong>{} {} — {}</strong>{}<br>
              <small style="color:#6B7280;">{}</small>
            </div>""".format(icon, mid, title, new_badge, desc),
                unsafe_allow_html=True)

            # Capture des valeurs dans la closure
            _node   = node
            _module = mid
            def _make_cb(n, m):
                def _cb():
                    st.session_state["active_node"]   = n
                    st.session_state["active_module"] = m
                    st.session_state["nav_mode"]      = "simulation"
                return _cb

            st.button(
                "Ouvrir {}".format(mid),
                key="dash_{}".format(mid),
                use_container_width=True,
                type="primary",
                on_click=_make_cb(_node, _module)
            )


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
