# =============================================================================
# modules/ai_copilot.py — SmartRotor Copilot v3.0 (Expert Edition)
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
#
# v3.0 — Nouvelles fonctionnalités :
#   • Interface utilisateur immersive type Modern LLM
#   • Sélecteur dynamique de modèles Gemini (Anti-Quota/404)
#   • Expert Diagnostic Vibratoire & Audit API 684
#   • Hardening absolu contre les rechargements Streamlit
# =============================================================================

import streamlit as st
import json
import numpy as np

try:
    import google.generativeai as genai
    GEMINI_OK = True
except ImportError:
    GEMINI_OK = False

# =============================================================================
# CSS GLOBAL DU COPILOT
# =============================================================================
_COPILOT_CSS = """
<style>
/* ── Hero Copilot ────────────────────────────────────────────────────── */
.cop-hero {
    background: linear-gradient(135deg, #0F1923 0%, #153F62 55%, #1F5C8B 100%);
    border-radius: 12px 12px 0 0;
    padding: 20px 24px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    border: 1.5px solid rgba(31,92,139,0.5);
    border-bottom: none;
}
.cop-hero-left { display: flex; align-items: center; gap: 14px; }
.cop-hero-orb {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, #1F5C8B 0%, #7B1FA2 100%);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3em;
    box-shadow: 0 0 18px rgba(123,31,162,0.35);
    flex-shrink: 0;
}
.cop-hero-title { color: #FFFFFF; font-weight: 800; font-size: 1.05em; letter-spacing: -0.2px; }
.cop-hero-sub   { color: rgba(255,255,255,0.55); font-size: 0.78em; margin-top: 2px; }
.cop-hero-tags  { display: flex; gap: 6px; flex-wrap: wrap; }
.cop-hero-tag {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.18);
    color: rgba(255,255,255,0.75);
    font-size: 0.70em; font-weight: 600;
    padding: 3px 9px; border-radius: 99px;
    letter-spacing: 0.03em;
}
.cop-hero-tag.active { background: rgba(34,134,58,0.3); border-color: rgba(34,134,58,0.6); color: #7FE5A0; }
.cop-hero-tag.warn   { background: rgba(245,124,0,0.25); border-color: rgba(245,124,0,0.5);   color: #FFB74D; }
.cop-hero-tag.err    { background: rgba(192,0,0,0.25);   border-color: rgba(192,0,0,0.5);     color: #FF8F8F; }

/* ── Panneau Config ──────────────────────────────────────────────────── */
.cop-config-wrap {
    background: #F7F9FC;
    border: 1.5px solid #D0D8E4;
    border-radius: 10px;
    padding: 0;
    overflow: hidden;
    margin-bottom: 14px;
}
.cop-config-header {
    background: #153F62;
    color: #FFFFFF;
    padding: 9px 14px;
    font-size: 0.78em;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    display: flex;
    align-items: center;
    gap: 7px;
}
.cop-config-body { padding: 12px 14px; }
.cop-key-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    border-radius: 8px;
    font-size: 0.80em;
    font-weight: 600;
    margin-top: 8px;
}
.cop-key-status.ok  { background: #E8F5E9; color: #1B5E20; border: 1px solid #A5D6A7; }
.cop-key-status.off { background: #FFF8E1; color: #E65100; border: 1px solid #FFCC80; }
.cop-key-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.cop-key-dot.ok  { background: #22863A; }
.cop-key-dot.off { background: #F57C00; }

/* ── Contexte rotor ──────────────────────────────────────────────────── */
.cop-ctx-wrap { background: #FFFFFF; border: 1.5px solid #D0D8E4; border-radius: 10px; overflow: hidden; margin-bottom: 14px; }
.cop-ctx-header { background: linear-gradient(90deg, #0F2D4A, #1F5C8B); color: #FFFFFF; padding: 8px 14px; font-size: 0.76em; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; }
.cop-ctx-body { padding: 10px 12px; }
.cop-ctx-row  { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; border-bottom: 1px solid #F0F4FF; font-size: 0.80em; }
.cop-ctx-row:last-child { border-bottom: none; }
.cop-ctx-label { color: #6B7280; }
.cop-ctx-val   { font-weight: 700; color: #1A1A2E; }
.cop-ctx-val.ok   { color: #22863A; }
.cop-ctx-val.err  { color: #C00000; }
.cop-ctx-val.warn { color: #C55A11; }

/* ── Style du Chat ───────────────────────────────────────────────────── */
.stChatMessage { padding: 1.2rem 1.5rem !important; border-radius: 12px; margin-bottom: 12px; }
.stChatMessageContent { font-size: 1.05em; line-height: 1.6; }
</style>
"""

