# modules/ai_copilot.py — SmartRotor Copilot v2.3
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
#
# v2.3 — Anti ghost-call hardening :
#   • copilot_pending_response est vidé AVANT l'appel API (pas après)
#   • Verrou copilot_is_processing empêche tout double appel lors des reruns
#   • Les boutons quick-prompt utilisent on_click (phase callback) et
#     NE déclenchent PLUS de st.rerun() manuel — le cycle naturel de
#     Streamlit suffit, et le verrou bloque un éventuel appel parasite.
#   • La réponse est toujours écrite dans st.session_state AVANT le rerun
#     final, de sorte que Streamlit affiche sans re-questionner l'API.
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
# CSS GLOBAL DU COPILOT  (inchangé)
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
.cop-ctx-wrap {
    background: #FFFFFF;
    border: 1.5px solid #D0D8E4;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 14px;
}
.cop-ctx-header {
    background: linear-gradient(90deg, #0F2D4A, #1F5C8B);
    color: #FFFFFF;
    padding: 8px 14px;
    font-size: 0.76em;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.cop-ctx-body { padding: 10px 12px; }
.cop-ctx-row  { display: flex; justify-content: space-between; align-items: center;
                padding: 4px 0; border-bottom: 1px solid #F0F4FF; font-size: 0.80em; }
.cop-ctx-row:last-child { border-bottom: none; }
.cop-ctx-label { color: #6B7280; }
.cop-ctx-val   { font-weight: 700; color: #1A1A2E; }
.cop-ctx-val.ok   { color: #22863A; }
.cop-ctx-val.err  { color: #C00000; }
.cop-ctx-val.warn { color: #C55A11; }

/* ── Mode infos ──────────────────────────────────────────────────────── */
.cop-mode-pill {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 3px 10px; border-radius: 99px;
    font-size: 0.72em; font-weight: 700;
}
.cop-mode-pill.ok  { background: #E8F5E9; color: #1B5E20; border: 1px solid #A5D6A7; }
.cop-mode-pill.off { background: #FFF3E0; color: #E65100; border: 1px solid #FFCC80; }

/* ── Stats conversation ──────────────────────────────────────────────── */
.cop-stats-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
    background: #F7F9FC;
    border: 1px solid #D0D8E4;
    border-radius: 8px;
    margin-bottom: 12px;
}
.cop-stat-item { text-align: center; }
.cop-stat-num  { font-size: 1.1em; font-weight: 800; color: #1F5C8B; line-height: 1; }
.cop-stat-lbl  { font-size: 0.66em; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.04em; }
.cop-stat-sep  { width: 1px; height: 28px; background: #D0D8E4; }

/* ── Modes propres dans contexte ─────────────────────────────────────── */
.cop-mode-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 3px 0;
    font-size: 0.78em;
    border-bottom: 1px solid #F0F4FF;
}
.cop-mode-row:last-child { border-bottom: none; }
.cop-mode-fn  { font-weight: 700; color: #1A1A2E; }
.cop-mode-ld  { color: #6B7280; }
.cop-mode-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.cop-mode-dot.ok   { background: #22863A; }
.cop-mode-dot.warn { background: #C55A11; }
.cop-mode-dot.err  { background: #C00000; }
</style>
"""

# =============================================================================
# INITIALISATION — clés de session avec valeurs par défaut
# =============================================================================
def _init_copilot_state():
    defaults = {
        "copilot_chat_history":    [],
        "copilot_api_key":         "",
        "copilot_clear_requested": False,
        # ── Anti ghost-call ──────────────────────────────────────────────
        # None  → rien à traiter
        # str   → prompt en attente d'un appel API
        "copilot_pending_response": None,
        # True  → un appel API est déjà en cours, bloquer tout nouveau départ
        "copilot_is_processing":    False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # Lecture de la clé depuis les secrets si disponible
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
    for cls, lbl in [tag_gemini, ("", "ROSS OK"), tag_rotor,
                     ("", "{} messages".format(n_msgs))]:
        tags_html += '<span class="cop-hero-tag {}">{}</span>'.format(cls, lbl)

    st.markdown("""
    <div class="cop-hero">
      <div class="cop-hero-left">
        <div class="cop-hero-orb">✨</div>
        <div>
          <div class="cop-hero-title">SmartRotor Copilot</div>
          <div class="cop-hero-sub">
            Assistant IA spécialisé en dynamique des rotors · Powered by Gemini
          </div>
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

    # ── Configuration clé API ─────────────────────────────────────────────
    st.markdown("""
    <div class="cop-config-wrap">
      <div class="cop-config-header">🔑 Configuration Gemini</div>
      <div class="cop-config-body">
    """, unsafe_allow_html=True)

    api_key = st.session_state.get("copilot_api_key", "")
    new_key = st.text_input(
        "Clé API Google Gemini",
        value="",
        type="password",
        placeholder="AIza...",
        help="https://aistudio.google.com/apikey — gratuit",
        key="copilot_key_input",
        label_visibility="collapsed",
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Valider la clé", key="copilot_key_save",
                     use_container_width=True, type="primary"):
            if new_key.strip():
                st.session_state["copilot_api_key"] = new_key.strip()
                st.success("Clé sauvegardée !")
            else:
                st.warning("Saisissez une clé.")
    with c2:
        # On utilise on_click pour déclencher le nettoyage AVANT le rechargement de la page
        if st.button("Effacer", key="copilot_key_clear", use_container_width=True, on_click=_cb_clear_api_key):
            st.info("Clé supprimée.")

    if api_key and GEMINI_OK:
        st.markdown("""
        <div class="cop-key-status ok">
          <div class="cop-key-dot ok"></div>
          Connecté · {}...{}
        </div>
        """.format(api_key[:4], api_key[-4:]), unsafe_allow_html=True)
    elif not GEMINI_OK:
        st.markdown("""
        <div class="cop-key-status off">
          <div class="cop-key-dot off"></div>
          google-generativeai non installé
        </div>
        """, unsafe_allow_html=True)
        st.code("pip install google-generativeai", language="bash")
    else:
        st.markdown("""
        <div class="cop-key-status off">
          <div class="cop-key-dot off"></div>
          Sans clé — mode hors-ligne actif
        </div>
        """, unsafe_allow_html=True)

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
        <div class="cop-ctx-row">
          <span class="cop-ctx-label">Nœuds / DDL</span>
          <span class="cop-ctx-val ok">{nn} / {ndof}</span>
        </div>
        <div class="cop-ctx-row">
          <span class="cop-ctx-label">Masse totale</span>
          <span class="cop-ctx-val">{m:.2f} kg</span>
        </div>
        """.format(
            nn=context.get("n_nodes", "—"),
            ndof=context.get("ndof", "—"),
            m=context.get("mass_kg", 0),
        ), unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="cop-ctx-row">
          <span class="cop-ctx-label">Rotor</span>
          <span class="cop-ctx-val err">Non chargé</span>
        </div>
        """, unsafe_allow_html=True)

    if context.get("modal"):
        fn_list = context["modal"]["fn_hz"]
        ld_list = context["modal"]["log_dec"]
        st.markdown("</div></div>", unsafe_allow_html=True)

        st.markdown("""
        <div class="cop-ctx-wrap" style="margin-top:10px;">
          <div class="cop-ctx-header"
               style="background:linear-gradient(90deg,#1A5C3A,#22863A);">
            📊 Modes propres
          </div>
          <div class="cop-ctx-body">
        """, unsafe_allow_html=True)

        mode_rows = ""
        for i, (f, ld) in enumerate(zip(fn_list, ld_list)):
            dot_cls = "err" if ld <= 0 else "warn" if ld < 0.1 else "ok"
            mode_rows += """
            <div class="cop-mode-row">
              <span style="color:#6B7280;font-size:0.75em;">M{i}</span>
              <span class="cop-mode-fn">{f:.2f} Hz</span>
              <span class="cop-mode-ld">δ={ld:.4f}</span>
              <div class="cop-mode-dot {cls}"></div>
            </div>""".format(i=i + 1, f=f, ld=ld, cls=dot_cls)
        st.markdown(mode_rows, unsafe_allow_html=True)

        n_inst = context["modal"]["n_instable"]
        if n_inst > 0:
            st.markdown("</div></div>", unsafe_allow_html=True)
            st.error("⚠️ {} mode(s) INSTABLE(S) détecté(s) !".format(n_inst))
        else:
            st.markdown("</div></div>", unsafe_allow_html=True)
    else:
        st.markdown("</div></div>", unsafe_allow_html=True)

    if context.get("api684"):
        score = context["api684"]["score"]
        cls   = "ok" if score >= 80 else "warn" if score >= 50 else "off"
        st.markdown("""
        <div class="cop-key-status {cls}" style="margin-top:8px;">
          <div class="cop-key-dot {cls}"></div>
          API 684 — Score {score:.0f}%
        </div>
        """.format(cls=cls, score=score), unsafe_allow_html=True)

    n_msgs = len(st.session_state.get("copilot_chat_history", []))
    n_user = sum(
        1 for m in st.session_state.get("copilot_chat_history", [])
        if m["role"] == "user"
    )
    if n_msgs > 0:
        st.markdown("""
        <div class="cop-stats-bar" style="margin-top:12px;">
          <div class="cop-stat-item">
            <div class="cop-stat-num">{nm}</div>
            <div class="cop-stat-lbl">messages</div>
          </div>
          <div class="cop-stat-sep"></div>
          <div class="cop-stat-item">
            <div class="cop-stat-num">{nu}</div>
            <div class="cop-stat-lbl">questions</div>
          </div>
          <div class="cop-stat-sep"></div>
          <div class="cop-stat-item">
            <div class="cop-stat-num">{na}</div>
            <div class="cop-stat-lbl">réponses</div>
          </div>
        </div>
        """.format(nm=n_msgs, nu=n_user, na=n_msgs - n_user),
        unsafe_allow_html=True)

    with st.expander("Contexte JSON (debug)", expanded=False):
        st.json(context)


# =============================================================================
# ZONE DE CHAT
# =============================================================================
def _render_chat_area():
    st.markdown(_COPILOT_CSS, unsafe_allow_html=True)
    _render_cop_hero()
    _render_chat_area_inner()


def _render_chat_area_inner():
    """
    Logique principale du chat.

    Ordre d'exécution à chaque cycle Streamlit :
      1. Effacement si demandé
      2. Traitement du prompt en attente  ← UNIQUE point d'appel API
         (protégé par le verrou is_processing)
      3. Affichage de l'historique
      4. Zone de saisie / boutons quick-prompt
         → ils écrivent dans pending_response mais N'appellent PAS l'API
    """

    # ── 1. Effacement si demandé ──────────────────────────────────────────
    if st.session_state.get("copilot_clear_requested"):
        st.session_state["copilot_chat_history"]    = []
        st.session_state["copilot_pending_response"] = None
        st.session_state["copilot_is_processing"]    = False
        st.session_state["copilot_clear_requested"]  = False

    # ── 2. Traitement du prompt en attente ────────────────────────────────
    #
    # RÈGLES ANTI-GHOST-CALL :
    #   a) On récupère le prompt et on vide pending AVANT d'appeler l'API.
    #      Si Streamlit relance le script entre-temps, pending est vide →
    #      aucun second appel.
    #   b) Le verrou is_processing bloque tout appel parasite déclenché par
    #      un rerun survenant pendant l'appel HTTP à Gemini.
    #   c) On écrit la réponse dans session_state puis on rerun UNE SEULE
    #      FOIS pour afficher — Streamlit ne re-questionne pas l'API.
    #
    pending = st.session_state.get("copilot_pending_response")

    if pending and not st.session_state.get("copilot_is_processing", False):
        # Acquérir le verrou et vider le pending AVANT l'appel HTTP
        st.session_state["copilot_is_processing"]    = True
        st.session_state["copilot_pending_response"] = None   # ← vider ici

        context = _build_context()
        history = st.session_state["copilot_chat_history"][:-1]  # sans le msg user déjà ajouté

        with st.spinner("SmartRotor Copilot analyse votre question…"):
            response = _call_gemini(pending, context, history)

        # Stocker la réponse et relâcher le verrou
        st.session_state["copilot_chat_history"].append(
            {"role": "assistant", "content": response}
        )
        st.session_state["copilot_is_processing"] = False

        # Un seul rerun pour afficher la réponse — l'API ne sera plus appelée
        st.rerun()

    # ── 3. Bouton Effacer ─────────────────────────────────────────────────
    col_title, col_clear = st.columns([5, 1])
    with col_title:
        st.markdown(
            '<div style="padding:6px 0 4px;font-size:0.82em;font-weight:700;'
            'color:#6B7280;text-transform:uppercase;letter-spacing:0.06em;">'
            '💬 Conversation</div>',
            unsafe_allow_html=True,
        )
    with col_clear:
        st.button(
            "🗑 Effacer",
            key="copilot_clear_btn",
            use_container_width=True,
            on_click=_cb_clear_history,
            help="Effacer l'historique",
        )

    # ── 4. Questions rapides ──────────────────────────────────────────────
    #
    # IMPORTANT : on utilise on_click pour que la mise à jour du
    # session_state se fasse dans la phase callback (avant le rendu),
    # ce qui évite un st.rerun() explicite.  L'appel API se fera au
    # prochain cycle, dans le bloc n°2 ci-dessus.
    #
    with st.expander("⚡ Questions rapides", expanded=False):
        quick_prompts = [
            "Créer un rotor avec ROSS",
            "Comprendre le diagramme de Campbell",
            "Interpréter le Log Décrément",
            "Analyser la réponse au balourd",
            "Paliers hydrodynamiques HD",
            "Vérifier la conformité API 684",
            "Modéliser un MultiRotor",
            "Simuler un défaut de fissure",
            "Qu'est-ce que la carte UCS ?",
            "Calculer l'ISO 1940",
            "Comprendre l'oil whirl/whip",
            "Modes FW vs BW — différence ?",
        ]
        cols = st.columns(2)
        for i, qp in enumerate(quick_prompts):
            with cols[i % 2]:
                lbl = qp[:42] + ("…" if len(qp) > 42 else "")
                # on_click → pas de rerun manuel, pas d'appel API direct
                st.button(
                    lbl,
                    key="qp_{}_v23".format(i),
                    use_container_width=True,
                    on_click=_cb_quick_prompt,
                    args=(qp,),
                )

    # ── 5. Historique de la conversation ─────────────────────────────────
    history = st.session_state.get("copilot_chat_history", [])

    if not history:
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;padding:60px 30px;text-align:center;gap:12px;">
          <div style="width:64px;height:64px;background:linear-gradient(135deg,#EBF4FB,#E3F2FD);
                      border:2px solid #B5D4F4;border-radius:16px;
                      display:flex;align-items:center;justify-content:center;
                      font-size:1.8em;margin-bottom:4px;">✨</div>
          <div style="font-size:1.0em;font-weight:700;color:#1F5C8B;">
            SmartRotor Copilot est prêt
          </div>
          <div style="font-size:0.82em;color:#9CA3AF;line-height:1.5;max-width:300px;">
            Posez une question en rotordynamique, demandez du code ROSS,
            ou choisissez une question rapide ci-dessus.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # ── 6. Saisie permanente ──────────────────────────────────────────────
    #
    # st.chat_input n'émet un résultat que lorsque l'utilisateur appuie
    # sur Entrée — jamais lors d'un simple rerun de Streamlit.
    # C'est donc un déclencheur intrinsèquement sûr.
    #
    user_input = st.chat_input(
        "Posez votre question en dynamique des rotors…",
        key="copilot_chat_input",
    )
    if user_input:
        _enqueue_prompt(user_input)
        st.rerun()


# =============================================================================
# CALLBACKS — modifient uniquement session_state, n'appellent JAMAIS l'API
# =============================================================================
def _cb_clear_history():
    """Callback bouton Effacer."""
    st.session_state["copilot_clear_requested"] = True


def _cb_quick_prompt(prompt: str):
    """
    Callback des boutons quick-prompt.
    Enfile le prompt SANS appeler l'API ni déclencher de rerun manuel.
    Le prochain cycle Streamlit (déclenché automatiquement après on_click)
    traitera le pending dans _render_chat_area_inner().
    """
    _enqueue_prompt(prompt)


def _enqueue_prompt(prompt: str):
    """
    Enregistre un prompt dans la file d'attente.
    Règle : on n'écrit dans pending_response que si aucun appel n'est
    déjà en cours (verrou is_processing).
    """
    if st.session_state.get("copilot_is_processing", False):
        # Un appel est déjà en cours — ignorer silencieusement
        return
    if st.session_state.get("copilot_pending_response"):
        # Un prompt attend déjà — ignorer silencieusement
        return

    # Ajouter le message utilisateur à l'historique
    st.session_state["copilot_chat_history"].append(
        {"role": "user", "content": prompt}
    )
    # Mettre en file d'attente APRÈS avoir ajouté à l'historique
    st.session_state["copilot_pending_response"] = prompt


# =============================================================================
# CONTEXTE SESSION
# =============================================================================
def _build_context() -> dict:
    rotor  = st.session_state.get("rotor")
    modal  = st.session_state.get("res_modal")
    camp   = st.session_state.get("res_campbell")
    df_api = st.session_state.get("df_api")

    ctx = {"rotor_loaded": rotor is not None}

    if rotor:
        ctx["n_nodes"]    = len(rotor.nodes)
        ctx["mass_kg"]    = round(float(rotor.m), 2)
        ctx["ndof"]       = rotor.ndof
        ctx["rotor_name"] = st.session_state.get("rotor_name", "Rotor")

    if modal:
        fn = modal.wn / (2 * np.pi)
        ld = getattr(modal, "log_dec", np.zeros(len(fn)))
        n  = min(6, len(fn))
        ctx["modal"] = {
            "fn_hz":      [round(float(v), 2) for v in fn[:n]],
            "log_dec":    [round(float(v), 4) for v in ld[:n]],
            "n_instable": int(sum(1 for v in ld[:n] if v <= 0)),
        }

    if camp is not None:
        ctx["campbell"] = {"calculated": True}
        df_c = st.session_state.get("df_campbell")
        if df_c is not None:
            ctx["campbell"]["n_critical_speeds"] = len(df_c)

    if df_api is not None and not df_api.empty:
        api_p = st.session_state.get("api_params", {})
        ctx["api684"] = {
            "score":  api_p.get("score", 0),
            "op_rpm": api_p.get("op_rpm", 0),
        }

    return ctx


# =============================================================================
# APPEL GEMINI — appelé UNE SEULE FOIS par cycle grâce au verrou
# =============================================================================
def _call_gemini(user_msg: str, context: dict, history: list) -> str:
    """
    Effectue un appel HTTP à l'API Gemini.
    Cette fonction ne doit être appelée QUE depuis le bloc protégé par
    copilot_is_processing dans _render_chat_area_inner().
    """
    if not GEMINI_OK:
        return _fallback(user_msg, context)

    api_key = st.session_state.get("copilot_api_key", "")
    if not api_key:
        return (
            "⚠️ **Aucune clé API configurée.**\n\n"
            "Saisissez votre clé Gemini dans le panneau de configuration.\n"
            "Clé gratuite : https://aistudio.google.com/apikey\n\n"
            "---\n**Réponse hors-ligne :**\n\n"
            + _fallback(user_msg, context)
        )

    try:
        genai.configure(api_key=api_key)

        # Sélection du modèle
        try:
            models = [
                m.name for m in genai.list_models()
                if "generateContent" in m.supported_generation_methods
            ]
        except Exception:
            models = ["models/gemini-1.5-flash"]

        if not models:
            models = ["models/gemini-1.5-flash"]

        model_name = models[0]
        for m in models:
            if "flash" in m:
                model_name = m
                break
            elif "pro" in m and "vision" not in m:
                model_name = m

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
            {"role": "model", "parts": [
                "Compris ! Je suis SmartRotor Copilot, prêt à analyser "
                "vos rotors et générer du code ROSS."
            ]},
        ]
        for h in history[-8:]:
            role = "user" if h["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [h["content"]]})

        chat     = model.start_chat(history=gemini_history)
        response = chat.send_message(user_msg)
        return response.text

    except Exception as e:
        err_str = str(e)
        if any(k in err_str.upper() for k in ["API_KEY", "401", "403", "INVALID"]):
            return (
                "❌ **Clé API invalide ou expirée.**\n\n"
                "---\n**Réponse hors-ligne :**\n\n"
                + _fallback(user_msg, context)
            )
        if "429" in err_str or "quota" in err_str.lower():
            return (
                "⏳ **Quota Gemini dépassé.**\n\n"
                "La limite de requêtes gratuites a été atteinte. "
                "Patientez quelques secondes puis réessayez, ou "
                "passez sur un plan payant sur https://ai.dev/rate-limit\n\n"
                "---\n**Réponse hors-ligne :**\n\n"
                + _fallback(user_msg, context)
            )
        return (
            "⚠️ **Erreur Gemini :** `{}`\n\n---\n**Réponse hors-ligne :**\n\n".format(err_str)
            + _fallback(user_msg, context)
        )


# =============================================================================
# FALLBACK HORS-LIGNE
# =============================================================================
def _fallback(user_msg: str, context: dict) -> str:
    msg_lower    = user_msg.lower()
    rotor_loaded = context.get("rotor_loaded", False)

    ctx_info = ""
    if rotor_loaded:
        ctx_info = "\n\n---\n*Rotor : {} nœuds, {} kg*".format(
            context.get("n_nodes", "?"), context.get("mass_kg", "?"))
        if context.get("modal"):
            ctx_info += "\n\nModes propres :\n"
            for i, (f, ld) in enumerate(
                    zip(context["modal"]["fn_hz"], context["modal"]["log_dec"])):
                s = "⚠️ INSTABLE" if ld <= 0 else ("✅ OK" if ld >= 0.1 else "🟡 Marginal")
                ctx_info += "- M{} : {:.2f} Hz | δ={:.4f} | {}\n".format(i + 1, f, ld, s)

    responses = {
        ("créer", "rotor", "modélis"): (
            "## Créer un rotor avec ROSS\n\n"
            "```python\nimport ross as rs\nimport numpy as np\n\n"
            "steel = rs.Material(name='Steel', rho=7810, E=211e9, G_s=81.2e9)\n"
            "shaft = [rs.ShaftElement(L=0.25, idl=0.0, odl=0.05, material=steel)\n"
            "         for _ in range(6)]\n"
            "disk  = rs.DiskElement(n=3, m=15.0, Id=0.025, Ip=0.047)\n"
            "b0    = rs.BearingElement(n=0, kxx=1e7, kyy=1e7, cxx=500, cyy=500)\n"
            "b6    = rs.BearingElement(n=6, kxx=1e7, kyy=1e7, cxx=500, cyy=500)\n"
            "rotor = rs.Rotor(shaft, [disk], [b0, b6])\n"
            "print('Masse : {:.2f} kg'.format(rotor.m))\n```"
        ),
        ("campbell",): (
            "## Diagramme de Campbell\n\n"
            "Superpose fréquences propres fn(Ω) et droites harmoniques kX.\n"
            "- Intersection fn ↔ 1X → **vitesse critique**\n"
            "- **API 684** : marge ≥ 15 % obligatoire\n\n"
            "```python\nspeeds = np.linspace(0, 10000*np.pi/30, 100)\n"
            "camp = rotor.run_campbell(speeds, frequencies=12)\ncamp.plot()\n```"
        ),
        ("log dec", "instabilit", "stabilit"): (
            "## Log Décrément et stabilité\n\n"
            "| δ | Statut | API 684 |\n|---|--------|---------|\n"
            "| > 0.3 | Très stable | ✅ |\n"
            "| 0.1–0.3 | Stable | ✅ |\n"
            "| 0–0.1 | Marginal | ⚠️ |\n"
            "| **≤ 0** | **INSTABLE** | **❌** |\n"
        ),
        ("api 684", "conformit", "norme"): (
            "## Vérification API 684\n\n"
            "1. Vc hors de [0.85·Nop, 1.15·Nop]\n"
            "2. Log Dec ≥ 0.1 pour tous les modes\n"
        ),
        ("iso 1940", "balourd"): (
            "## ISO 1940 — Balourd résiduel\n\n"
            "**Uper = m·G / (1000·ω)**\n\n"
            "| Grade | Application |\n|-------|-------------|\n"
            "| G0.4 | Turbines HP, gyroscopes |\n"
            "| G2.5 | Compresseurs, turbines standard |\n"
            "| G6.3 | Machines-outils |\n"
        ),
        ("palier hydro", "fluid film", "oil whirl", "oil whip"): (
            "## Paliers hydrodynamiques\n\n"
            "- **Kxy > 0** → déstabilisant (forces fluides)\n"
            "- Oil whirl ≈ **0.46·Ω** (sous-synchrone)\n"
            "- Oil whip si fn_rotor ≈ 0.46·Ω → instabilité explosive\n"
        ),
        ("multirotor", "gear", "engrenage"): (
            "## MultiRotor & GearElement\n\n"
            "**fe = N1·z1/60** · Rapport i = z1/z2\n\n"
            "```python\ngear = rs.GearElement(\n    n=3, m=14.37, Id=0.068, Ip=0.136,\n"
            "    width=0.07, n_teeth=37, base_diameter=0.19, pressure_angle=22.5)\n"
            "multi = rs.MultiRotor(rotors=[r1, r2], gear_mesh_stiffness=1e8)\n```"
        ),
    }

    for keys, resp in responses.items():
        if any(k in msg_lower for k in keys):
            return resp + ctx_info

    return (
        "Je suis **SmartRotor Copilot**, spécialisé en dynamique des rotors.\n\n"
        "Je peux vous aider avec : modélisation ROSS, analyse modale, Campbell, "
        "balourd, défauts, normes API 684 / ISO 1940, paliers HD, MultiRotor.\n\n"
        "Configurez votre clé API Gemini pour des réponses complètes et personnalisées."
        + ctx_info
    )


def _cb_clear_api_key():
    """Callback pour vider la clé API et réinitialiser le widget visuel."""
    st.session_state["copilot_api_key"] = ""
    st.session_state["copilot_key_input"] = ""
    
