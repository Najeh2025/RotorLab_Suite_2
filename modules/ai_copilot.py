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
        st.markdown(f'<div class="cop-key-status {cls}" style="margin-top:8px;"><div class="cop-key-dot {cls}"></div>API 684 — Score {score:.0f}%</div>', unsafe_allow_html=True)

# =============================================================================
# ZONE DE CHAT (INTERFACE MODERN LLM)
# =============================================================================
def _render_chat_area():
    st.markdown(_COPILOT_CSS, unsafe_allow_html=True)
    _render_cop_hero()
    _render_chat_area_inner()

def _render_chat_area_inner():
    # ── 1. Effacement si demandé ──────────────────────────────────────────
    if st.session_state.get("copilot_clear_requested"):
        st.session_state["copilot_chat_history"]     = []
        st.session_state["copilot_clear_requested"]  = False
        st.session_state["copilot_is_processing"]    = False # Sécurité

    history = st.session_state.get("copilot_chat_history", [])

    # ── 2. En-tête discret (Bouton Nouveau Chat) ──────────────────────────
    if history:
        col_space, col_clear = st.columns([5, 1])
        with col_clear:
            st.button("✨ Nouveau Chat", key="copilot_clear_btn", use_container_width=True, on_click=_cb_clear_history)

    # ── 3. Style CSS avancé ───────────────────────────────────────────────
    st.markdown("""
    <style>
    .stChatMessage { padding: 1.2rem 1.5rem !important; border-radius: 12px; margin-bottom: 12px; }
    .stChatMessageContent { font-size: 1.05em; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

    # ── 4. DESSIN DE L'HISTORIQUE ET DE L'ACCUEIL ─────────────────────────
    if not history:
        # ÉCRAN D'ACCUEIL (inchangé)
        st.markdown("""
        <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; padding-top: 10vh; padding-bottom: 6vh; text-align: center;">
            <div style="font-size: 3.8em; font-weight: 600; line-height: 1.1; letter-spacing: -1.5px;">
                <span style="background: -webkit-linear-gradient(135deg, #1F5C8B, #7B1FA2); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Bonjour.</span>
            </div>
            <div style="font-size: 2.2em; font-weight: 500; color: #8A9BB0; line-height: 1.2; letter-spacing: -0.5px; margin-top: 8px;">
                Comment puis-je optimiser votre rotor aujourd'hui ?
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='text-align: center; color: #6B7280; font-size: 0.85em; margin-bottom: 15px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;'>Suggestions pour démarrer</div>", unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        prompts_data = [
            (c1, "🏗️ Modélisation", "Créer un rotor avec ROSS en Python"),
            (c2, "🩺 Diagnostic M7", "Diagnostiquer une forte composante vibratoire à 2X la vitesse de rotation"),
            (c3, "⚖️ Audit API 684", "Rédiger un audit de conformité API 684 basé sur les données actuelles"),
            (c4, "💧 Stabilisation", "Comment stabiliser ce rotor (Log Decrétement négatif) ?")
        ]
        for col, label, prompt in prompts_data:
            with col:
                # Les quick prompts ne passent plus par un callback compliqué
                # Ils injectent directement la question dans le chat_input virtuel via st.button
                if st.button(label, help=prompt, key=f"qp_hero_{label}", use_container_width=True):
                     # Simuler l'envoi d'une question
                     st.session_state["copilot_chat_history"].append({"role": "user", "content": prompt})
                     # Forcer le rechargement immédiat
                     st.rerun()
    else:
        # AFFICHAGE DE LA CONVERSATION
        for msg in history:
            avatar = "🧑‍💻" if msg["role"] == "user" else "✨"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    # ── 5. SAISIE UTILISATEUR & TRAITEMENT IMMÉDIAT ───────────────────────
    
    # 1. On affiche la zone de saisie
    user_input = st.chat_input("Posez votre question en dynamique des rotors…", key="copilot_chat_input")
    
    # 2. Si l'utilisateur vient de taper une question (ou cliqué sur Entrée)
    if user_input:
        # On affiche IMMÉDIATEMENT la question de l'utilisateur à l'écran
        st.session_state["copilot_chat_history"].append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input)
            
        # On affiche IMMÉDIATEMENT la roue de chargement de l'IA
        with st.chat_message("assistant", avatar="✨"):
            with st.spinner("SmartRotor Copilot analyse votre question…"):
                context = _build_context()
                api_history = st.session_state["copilot_chat_history"][:-1]
                response = _call_gemini(user_input, context, api_history)
                st.markdown(response) # On affiche la réponse une fois prête
                
        # On sauvegarde la réponse de l'IA dans l'historique
        st.session_state["copilot_chat_history"].append({"role": "assistant", "content": response})
        st.rerun()  # ← CETTE LIGNE MANQUAIT

