# =============================================================================
# modules/ai_copilot.py — SmartRotor Copilot v3.2 (Fixed Layout)
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
#
# v3.2 — Mise en page fixe :
#   • Hero toujours visible (position: sticky)
#   • Panneau gauche toujours visible (CSS :has() sticky)
#   • Zone de messages scrollable indépendamment (st.container)
#   • Pas de double scrollbar
#   • Comportement natif st.chat_input préservé
#   • Auto-scroll vers le dernier message (components.html)
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
# CSS GLOBAL
# =============================================================================
_COPILOT_CSS = """
<style>

/* ════════════════════════════════════════════════════
   COMPOSANTS VISUELS
   ════════════════════════════════════════════════════ */

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
.cop-hero-tag.active   { background: rgba(34,134,58,0.3);    border-color: rgba(34,134,58,0.6);    color: #7FE5A0; }
.cop-hero-tag.warn     { background: rgba(245,124,0,0.25);   border-color: rgba(245,124,0,0.5);    color: #FFB74D; }
.cop-hero-tag.err      { background: rgba(192,0,0,0.25);     border-color: rgba(192,0,0,0.5);      color: #FF8F8F; }
.cop-hero-tag.exchange { background: rgba(123,31,162,0.30);  border-color: rgba(179,100,228,0.6);  color: #D8A8FF; font-weight: 700; }

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
    display: flex; align-items: center; gap: 8px;
    padding: 8px 10px; border-radius: 8px;
    font-size: 0.80em; font-weight: 600; margin-top: 8px;
}
.cop-key-status.ok  { background: #E8F5E9; color: #1B5E20; border: 1px solid #A5D6A7; }
.cop-key-status.off { background: #FFF8E1; color: #E65100; border: 1px solid #FFCC80; }
.cop-key-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.cop-key-dot.ok  { background: #22863A; }
.cop-key-dot.off { background: #F57C00; }

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

.stChatMessage { padding: 1.2rem 1.5rem !important; border-radius: 12px; margin-bottom: 12px; }
.stChatMessageContent { font-size: 1.05em; line-height: 1.6; }

/* ════════════════════════════════════════════════════
   LAYOUT FIXE — éléments toujours visibles
   ════════════════════════════════════════════════════ */

/* 1. Hero : sticky au sommet du viewport */
.cop-hero {
    position: sticky !important;
    top: 0 !important;
    z-index: 500 !important;
}

/* 2. Panneau gauche (settings) : sticky dans le mode plein écran copilot
      Cible le premier stVerticalBlock du stHorizontalBlock qui
      contient .cop-config-wrap (sélecteur :has() — Chrome 105+,
      Firefox 121+, Safari 15.4+; dégradation gracieuse sinon). */
[data-testid="stHorizontalBlock"]:has(.cop-config-wrap)
    > [data-testid="column"]:first-child
    > [data-testid="stVerticalBlock"] {
    position       : sticky;
    top            : 0;
    max-height     : 100vh;
    overflow-y     : auto;
    overflow-x     : hidden;
    scrollbar-width: thin;
    scrollbar-color: rgba(31,92,139,0.4) transparent;
    padding-bottom : 20px;
}
[data-testid="stHorizontalBlock"]:has(.cop-config-wrap)
    > [data-testid="column"]:first-child
    > [data-testid="stVerticalBlock"]::-webkit-scrollbar       { width: 4px; }
[data-testid="stHorizontalBlock"]:has(.cop-config-wrap)
    > [data-testid="column"]:first-child
    > [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb {
    background   : rgba(31,92,139,0.45);
    border-radius: 4px;
}

/* 3. Container de messages scrollable — supprime la bordure Streamlit */
[data-testid="stVerticalBlockBorderWrapper"] {
    border    : none !important;
    box-shadow: none !important;
}

/* 4. Scroll fluide sur toute la page */
html { scroll-behavior: smooth; }

/* 5. Scrollbar de la zone de messages */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    scrollbar-width: thin;
    scrollbar-color: rgba(31,92,139,0.35) transparent;
}
[data-testid="stVerticalBlockBorderWrapper"] > div::-webkit-scrollbar       { width: 5px; }
[data-testid="stVerticalBlockBorderWrapper"] > div::-webkit-scrollbar-thumb {
    background   : rgba(31,92,139,0.4);
    border-radius: 4px;
}

</style>
"""

