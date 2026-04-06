# =============================================================================
# RotorLab Suite 2.0 — Application principale
# Pr. Najeh Ben Guedria — ISTLS, Université de Sousse
# Architecture : 3 panneaux (Model Tree | Settings | Graphics)
# =============================================================================

import streamlit as st
import numpy as np
import pandas as pd
from pathlib import Path

# ── Import de la configuration ────────────────────────────────────────────────
from config import APP_NAME, APP_VERSION, APP_AUTHOR, APP_INST, MODEL_TREE

# ── Vérification ROSS ─────────────────────────────────────────────────────────
try:
    import ross as rs
    ROSS_AVAILABLE = True
    ROSS_VERSION   = getattr(rs, '__version__', 'unknown')
except ImportError:
    ROSS_AVAILABLE = False
    ROSS_VERSION   = "non installé"

# =============================================================================
# CONFIGURATION DE LA PAGE
# =============================================================================
st.set_page_config(
    page_title = f"{APP_NAME}",
    page_icon  = "⚙️",
    layout     = "wide",
    initial_sidebar_state = "collapsed",   # Sidebar fermée par défaut (layout COMSOL)
)

# =============================================================================
# CHARGEMENT DU CSS
# =============================================================================
def load_css():
    css_path = Path("styles/theme.css")
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # CSS de fallback minimal si le fichier est absent
        st.markdown("""
        <style>
        .block-container { padding-top:0.5rem !important; max-width:100% !important; }
        </style>
        """, unsafe_allow_html=True)

load_css()