# =============================================================================
# CALLBACKS
# =============================================================================
def _cb_clear_history():
    st.session_state["copilot_clear_requested"] = True

def _cb_save_config():
    st.session_state["copilot_api_key"] = st.session_state.get("copilot_key_input", "").strip()
    st.session_state["copilot_model_choice"] = st.session_state.get("copilot_model_select", "")

def _cb_clear_api_key():
    st.session_state["copilot_api_key"] = ""
    st.session_state["copilot_key_input"] = ""

def _cb_quick_prompt(prompt: str):
    _enqueue_prompt(prompt)

def _enqueue_prompt(prompt: str):
    if st.session_state.get("copilot_is_processing", False) or st.session_state.get("copilot_pending_response"):
        return
    st.session_state["copilot_chat_history"].append({"role": "user", "content": prompt})
    st.session_state["copilot_pending_response"] = prompt


# =============================================================================
# CONTEXTE SESSION
# =============================================================================
def _build_context() -> dict:
    rotor  = st.session_state.get("rotor")
    modal  = st.session_state.get("res_modal")
    df_api = st.session_state.get("df_api")

    ctx = {"rotor_loaded": rotor is not None}
    if rotor:
        ctx["n_nodes"]    = len(rotor.nodes)
        ctx["mass_kg"]    = round(float(rotor.m), 2)
        ctx["ndof"]       = rotor.ndof

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
        ctx["api684"] = {"score": api_p.get("score", 0), "op_rpm": api_p.get("op_rpm", 0)}

    return ctx