# =============================================================================
# INITIALISATION
# =============================================================================
def _init_copilot_state():
    defaults = {
        "copilot_chat_history":         [],
        "copilot_api_key":              "",
        "copilot_model_choice":         "",
        "copilot_clear_requested":      False,
        "copilot_pending_response":     None,
        "copilot_is_processing":        False,
        "copilot_pending_quick_prompt": None,
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
    """Mode simulation : héro dans col_graphics, settings dans col_settings."""
    _init_copilot_state()
    with col_settings:
        st.markdown(_COPILOT_CSS, unsafe_allow_html=True)
        _render_settings_panel()
    with col_graphics:
        _render_chat_area()


def render_copilot_fullscreen():
    """Mode plein écran copilot : héro pleine largeur, 2 colonnes dessous."""
    _init_copilot_state()
    st.markdown(_COPILOT_CSS, unsafe_allow_html=True)
    _render_cop_hero()                        # ← sticky full-width au scroll
    col1, col2 = st.columns([1, 2.8])
    with col1:
        _render_settings_panel(compact=False) # ← sticky via :has() CSS
    with col2:
        _render_chat_area_inner()             # ← zone scrollable + chat_input


# =============================================================================
# HERO
# =============================================================================
def _render_cop_hero():
    api_key = st.session_state.get("copilot_api_key", "")
    rotor   = st.session_state.get("rotor")
    history = st.session_state.get("copilot_chat_history", [])

    n_user      = sum(1 for m in history if m["role"] == "user")
    n_assistant = sum(1 for m in history if m["role"] == "assistant")
    n_exchanges = min(n_user, n_assistant)
    exchange_lbl = "💬 {} échange{}".format(n_exchanges, "s" if n_exchanges > 1 else "")

    tag_gemini = ("active", "Gemini IA actif") if (GEMINI_OK and api_key) else \
                 ("warn",   "Mode hors-ligne") if GEMINI_OK else \
                 ("err",    "Gemini absent")
    tag_rotor  = ("active", "{} nœuds".format(len(rotor.nodes))) if rotor \
                 else ("warn", "Sans rotor")

    tags_html = ""
    for cls, lbl in [tag_gemini, ("", "ROSS OK"), tag_rotor]:
        tags_html += '<span class="cop-hero-tag {}">{}</span>'.format(cls, lbl)
    ex_cls     = "exchange" if n_exchanges > 0 else ""
    tags_html += '<span class="cop-hero-tag {}">{}</span>'.format(ex_cls, exchange_lbl)

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
        model_options = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.5-flash"]

    current_model = st.session_state.get("copilot_model_choice", "")
    if not current_model or current_model not in model_options:
        current_model = model_options[2]

    st.selectbox(
        "Modèle IA",
        options=model_options,
        index=model_options.index(current_model),
        help="Changez de modèle si vous atteignez la limite de requêtes.",
        key="copilot_model_select"
    )

    c1, c2 = st.columns(2)
    with c1:
        st.button("Enregistrer", key="copilot_key_save", use_container_width=True,
                  type="primary", on_click=_cb_save_config)
    with c2:
        st.button("Effacer", key="copilot_key_clear", use_container_width=True,
                  on_click=_cb_clear_api_key)

    if api_key and GEMINI_OK:
        st.markdown("""
        <div class="cop-key-status ok"><div class="cop-key-dot ok"></div>
          Connecté · {}...{}
        </div>""".format(api_key[:4], api_key[-4:]), unsafe_allow_html=True)
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
        st.markdown("""
        <div class="cop-ctx-row"><span class="cop-ctx-label">Nœuds / DDL</span>
          <span class="cop-ctx-val ok">{} / {}</span></div>
        <div class="cop-ctx-row"><span class="cop-ctx-label">Masse totale</span>
          <span class="cop-ctx-val">{:.2f} kg</span></div>
        """.format(context.get("n_nodes"), context.get("ndof"),
                   context.get("mass_kg", 0)), unsafe_allow_html=True)
    else:
        st.markdown('<div class="cop-ctx-row"><span class="cop-ctx-label">Rotor</span>'
                    '<span class="cop-ctx-val err">Non chargé</span></div>',
                    unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    if context.get("modal"):
        fn_list = context["modal"]["fn_hz"]
        ld_list = context["modal"]["log_dec"]
        st.markdown('<div class="cop-ctx-wrap">'
                    '<div class="cop-ctx-header" style="background:linear-gradient(90deg,#1A5C3A,#22863A);">'
                    '📊 Modes propres</div><div class="cop-ctx-body">', unsafe_allow_html=True)
        mode_rows = ""
        for i, (f, ld) in enumerate(zip(fn_list, ld_list)):
            dot_cls = "err" if ld <= 0 else "warn" if ld < 0.1 else "ok"
            mode_rows += (
                '<div class="cop-ctx-row">'
                '<span style="color:#6B7280;font-size:0.75em;">M{}</span>'
                '<span style="font-weight:700;">{:.2f} Hz</span>'
                '<span style="color:#6B7280;">δ={:.4f}</span>'
                '<div class="cop-key-dot {}"></div></div>'.format(i + 1, f, ld, dot_cls)
            )
        st.markdown(mode_rows, unsafe_allow_html=True)
        if context["modal"]["n_instable"] > 0:
            st.error("⚠️ {} mode(s) INSTABLE(S) !".format(context["modal"]["n_instable"]))
        st.markdown("</div></div>", unsafe_allow_html=True)

    if context.get("api684"):
        score = context["api684"]["score"]
        cls   = "ok" if score >= 80 else "warn" if score >= 50 else "off"
        st.markdown(
            '<div class="cop-key-status {c}" style="margin-top:8px;">'
            '<div class="cop-key-dot {c}"></div>API 684 — Score {s:.0f}%</div>'.format(
                c=cls, s=score), unsafe_allow_html=True)


# =============================================================================
# ZONE DE CHAT
# =============================================================================
def _render_chat_area():
    """Wrapper appelé en mode simulation (héro dans la colonne graphique)."""
    st.markdown(_COPILOT_CSS, unsafe_allow_html=True)
    _render_cop_hero()
    _render_chat_area_inner()


def _render_chat_area_inner():
    """Cœur de la zone de chat : messages scrollables + input fixe en bas."""

    # ── Effacement ───────────────────────────────────────────────────────
    if st.session_state.get("copilot_clear_requested"):
        st.session_state["copilot_chat_history"]         = []
        st.session_state["copilot_clear_requested"]      = False
        st.session_state["copilot_is_processing"]        = False
        st.session_state["copilot_pending_quick_prompt"] = None

    history = st.session_state.get("copilot_chat_history", [])

    # ── Bouton Nouveau Chat ───────────────────────────────────────────────
    if history:
        _, col_clear = st.columns([5, 1])
        with col_clear:
            st.button("✨ Nouveau Chat", key="copilot_clear_btn",
                      use_container_width=True, on_click=_cb_clear_history)

    # ── Écran d'accueil ───────────────────────────────────────────────────
    if not history:
        st.markdown("""
        <div style="display:flex;flex-direction:column;justify-content:center;
                    align-items:center;padding-top:10vh;padding-bottom:6vh;text-align:center;">
          <div style="font-size:3.8em;font-weight:600;line-height:1.1;letter-spacing:-1.5px;">
            <span style="background:-webkit-linear-gradient(135deg,#1F5C8B,#7B1FA2);
                         -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
              Bonjour.</span>
          </div>
          <div style="font-size:2.2em;font-weight:500;color:#8A9BB0;
                      line-height:1.2;letter-spacing:-0.5px;margin-top:8px;">
            Comment puis-je optimiser votre rotor aujourd'hui ?
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(
            "<div style='text-align:center;color:#6B7280;font-size:0.85em;"
            "margin-bottom:15px;font-weight:700;text-transform:uppercase;"
            "letter-spacing:0.08em;'>Suggestions pour démarrer</div>",
            unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        prompts_data = [
            (c1, "🏗️ Modélisation",  "Créer un rotor avec ROSS en Python"),
            (c2, "🩺 Diagnostic M7", "Diagnostiquer une forte composante vibratoire à 2X la vitesse de rotation"),
            (c3, "⚖️ Audit API 684", "Rédiger un audit de conformité API 684 basé sur les données actuelles"),
            (c4, "💧 Stabilisation", "Comment stabiliser ce rotor (Log Decrétement négatif) ?"),
        ]
        for col, label, prompt in prompts_data:
            with col:
                if st.button(label, help=prompt,
                             key="qp_hero_{}".format(label),
                             use_container_width=True):
                    st.session_state["copilot_chat_history"].append(
                        {"role": "user", "content": prompt})
                    st.session_state["copilot_pending_quick_prompt"] = prompt
                    st.rerun()

    else:
        # ── ZONE DE MESSAGES SCROLLABLE ───────────────────────────────────
        # st.container(height=X) crée un bloc scrollable natif Streamlit.
        # La hauteur est ajustée dynamiquement via JS injecté ci-dessous.
        # Valeur initiale : 500 px (raisonnable sur tous les écrans).
        msg_container = _make_scrollable_container(default_height=500)

        with msg_container:
            for msg in history:
                avatar = "🧑‍💻" if msg["role"] == "user" else "✨"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])

        # JS : adapte la hauteur du container au viewport et scroll en bas.
        _inject_layout_js()

    # ── Traitement d'un quick prompt en attente ───────────────────────────
    pending = st.session_state.get("copilot_pending_quick_prompt")
    if pending:
        st.session_state["copilot_pending_quick_prompt"] = None
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(pending)
        with st.chat_message("assistant", avatar="✨"):
            with st.spinner("SmartRotor Copilot analyse votre question…"):
                response = _call_gemini(
                    pending, _build_context(),
                    st.session_state["copilot_chat_history"][:-1])
                st.markdown(response)
        st.session_state["copilot_chat_history"].append(
            {"role": "assistant", "content": response})
        st.rerun()
        return

    # ── Saisie manuelle ───────────────────────────────────────────────────
    # st.chat_input est rendu par Streamlit HORS du container → reste fixe en bas.
    user_input = st.chat_input(
        "Posez votre question en dynamique des rotors…",
        key="copilot_chat_input")

    if user_input:
        st.session_state["copilot_chat_history"].append(
            {"role": "user", "content": user_input})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input)
        with st.chat_message("assistant", avatar="✨"):
            with st.spinner("SmartRotor Copilot analyse votre question…"):
                response = _call_gemini(
                    user_input, _build_context(),
                    st.session_state["copilot_chat_history"][:-1])
                st.markdown(response)
        st.session_state["copilot_chat_history"].append(
            {"role": "assistant", "content": response})
        st.rerun()


# =============================================================================
# HELPERS LAYOUT
# =============================================================================
def _make_scrollable_container(default_height: int = 500):
    """
    Crée un st.container scrollable (Streamlit ≥ 1.31).
    Fallback transparent sur les versions antérieures.
    """
    try:
        return st.container(height=default_height, border=False)
    except TypeError:
        # Streamlit < 1.31 : pas de paramètre height → fallback
        return st.container()


def _inject_layout_js():
    """
    Injecte du JavaScript via st.components.v1.html (iframe height=0).
    Le script accède au DOM parent pour :
      1. Recalculer et fixer la hauteur du container de messages.
      2. Scroller automatiquement vers le dernier message.
    """
    try:
        import streamlit.components.v1 as components

        js_code = """
<script>
(function() {
    var doc = (window.parent || window).document;

    function computeAndApply() {
        /* ── Éléments de référence ── */
        var hero      = doc.querySelector('.cop-hero');
        var chatInput = doc.querySelector('[data-testid="stChatInput"]');
        var rlHeader  = doc.querySelector('.rl-header');   /* nav RotorLab */
        var topNav    = doc.querySelector('[data-testid="stToolbar"]');

        var heroH     = hero      ? hero.getBoundingClientRect().height      : 100;
        var inputH    = chatInput ? chatInput.getBoundingClientRect().height + 24 : 90;
        var headerH   = rlHeader  ? rlHeader.getBoundingClientRect().height  : 0;
        var navH      = topNav    ? topNav.getBoundingClientRect().height     : 0;

        /* Marge de sécurité (bouton Nouveau Chat + padding) */
        var margin = 80;
        var availH = Math.max(
            300,
            window.parent.innerHeight - heroH - inputH - headerH - navH - margin
        );

        /* ── Cible : stVerticalBlockBorderWrapper (container Streamlit) ── */
        var wrappers = doc.querySelectorAll(
            '[data-testid="stVerticalBlockBorderWrapper"]');
        wrappers.forEach(function(w) {
            /* Vérifier que ce wrapper est dans la zone copilot */
            if (!w.closest('[data-testid="stChatMessageContainer"]') &&
                !w.closest('.cop-chat-zone')) {
                w.style.height    = availH + 'px';
                w.style.maxHeight = availH + 'px';
            }
        });

        /* ── Auto-scroll vers le dernier message ── */
        var msgs = doc.querySelectorAll('[data-testid="stChatMessage"]');
        if (msgs.length > 0) {
            msgs[msgs.length - 1].scrollIntoView({
                behavior : 'smooth',
                block    : 'end'
            });
        }
    }

    /* Appels décalés pour laisser Streamlit finir de rendre */
    setTimeout(computeAndApply, 200);
    setTimeout(computeAndApply, 600);
    setTimeout(computeAndApply, 1200);

    /* Recalcul au redimensionnement de la fenêtre */
    var resizeTimer;
    window.parent.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(computeAndApply, 150);
    });
})();
</script>
"""
        components.html(js_code, height=0, scrolling=False)
    except Exception:
        pass   # Dégradation gracieuse si components non disponible


# =============================================================================
# CALLBACKS
# =============================================================================
def _cb_clear_history():
    st.session_state["copilot_clear_requested"]      = True
    st.session_state["copilot_pending_quick_prompt"] = None


def _cb_save_config():
    st.session_state["copilot_api_key"]      = \
        st.session_state.get("copilot_key_input", "").strip()
    st.session_state["copilot_model_choice"] = \
        st.session_state.get("copilot_model_select", "")


def _cb_clear_api_key():
    st.session_state["copilot_api_key"]   = ""
    st.session_state["copilot_key_input"] = ""


# =============================================================================
# CONTEXTE SESSION
# =============================================================================
def _build_context() -> dict:
    rotor  = st.session_state.get("rotor")
    modal  = st.session_state.get("res_modal")
    df_api = st.session_state.get("df_api")

    ctx = {"rotor_loaded": rotor is not None}
    if rotor:
        ctx["n_nodes"] = len(rotor.nodes)
        ctx["mass_kg"] = round(float(rotor.m), 2)
        ctx["ndof"]    = rotor.ndof

    if modal:
        fn = modal.wn / (2 * np.pi)
        ld = getattr(modal, "log_dec", np.zeros(len(fn)))
        n  = min(6, len(fn))
        ctx["modal"] = {
            "fn_hz":      [round(float(v), 2) for v in fn[:n]],
            "log_dec":    [round(float(v), 4) for v in ld[:n]],
            "n_instable": int(sum(1 for v in ld[:n] if v <= 0)),
        }

    if df_api is not None and not df_api.empty:
        api_p = st.session_state.get("api_params", {})
        ctx["api684"] = {
            "score":  api_p.get("score", 0),
            "op_rpm": api_p.get("op_rpm", 0),
        }
    return ctx


# =============================================================================
# APPEL GEMINI
# =============================================================================
def _call_gemini(user_msg: str, context: dict, history: list) -> str:
    if not GEMINI_OK:
        return _fallback(user_msg, context)

    api_key = st.session_state.get("copilot_api_key", "")
    if not api_key:
        return ("⚠️ **Aucune clé API configurée.**\n\n"
                "Saisissez votre clé Gemini dans le panneau de configuration.\n\n---\n"
                "**Réponse hors-ligne :**\n\n" + _fallback(user_msg, context))

    try:
        genai.configure(api_key=api_key)
        model_name = st.session_state.get("copilot_model_choice", "gemini-2.0-flash")

        system_prompt = (
                "Tu es SmartRotor Copilot, un ingénieur expert en dynamique des "
                "rotors, mécanique vibratoire et spécialiste absolu de la "
                "bibliothèque Python ROSS.\n\n"
                "DOMAINES D'EXPERTISE :\n"
                "- Modélisation ROSS (ShaftElement, DiskElement, BearingElement, "
                "GearElement, MultiRotor)\n"
                "- Analyses : modale, diagramme de Campbell, réponse au balourd, "
                "intégration temporelle, détection de défauts\n"
                "- Phénomènes avancés : orbites, instabilités (whirl/whip), paliers hydrodynamiques\n"
                "- Normes & références : API 684, ISO 1940, ISO 7919-3\n"
                "- Outils & concepts : Carte UCS, systèmes MultiRotor\n\n"
                "RÈGLES DE RÉPONSE :\n"
                "1. Sois précis, scientifique et pédagogique. Structure tes réponses en Markdown "
                "(titres, listes, tableaux si pertinent).\n"
                "2. Fournis systématiquement du code ROSS fonctionnel, commenté et exécutable "
                "lorsque cela éclaire la réponse. Utilise les balises ```python.\n"
                "3. Personnalise chaque réponse en t'appuyant explicitement sur les paramètres "
                "du rotor fournis dans le contexte ci-dessous.\n"
                "4. POLITIQUE LINGUISTIQUE : Réponds par défaut en français. Si l'utilisateur "
                "s'exprime dans une autre langue ou demande explicitement une réponse dans une "
                "langue spécifique, adapte-toi immédiatement à sa demande. Conserve la même "
                "rigueur technique, la structure Markdown et la terminologie internationale "
                "(ex. : whirl/whip, Campbell, UCS, mode shape) quelle que soit la langue utilisée.\n\n"
                "CONTEXTE ACTUEL DU ROTOR :\n"
                + json.dumps(context, ensure_ascii=False, indent=2)
                )


        model = genai.GenerativeModel(model_name)
        gemini_history = [
            {"role": "user",  "parts": [system_prompt]},
            {"role": "model", "parts": ["Compris ! Je suis SmartRotor Copilot, prêt."]},
        ]
        for h in history[-8:]:
            role = "user" if h["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [h["content"]]})

        chat     = model.start_chat(history=gemini_history)
        response = chat.send_message(user_msg)
        return response.text

    except Exception as e:
        err = str(e)
        if "404" in err:
            return ("⚠️ **Modèle IA non trouvé.** Sélectionnez un autre modèle.\n\n---\n"
                    + _fallback(user_msg, context))
        if any(k in err.upper() for k in ["API_KEY", "401", "403", "INVALID"]):
            return "❌ **Clé API invalide ou expirée.**\n\n---\n" + _fallback(user_msg, context)
        if "429" in err or "quota" in err.lower():
            return ("⏳ **Quota Gemini dépassé.** Patientez ou changez de modèle.\n\n---\n"
                    + _fallback(user_msg, context))
        return "⚠️ **Erreur Gemini :** `{}`\n\n---\n".format(err) + _fallback(user_msg, context)


# =============================================================================
# FALLBACK HORS-LIGNE
# =============================================================================
def _fallback(user_msg: str, context: dict) -> str:
    msg_lower = user_msg.lower()
    ctx_info  = ""
    if context.get("rotor_loaded"):
        ctx_info = "\n\n---\n*Rotor : {} nœuds, {} kg*".format(
            context.get("n_nodes", "?"), context.get("mass_kg", "?"))

    responses = {
        ("2x", "vibration", "diagnosti", "symptôme"): (
            "## 🩺 Diagnostic Vibratoire\n\n"
            "Une forte composante à **2X** indique une asymétrie. Causes probables :\n"
            "1. **Désalignement** des paliers ou de l'accouplement.\n"
            "2. **Fissure transverse** (raideur variable 2 fois/tour).\n"
            "3. **Asymétrie géométrique** (rotor à 2 pôles).\n\n"
            "*Action :* Module **M7** → Défauts → Fissure ou Désalignement."
        ),
        ("stabilis", "log dec", "instable"): (
            "## 🛡️ Optimisation de la Stabilité\n\n"
            "- Réduire la raideur croisée $K_{xy}$ des paliers HD.\n"
            "- Augmenter l'amortissement direct $C_{xx}$, $C_{yy}$.\n"
            "- Adopter des paliers **Tilting Pad** (pas de $K_{xy}$).\n"
            "- Déplacer la première fréquence propre en modifiant la géométrie."
        ),
        ("api 684", "audit", "conformit"): (
            "## 📋 Audit Normatif API 684\n\n"
            "**Critères :**\n"
            "1. Marge de séparation ≥ 15-25% autour de Nop.\n"
            "2. Log Décrément $\\delta \\geq 0.1$ pour tous les modes.\n\n"
            "*Action :* Module **M3** → onglet API 684."
        ),
        ("code", "script", "python", "ross"): (
            "## 💻 Exemple ROSS\n\n"
            "```python\nimport ross as rs\nimport numpy as np\n\n"
            "steel = rs.Material(name='Steel', rho=7810, E=211e9, G_s=81.2e9)\n"
            "shaft = [rs.ShaftElement(L=0.25, idl=0, odl=0.05, material=steel)\n"
            "         for _ in range(6)]\n"
            "disk  = rs.DiskElement(n=3, m=15.0, Id=0.025, Ip=0.047)\n"
            "b0    = rs.BearingElement(n=0, kxx=1e7, kyy=1e7, cxx=500, cyy=500)\n"
            "b6    = rs.BearingElement(n=6, kxx=1e7, kyy=1e7, cxx=500, cyy=500)\n"
            "rotor = rs.Rotor(shaft, [disk], [b0, b6])\n"
            "modal = rotor.run_modal(speed=0)\n"
            "print(modal.wn / (2*np.pi))  # fn en Hz\n```"
        ),
    }

    for keys, resp in responses.items():
        if any(k in msg_lower for k in keys):
            return resp + ctx_info

    return ("Je suis **SmartRotor Copilot**. Connectez votre clé Gemini pour "
            "une assistance experte ou choisissez une suggestion." + ctx_info)