# =============================================================================
# INITIALISATION DU SESSION STATE
# =============================================================================
def init_session_state():
    defaults = {
        # Navigation
        "active_node"   : "shaft",          # Nœud actif dans le Model Tree
        "active_module" : "M1",             # Module actif
        "nav_mode"      : "dashboard",     # "simulation" | "tutorial" | "dashboard"

        # Rotor & Modèle
        "rotor"         : None,             # Objet rs.Rotor actif
        "rotor_name"    : "Nouveau rotor",
        "rotor_source"  : None,             # "custom" | "compressor" | "loaded"

        # Données de l'interface M1
        "df_shaft"      : _default_shaft(),
        "df_disk"       : _default_disk(),
        "df_bear"       : _default_bearing(),
        "mat_name"      : "Acier standard (AISI 1045)",

        # Résultats des modules (None = pas encore calculé)
        "res_static"    : None,
        "res_modal"     : None,
        "res_campbell"  : None,
        "res_ucs"       : None,
        "res_unbalance" : None,
        "res_freq"      : None,
        "res_temporal"  : None,

        # Données dérivées pour le rapport
        "df_modal"      : None,
        "df_campbell"   : None,
        "df_api"        : None,
        "api_params"    : None,
        "img_rotor"     : None,
        "img_campbell"  : None,

        # Interface
        "log_messages"  : [],               # Messages dans la barre de log
        "user_name"     : "Utilisateur",
        "chat_history"  : [],               # Historique SmartRotor Copilot
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
# FONCTIONS UTILITAIRES UI
# =============================================================================
def add_log(message: str, level: str = "info"):
    """Ajoute un message dans la barre de log (panel droit, bas)."""
    from datetime import datetime
    ts   = datetime.now().strftime("%H:%M:%S")
    icon = {"info": "ℹ️", "ok": "✅", "warn": "⚠️", "err": "❌"}.get(level, "ℹ️")
    st.session_state["log_messages"].append(
        {"ts": ts, "icon": icon, "msg": message, "level": level}
    )
    # Garder les 20 derniers messages
    if len(st.session_state["log_messages"]) > 20:
        st.session_state["log_messages"] = st.session_state["log_messages"][-20:]

def navigate_to(node_id: str, module: str):
    """Change le nœud actif dans l'arbre et le module affiché."""
    st.session_state["active_node"]   = node_id
    st.session_state["active_module"] = module

def get_rotor_status():
    """Retourne (label, couleur) du statut du rotor actif."""
    r = st.session_state.get("rotor")
    if r is None:
        return "Aucun rotor", "#C00000"
    name = st.session_state.get("rotor_name", "Rotor")
    return f"{name} · {len(r.nodes)} nœuds · {r.m:.1f} kg", "#22863A"

# =============================================================================
# COMPOSANT : HEADER DE L'APPLICATION
# =============================================================================
def render_header():
    rotor_label, rotor_color = get_rotor_status()
    ross_color = "#22863A" if ROSS_AVAILABLE else "#C00000"
    ross_label = f"ROSS {ROSS_VERSION}" if ROSS_AVAILABLE else "ROSS absent"

    st.markdown(f"""
    <div class="rl-header">
      <div>
        <span class="rl-header-title">⚙️ {APP_NAME}</span>
        <span style="color:rgba(255,255,255,0.5); margin:0 8px;">|</span>
        <span class="rl-header-sub">{APP_AUTHOR} — {APP_INST}</span>
      </div>
      <div style="display:flex; gap:8px; align-items:center;">
        <span class="rl-header-badge" style="background:rgba(255,255,255,0.1)">
          v{APP_VERSION}
        </span>
        <span class="rl-header-badge"
              style="background:{'rgba(34,134,58,0.3)' if ROSS_AVAILABLE else 'rgba(192,0,0,0.3)'}">
          {ross_label}
        </span>
        <span class="rl-header-badge"
              style="background:{'rgba(34,134,58,0.3)' if st.session_state['rotor'] else 'rgba(192,0,0,0.25)'}">
          🔩 {rotor_label}
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# COMPOSANT : MODEL TREE (panneau gauche)
# =============================================================================
def render_model_tree():
    """Arbre de navigation style COMSOL — panneau gauche."""

    active = st.session_state.get("active_node", "shaft")

    st.markdown("""
    <style>
    section[data-testid="stMain"] div[data-testid="stVerticalBlock"]
        div[data-testid="stButton"] > button {
        text-align       : left !important;
        justify-content  : flex-start !important;
        font-size        : 0.82em !important;
        font-weight      : 400 !important;
        background       : transparent !important;
        border           : none !important;
        border-left      : 3px solid transparent !important;
        border-radius    : 0 !important;
        padding          : 5px 8px 5px 18px !important;
        margin           : 1px 0 !important;
        box-shadow       : none !important;
        color            : #1A1A2E !important;
        transition       : all 0.15s !important;
    }
    section[data-testid="stMain"] div[data-testid="stVerticalBlock"]
        div[data-testid="stButton"] > button:hover {
        background       : rgba(31,92,139,0.09) !important;
        border-left-color: rgba(31,92,139,0.4) !important;
        color            : #1F5C8B !important;
    }
    </style>
    """, unsafe_allow_html=True)

    for section in MODEL_TREE:
        st.markdown(
            '<div class="rl-tree-section">'
            '{} {}'
            '</div>'.format(section["icon"], section["label"]),
            unsafe_allow_html=True
        )

        for item in section["children"]:
            is_active = (item["id"] == active)
            is_new    = item["module"] in ("M5", "M8")
            new_tag   = " [NEW]" if is_new else ""

            if is_active:
                st.markdown(
                    '<div style="'
                    'background:rgba(31,92,139,0.10);'
                    'border-left:3px solid #1F5C8B;'
                    'padding:5px 8px 5px 18px;'
                    'font-size:0.82em;'
                    'font-weight:600;'
                    'color:#1F5C8B;'
                    'margin:1px 0;'
                    '">{} &nbsp;{}{}</div>'.format(
                        item["icon"], item["label"], new_tag
                    ),
                    unsafe_allow_html=True
                )
            else:
                st.button(
                    "{}  {}{}".format(
                        item["icon"], item["label"], new_tag
                    ),
                    key="tree_{}".format(item["id"]),
                    use_container_width=True,
                    on_click=navigate_to,
                    args=(item["id"], item["module"]),
                )

    st.markdown("---")
    st.caption("Actions rapides")

    if ROSS_AVAILABLE:
        st.button(
            "📂 Charger compresseur",
            use_container_width=True,
            key="tree_load_comp",
            on_click=_load_compressor_example
        )

    if st.session_state.get("rotor") is not None:
        st.button(
            "🗑️ Réinitialiser",
            use_container_width=True,
            key="tree_reset",
            on_click=_reset_model
        )

def _load_compressor_example():
    """Charge le compresseur de référence ROSS."""
    try:
        with st.spinner("Chargement du compresseur..."):
            comp = rs.compressor_example()
            st.session_state["rotor"]       = comp
            st.session_state["rotor_name"]  = "Compresseur centrifuge (référence ROSS)"
            st.session_state["rotor_source"] = "compressor"
            # Synchronisation des tableaux M1
            shaft_data = [{"L (m)": el.L, "id_L (m)": el.idl, "od_L (m)": el.odl,
                           "id_R (m)": el.idr, "od_R (m)": el.odr}
                          for el in comp.shaft_elements]
            st.session_state["df_shaft"] = pd.DataFrame(shaft_data)
            disk_data = [{"nœud": d.n, "Masse (kg)": d.m,
                          "Id (kg.m²)": d.Id, "Ip (kg.m²)": d.Ip}
                         for d in comp.disk_elements]
            st.session_state["df_disk"]  = pd.DataFrame(disk_data)
            bear_data = []
            for b in comp.bearing_elements:
                kxx = b.kxx[0] if hasattr(b.kxx,'__iter__') else getattr(b,'kxx',0)
                kyy = b.kyy[0] if hasattr(b.kyy,'__iter__') else getattr(b,'kyy',0)
                kxy = b.kxy[0] if hasattr(b.kxy,'__iter__') else getattr(b,'kxy',0)
                cxx = b.cxx[0] if hasattr(b.cxx,'__iter__') else getattr(b,'cxx',0)
                cyy = b.cyy[0] if hasattr(b.cyy,'__iter__') else getattr(b,'cyy',0)
                bear_data.append({"nœud":b.n,"Type":"Palier",
                                  "kxx":kxx,"kyy":kyy,"kxy":kxy,"cxx":cxx,"cyy":cyy})
            st.session_state["df_bear"]  = pd.DataFrame(bear_data)
            add_log(f"Compresseur chargé : {len(comp.nodes)} nœuds, {comp.m:.1f} kg", "ok")
        st.rerun()
    except Exception as e:
        add_log(f"Erreur chargement compresseur : {e}", "err")
        st.error(str(e))

def _reset_model():
    """Réinitialise le modèle et tous les résultats."""
    for key in ["rotor", "res_static", "res_modal", "res_campbell",
                "res_ucs", "res_unbalance", "res_freq", "res_temporal"]:
        st.session_state[key] = None
    st.session_state["rotor_name"] = "Nouveau rotor"
    add_log("Modèle réinitialisé", "warn")
# =============================================================================
# COMPOSANT : BARRE DE LOG (bas du panneau droit)
# =============================================================================
def render_log_bar():
    """Barre de log style COMSOL en bas du panneau Graphics."""
    logs = st.session_state.get("log_messages", [])
    if not logs:
        st.markdown(
            '<div class="rl-log-bar">▶ RotorLab Suite 2.0 — Prêt.</div>',
            unsafe_allow_html=True
        )
        return
    # Affiche les 3 derniers messages
    lines = ""
    for log in logs[-3:]:
        css = {"ok":"rl-log-ok","warn":"rl-log-warn","err":"rl-log-err"}.get(log["level"],"")
        lines += f'<span class="{css}">{log["icon"]} [{log["ts"]}] {log["msg"]}</span><br>'
    st.markdown(f'<div class="rl-log-bar">{lines}</div>', unsafe_allow_html=True)

# =============================================================================
# COMPOSANT : BARRE DE NAVIGATION SUPÉRIEURE (mode : Simulation / Tuto / Dash)
# =============================================================================
def render_top_nav():
    """Barre de navigation entre les 3 modes principaux."""
    modes = {
        "dashboard" : "🏠 Tableau de Bord",
        "simulation": "🔬 Mode Simulation",
        "tutorial"  : "🎓 Mode Pédagogique",
        "copilot"   : "✨ SmartRotor Copilot",
    }
    current = st.session_state["nav_mode"]

    cols = st.columns(len(modes))
    for i, (key, label) in enumerate(modes.items()):
        with cols[i]:
            is_active = key == current
            btn_style = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_{key}",
                         use_container_width=True, type=btn_style):
                st.session_state["nav_mode"] = key
                st.rerun()

# =============================================================================
# ROUTAGE VERS LES MODULES
# =============================================================================
def route_to_module(module_id: str, node_id: str, col_settings, col_graphics):
    """Charge le bon module dans les panneaux Settings et Graphics."""

    if module_id == "M1" or node_id in ("material","parameters","shaft","disks","bearings"):
        from modules.m1_builder import render_m1
        render_m1(col_settings, col_graphics)

    elif module_id == "M2" or node_id == "static_modal":
        from modules.m2_modal import render_m2
        render_m2(col_settings, col_graphics)

    elif module_id == "M3" or node_id in ("campbell", "api_level1"):
        from modules.m3_campbell import render_m3
        render_m3(col_settings, col_graphics)

    elif module_id == "M4" or node_id in ("unbalance", "freq_resp"):
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
        # Fallback : afficher M1 par défaut
        from modules.m1_builder import render_m1
        render_m1(col_settings, col_graphics)

# =============================================================================
# MODES D'AFFICHAGE
# =============================================================================
def render_simulation_mode():
    """Mode principal : layout 3 panneaux style COMSOL."""

    # ── Disposition des 3 panneaux ──────────────────────────────────────
    # Ratio : Model Tree (1.5) | Settings (2) | Graphics (3)
    col_tree, col_settings, col_graphics = st.columns([1.5, 2, 3.5])

    with col_tree:
        render_model_tree()

    # ── Récupération du module actif ────────────────────────────────────
    module_id = st.session_state["active_module"]
    node_id   = st.session_state["active_node"]

    # ── Routage vers le module ──────────────────────────────────────────
    route_to_module(module_id, node_id, col_settings, col_graphics)


def render_dashboard():
    """Tableau de bord — aperçu global et accès rapide."""
    from datetime import datetime

    st.markdown(f"""
    <div style='text-align:center; padding:20px 0 30px;'>
      <h1 style='color:#1F5C8B; font-size:2.8em; margin:0; font-weight:800;'>
        ⚙️ RotorLab Suite 2.0
      </h1>
      <p style='color:#6B7280; font-size:1.1em; margin:4px 0 0;'>
        Plateforme Avancée de Simulation en Dynamique des Rotors
      </p>
      <p style='color:#9CA3AF; font-size:0.85em;'>
        {APP_AUTHOR} — {APP_INST}
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Statut rapide
    rotor = st.session_state.get("rotor")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="rl-metric-card">
          <div class="rl-metric-label">Statut ROSS</div>
          <div class="rl-metric-value" style="font-size:1em;color:{'#22863A' if ROSS_AVAILABLE else '#C00000'}">
            {'✅ ' + ROSS_VERSION if ROSS_AVAILABLE else '❌ Absent'}
          </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="rl-metric-card">
          <div class="rl-metric-label">Rotor actif</div>
          <div class="rl-metric-value" style="font-size:0.9em;color:{'#22863A' if rotor else '#C00000'}">
            {'✅ ' + str(len(rotor.nodes)) + ' nœuds' if rotor else '❌ Aucun'}
          </div>
        </div>""", unsafe_allow_html=True)
    with c3:
        n_done = len(st.session_state.get("tut_done", set()))
        st.markdown(f"""
        <div class="rl-metric-card">
          <div class="rl-metric-label">Tutoriels complétés</div>
          <div class="rl-metric-value">{n_done} / 6</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        n_res = sum(1 for k in ["res_modal","res_campbell","res_unbalance","res_temporal"]
                   if st.session_state.get(k) is not None)
        st.markdown(f"""
        <div class="rl-metric-card">
          <div class="rl-metric-label">Analyses calculées</div>
          <div class="rl-metric-value">{n_res} / 9</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Accès rapide modules
    st.markdown("### 🚀 Accès Rapide aux Modules")
    modules_grid = [
        ("M1","🏗️","Constructeur",    "Géométrie, Matériaux, Paliers",   "shaft"),
        ("M2","📊","Statique & Modal","Déflexion, Fréquences propres",    "static_modal"),
        ("M3","📈","Campbell + UCS",  "Stabilité, API 684, UCS Map",     "campbell"),
        ("M4","🌀","Balourd & H(jω)", "Bode, Polaire, ISO 1940",         "unbalance"),
        ("M5","💧","Paliers HD",      "BearingFluidFilm, coefficients",  "hd_bearings"),
        ("M6","⏱️","Temporel",        "Newmark, Orbites, Waterfall 3D",  "temporal"),
        ("M7","🔧","Défauts",         "Fissure, Désalignement, Frottement","faults"),
        ("M8","⚙️","MultiRotor",      "GearElement, Torsionnel",         "multirotor"),
        ("M9","📄","Rapport PDF",     "Export complet multi-sections",   "report"),
    ]

    cols = st.columns(3)
    for i, (mid, icon, title, desc, node) in enumerate(modules_grid):
        with cols[i % 3]:
            is_new = mid in ("M5","M8")
            new_badge = '<span class="rl-badge rl-badge-new">NEW v2</span>' if is_new else ''
            st.markdown(f"""
            <div class="rl-card-info" style="margin-bottom:4px;">
              <strong>{icon} {mid} — {title}</strong> {new_badge}<br>
              <small style="color:#6B7280;">{desc}</small>
            </div>""", unsafe_allow_html=True)
            if st.button(f"Ouvrir {mid}", key=f"dash_{mid}",
                         use_container_width=True, type="primary"):
                st.session_state["active_node"]   = node
                st.session_state["active_module"] = mid
                st.session_state["nav_mode"]      = "simulation"
                st.rerun()


def render_tutorial_mode():
    """Mode pédagogique — délégué au module tutorials."""
    from tutorials.tutorial_data import render_tutorials
    render_tutorials()


def render_copilot_mode():
    """Mode SmartRotor Copilot — plein écran."""
    from modules.ai_copilot import render_copilot_fullscreen
    render_copilot_fullscreen()


# =============================================================================
# POINT D'ENTRÉE PRINCIPAL
# =============================================================================
def main():
    # ── Header permanent ────────────────────────────────────────────────
    render_header()

    # ── Barre de navigation mode ─────────────────────────────────────────
    render_top_nav()
    st.markdown("<hr style='margin:4px 0 8px; border-color:#D0D8E4;'>",
                unsafe_allow_html=True)

    # ── Routage selon le mode actif ──────────────────────────────────────
    mode = st.session_state["nav_mode"]

    if mode == "simulation":
        render_simulation_mode()

    elif mode == "dashboard":
        render_dashboard()

    elif mode == "tutorial":
        render_tutorial_mode()

    elif mode == "copilot":
        render_copilot_mode()

    # ── Sidebar minimaliste ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"## ⚙️ {APP_NAME}")
        st.session_state["user_name"] = st.text_input(
            "👤 Nom :", st.session_state["user_name"])
        st.markdown("---")
        if ROSS_AVAILABLE:
            st.success(f"✅ ROSS {ROSS_VERSION}")
        else:
            st.error("❌ ROSS non installé")
            st.code("pip install ross-rotordynamics")
        rotor = st.session_state.get("rotor")
        if rotor:
            st.markdown("---")
            st.markdown("**🔩 Rotor actif :**")
            st.caption(f"{st.session_state.get('rotor_name','—')}")
            st.caption(f"{len(rotor.nodes)} nœuds · {rotor.m:.2f} kg")
        st.markdown("---")
        st.caption(f"v{APP_VERSION} · {APP_INST}")


if __name__ == "__main__":
    main()