# =============================================================================
# APPEL GEMINI
# =============================================================================
def _call_gemini(user_msg: str, context: dict, history: list) -> str:
    if not GEMINI_OK:
        return _fallback(user_msg, context)

    api_key = st.session_state.get("copilot_api_key", "")
    if not api_key:
        return ("⚠️ **Aucune clé API configurée.**\n\nSaisissez votre clé Gemini dans le panneau de configuration.\n\n---\n**Réponse hors-ligne :**\n\n" + _fallback(user_msg, context))

    try:
        genai.configure(api_key=api_key)
        model_name = st.session_state.get("copilot_model_choice", "gemini-1.5-flash")

        system_prompt = (
            "Tu es SmartRotor Copilot, un ingénieur expert en dynamique des "
            "rotors, mécanique vibratoire et spécialiste absolu de la "
            "bibliothèque Python ROSS.\n\n"
            
            "DOMAINES D'EXPERTISE :\n"
            "- Modélisation ROSS (ShaftElement, DiskElement, BearingElement, GearElement, MultiRotor)\n"
            "- Analyses : modale, diagramme de Campbell, réponse au balourd, intégration temporelle, détection de défauts\n"
            "- Phénomènes avancés : orbites, instabilités (whirl/whip), paliers hydrodynamiques\n"
            "- Normes & références : API 684, ISO 1940, ISO 7919-3\n"
            "- Outils & concepts : Carte UCS, systèmes MultiRotor\n\n"
            
            "RÔLES ACTIFS (DIAGNOSTIC & OPTIMISATION) :\n"
            "- DIAGNOSTIC VIBRATOIRE : Si l'utilisateur décrit un symptôme (ex: forte vibration à 1X, 2X, ou composante sous-synchrone), "
            "tu DOIS agir comme un analyste. Énumère les causes mécaniques les plus probables (balourd, désalignement, fissure, oil whirl, frottement) "
            "et suggère quel module de RotorLab Suite utiliser pour vérifier cette hypothèse.\n"
            "- OPTIMISATION DE STABILITÉ : Si le contexte fourni ou l'utilisateur indique des modes instables (Log Décrément négatif ou < 0.1), "
            "tu DOIS proposer des solutions d'ingénierie concrètes pour stabiliser le rotor (ex: modifier l'amortissement direct Cxx/Cyy, "
            "réduire les raideurs croisées Kxy, changer le type de palier pour des Tilting Pad, ou modifier la géométrie/masse).\n"
            "- AUDIT NORMATIF : Si l'utilisateur demande une vérification API 684, utilise les données de marge de séparation et de Log Décrément "
            "du contexte pour rédiger un mini-rapport de conformité.\n\n"
            
            "RÈGLES DE RÉPONSE :\n"
            "1. Sois précis, scientifique et pédagogique. Structure tes réponses en Markdown (titres, listes, tableaux si pertinent).\n"
            "2. Fournis systématiquement du code ROSS fonctionnel, commenté et exécutable lorsque cela éclaire la réponse. Utilise les balises ```python.\n"
            "3. Personnalise chaque réponse en t'appuyant EXPLICITEMENT sur les paramètres du rotor fournis dans le contexte (masse, nombre de nœuds, fréquences propres, Log Dec).\n"
            "4. POLITIQUE LINGUISTIQUE : Réponds par défaut en français. Si l'utilisateur s'exprime dans une autre langue, "
            "adapte-toi immédiatement. Conserve la rigueur technique et la terminologie internationale (whirl/whip, Campbell, UCS, mode shape) quelle que soit la langue.\n\n"
            
            "CONTEXTE ACTUEL DU ROTOR :\n"
            + json.dumps(context, ensure_ascii=False, indent=2)
        )

        model = genai.GenerativeModel(model_name)
        gemini_history = [
            {"role": "user",  "parts": [system_prompt]},
            {"role": "model", "parts": ["Compris ! Je suis SmartRotor Copilot, prêt à analyser vos rotors et générer du code ROSS."]},
        ]
        for h in history[-8:]:
            role = "user" if h["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [h["content"]]})

        chat     = model.start_chat(history=gemini_history)
        response = chat.send_message(user_msg)
        return response.text

    except Exception as e:
        err_str = str(e)
        if "404" in err_str and "models/" in err_str:
            return (f"⚠️ **Modèle IA non trouvé.** Le modèle `{model_name}` n'est pas disponible pour votre clé API. Sélectionnez 'gemini-1.5-flash' dans les paramètres.\n\n---\n**Réponse hors-ligne :**\n\n" + _fallback(user_msg, context))
        if any(k in err_str.upper() for k in ["API_KEY", "401", "403", "INVALID"]):
            return ("❌ **Clé API invalide ou expirée.**\n\n---\n**Réponse hors-ligne :**\n\n" + _fallback(user_msg, context))
        if "429" in err_str or "quota" in err_str.lower():
            return ("⏳ **Quota Gemini dépassé.** Patientez quelques secondes ou changez de modèle IA dans la configuration.\n\n---\n**Réponse hors-ligne :**\n\n" + _fallback(user_msg, context))
        return (f"⚠️ **Erreur Gemini :** `{err_str}`\n\n---\n**Réponse hors-ligne :**\n\n" + _fallback(user_msg, context))


# =============================================================================
# FALLBACK HORS-LIGNE (RÈGLES MÉTIERS EXPERTES)
# =============================================================================
def _fallback(user_msg: str, context: dict) -> str:
    msg_lower    = user_msg.lower()
    rotor_loaded = context.get("rotor_loaded", False)

    ctx_info = ""
    if rotor_loaded:
        ctx_info = "\n\n---\n*Rotor : {} nœuds, {} kg*".format(context.get("n_nodes", "?"), context.get("mass_kg", "?"))

    responses = {
        ("2x", "vibration", "diagnosti", "symptôme"): (
            "## 🩺 Diagnostic Vibratoire (Expertise M7)\n\n"
            "Une forte composante à **2X (deux fois la vitesse de rotation)** indique une asymétrie dans le rotor. Les causes principales sont :\n"
            "1. **Désalignement des paliers ou de l'accouplement** (Crée de fortes charges radiales).\n"
            "2. **Fissure transverse (Crack)** (La raideur de l'arbre varie 2 fois par tour sous l'effet de la gravité).\n"
            "3. **Asymétrie géométrique** (ex: rotor à 2 pôles d'un générateur électrique).\n\n"
            "*Action :* Ouvrez le **Module M7 (Défauts)** pour simuler une respiration de fissure et observer l'orbite interne."
        ),
        ("stabilis", "log dec < 0", "instable"): (
            "## 🛡️ Optimisation de la Stabilité (Expertise M3/M5)\n\n"
            "Votre rotor présente un Log Décrément négatif (Instabilité). Voici comment corriger cela :\n"
            "- **Réduire les forces déstabilisatrices :** Diminuez la raideur croisée ($K_{xy}$) des paliers hydrodynamiques.\n"
            "- **Augmenter l'amortissement :** Augmentez l'amortissement direct ($C_{xx}$, $C_{yy}$) aux emplacements modaux (ventres de vibration).\n"
            "- **Changer la technologie de palier :** Les paliers à patins oscillants (Tilting Pad Bearings) n'ont pas de raideur croisée et éliminent l'Oil Whirl.\n"
            "- **Modification structurelle :** Réduisez la masse en porte-à-faux ou augmentez le diamètre de l'arbre pour repousser la première fréquence propre."
        ),
        ("api 684", "audit", "conformit"): (
            "## 📋 Audit Normatif API 684\n\n"
            f"**Score actuel estimé : {context.get('api684', {}).get('score', 0)} %**\n\n"
            "**Critères de validation :**\n"
            "1. **Marge de séparation (Separation Margin) :** Les vitesses critiques (Vc) doivent être éloignées de la vitesse d'opération (Nop) d'au moins 16% à 26%.\n"
            "2. **Stabilité :** Un Log Décrément minimal de $\\delta_a = 0.1$ est exigé pour tous les modes dans la plage de fonctionnement.\n\n"
            "*Action :* Vérifiez le diagramme de Campbell (Module M3) pour visualiser les marges."
        ),
        ("code", "script", "python", "ross"): (
            "## 💻 Génération de Code ROSS\n\n"
            "```python\nimport ross as rs\nimport numpy as np\n\n"
            "# 1. Matériau et Arbre\n"
            "steel = rs.Material(name='Steel', rho=7810, E=211e9, G_s=81.2e9)\n"
            "shaft = [rs.ShaftElement(L=0.25, idl=0.0, odl=0.05, material=steel) for _ in range(6)]\n\n"
            "# 2. Disques et Paliers\n"
            "disk  = rs.DiskElement(n=3, m=15.0, Id=0.025, Ip=0.047)\n"
            "brg0  = rs.BearingElement(n=0, kxx=1e7, kyy=1e7, cxx=500, cyy=500)\n"
            "brg6  = rs.BearingElement(n=6, kxx=1e7, kyy=1e7, cxx=500, cyy=500)\n\n"
            "# 3. Assemblage et Analyse\n"
            "rotor = rs.Rotor(shaft, [disk], [brg0, brg6])\n"
            "campbell = rotor.run_campbell(speed_range=np.linspace(0, 1000, 50))\n"
            "campbell.plot()\n```"
        ),
    }

    for keys, resp in responses.items():
        if any(k in msg_lower for k in keys):
            return resp + ctx_info

    return ("Je suis **SmartRotor Copilot**. Connectez votre clé Gemini pour une assistance experte ou choisissez une question rapide." + ctx_info)