# =============================================================================
# INITIALISATION
# =============================================================================
def _init_copilot_state():
    defaults = {
        "copilot_chat_history":    [],
        "copilot_api_key":         "",
        "copilot_model_choice":    "",
        "copilot_clear_requested": False,
        "copilot_pending_response": None,
        "copilot_is_processing":    False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    if not st.session_state["copilot_api_key"]:
        try:
            st.session_state["copilot_api_key"] = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass


# =============================================================================
# POINTS D'ENTRÉE PUBLICS
# =============================================================================
def render_copilot(col_settings, col_graphics):
    _init_copilot_state()
    with col_settings:
        st.markdown(_COPILOT_CSS, unsafe_allow_html=True)
        _render_settings_panel()
    with col_graphics:
        _render_chat_area()


def render_copilot_fullscreen():
    _init_copilot_state()
    st.markdown(_COPILOT_CSS, unsafe_allow_html=True)
    _render_cop_hero()
    col1, col2 = st.columns([1, 2.8])
    with col1:
        _render_settings_panel(compact=False)
    with col2:
        _render_chat_area_inner()


# =============================================================================
# HERO
# =============================================================================
def _render_cop_hero():
    api_key = st.session_state.get("copilot_api_key", "")
    rotor   = st.session_state.get("rotor")
    n_msgs  = len(st.session_state.get("copilot_chat_history", []))

    tag_gemini = ("active", "Gemini IA actif") if (GEMINI_OK and api_key) else \
                 ("warn",   "Mode hors-ligne") if GEMINI_OK else \
                 ("err",    "Gemini absent")
    tag_rotor  = ("active", "{} nœuds".format(len(rotor.nodes))) if rotor \
                 else ("warn", "Sans rotor")

    tags_html = ""
    for cls, lbl in [tag_gemini, ("", "ROSS OK"), tag_rotor, ("", "{} messages".format(n_msgs))]:
        tags_html += '<span class="cop-hero-tag {}">{}</span>'.format(cls, lbl)

    st.markdown("""
    <div class="cop-hero">
      <div class="cop-hero-left">
        <div class="cop-hero-orb">✨</div>
        <div>
          <div class="cop-hero-title">SmartRotor Copilot</div>
          <div class="cop-hero-sub">Assistant IA spécialisé en dynamique des rotors</div>
        </div>
      </div>
      <div class="cop-hero-tags">{tags}</div>
    </div>
    """.format(tags=tags_html), unsafe_allow_html=True)


# =============================================================================
# PANNEAU SETTINGS
# =============================================================================
def _render_settings_panel(compact=True):
    if not compact:
        _render_cop_hero()

    st.markdown("""
    <div class="cop-config-wrap">
      <div class="cop-config-header">⚙️ Configuration Gemini</div>
      <div class="cop-config-body">
    """, unsafe_allow_html=True)

    api_key = st.session_state.get("copilot_api_key", "")
    st.text_input(
        "Clé API Google Gemini",
        value=api_key,
        type="password",
        placeholder="AIza...",
        help="https://aistudio.google.com/apikey — gratuit",
        key="copilot_key_input",
    )

    # Récupération dynamique des modèles
    model_options = []
    if api_key and GEMINI_OK:
        try:
            genai.configure(api_key=api_key)
            for m in genai.list_models():
                if "generateContent" in m.supported_generation_methods:
                    model_options.append(m.name.replace("models/", ""))
        except Exception:
            pass

    if not model_options:
        model_options = ["gemini-1.5-flash", "gemini-1.5-pro-latest", "gemini-pro"]

    current_model = st.session_state.get("copilot_model_choice", "")
    if not current_model or current_model not in model_options:
        current_model = model_options[0]
        
    index_model = model_options.index(current_model)
    
    st.selectbox(
        "Modèle IA",
        options=model_options,
        index=index_model,
        help="Changez de modèle si vous atteignez la limite de requêtes (Quota).",
        key="copilot_model_select"
    )

    c1, c2 = st.columns(2)
    with c1:
        st.button("Enregistrer", key="copilot_key_save", use_container_width=True, type="primary", on_click=_cb_save_config)
    with c2:
        st.button("Effacer", key="copilot_key_clear", use_container_width=True, on_click=_cb_clear_api_key)

    if api_key and GEMINI_OK:
        st.markdown(f"""
        <div class="cop-key-status ok"><div class="cop-key-dot ok"></div>
          Connecté · {api_key[:4]}...{api_key[-4:]}
        </div>""", unsafe_allow_html=True)
    elif not GEMINI_OK:
        st.markdown('<div class="cop-key-status off"><div class="cop-key-dot off"></div>google-generativeai non installé</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="cop-key-status off"><div class="cop-key-dot off"></div>Mode hors-ligne actif</div>', unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

    # ── Contexte rotor ────────────────────────────────────────────────────
    context = _build_context()
    rotor   = st.session_state.get("rotor")

    st.markdown("""
    <div class="cop-ctx-wrap">
      <div class="cop-ctx-header">🔩 Contexte du rotor actif</div>
      <div class="cop-ctx-body">
    """, unsafe_allow_html=True)

    if rotor:
        st.markdown(f"""
        <div class="cop-ctx-row"><span class="cop-ctx-label">Nœuds / DDL</span><span class="cop-ctx-val ok">{context.get('n_nodes')} / {context.get('ndof')}</span></div>
        <div class="cop-ctx-row"><span class="cop-ctx-label">Masse totale</span><span class="cop-ctx-val">{context.get('mass_kg'):.2f} kg</span></div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="cop-ctx-row"><span class="cop-ctx-label">Rotor</span><span class="cop-ctx-val err">Non chargé</span></div>', unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    if context.get("modal"):
        fn_list = context["modal"]["fn_hz"]
        ld_list = context["modal"]["log_dec"]
        st.markdown('<div class="cop-ctx-wrap"><div class="cop-ctx-header" style="background:linear-gradient(90deg,#1A5C3A,#22863A);">📊 Modes propres</div><div class="cop-ctx-body">', unsafe_allow_html=True)
        mode_rows = ""
        for i, (f, ld) in enumerate(zip(fn_list, ld_list)):
            dot_cls = "err" if ld <= 0 else "warn" if ld < 0.1 else "ok"
            mode_rows += f'<div class="cop-ctx-row"><span style="color:#6B7280;font-size:0.75em;">M{i+1}</span><span style="font-weight:700;">{f:.2f} Hz</span><span style="color:#6B7280;">δ={ld:.4f}</span><div class="cop-key-dot {dot_cls}"></div></div>'
        st.markdown(mode_rows, unsafe_allow_html=True)
        n_inst = context["modal"]["n_instable"]
        if n_inst > 0:
            st.error(f"⚠️ {n_inst} mode(s) INSTABLE(S) détecté(s) !")
        st.markdown("</div></div>", unsafe_allow_html=True)

    if context.get("api684"):
        score = context["api684"]["score"]
        cls   = "ok" if score >= 80 else "warn" if score >= 50 else "off"
        st.markdown(f'<div class="cop-key-status {cls}" style="margin-top:8px;"><div class="cop-key-dot {cls}"></div>API 684 — Score {score:.0f}%</div>
