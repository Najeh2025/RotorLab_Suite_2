# modules/ai_copilot.py — SmartRotor Copilot v2.1
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
# Corrections v2.1 :
#   - Gestion clé API Gemini via interface
#   - Zone de saisie toujours visible
#   - Bouton Effacer fonctionnel
#   - Persistance de l'historique entre les modes
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
# INITIALISATION DE L'ÉTAT — appelée au démarrage
# =============================================================================
def _init_copilot_state():
    """Initialise les clés de session dédiées au Copilot (une seule fois)."""
    if "copilot_chat_history" not in st.session_state:
        st.session_state["copilot_chat_history"] = []
    if "copilot_api_key" not in st.session_state:
        # Tenter de lire depuis st.secrets si disponible
        try:
            st.session_state["copilot_api_key"] = st.secrets.get(
                "GEMINI_API_KEY", "")
        except Exception:
            st.session_state["copilot_api_key"] = ""
    if "copilot_clear_requested" not in st.session_state:
        st.session_state["copilot_clear_requested"] = False
    if "copilot_pending_response" not in st.session_state:
        st.session_state["copilot_pending_response"] = None


# =============================================================================
# POINTS D'ENTRÉE
# =============================================================================
def render_copilot(col_settings, col_graphics):
    """Copilot intégré dans le layout 3 panneaux (Mode Simulation)."""
    _init_copilot_state()
    with col_settings:
        st.markdown(
            '<div class="rl-settings-title">✨ SmartRotor Copilot</div>',
            unsafe_allow_html=True)
        _render_settings_panel()
    with col_graphics:
        _render_chat_area()


def render_copilot_fullscreen():
    """Copilot en mode plein écran (onglet dédié)."""
    _init_copilot_state()
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("### ⚙️ Configuration")
        _render_settings_panel()
    with col2:
        _render_chat_area()


# =============================================================================
# PANNEAU SETTINGS — Configuration + Contexte
# =============================================================================
def _render_settings_panel():
    """Panneau gauche : clé API, contexte rotor, actions."""

    # ── 1. GESTION CLÉ API ────────────────────────────────────────────────
    st.markdown(
        '<div class="rl-section-header">🔑 Clé API Gemini</div>',
        unsafe_allow_html=True)

    current_key = st.session_state.get("copilot_api_key", "")
    key_preview = ("●" * 8 + current_key[-4:]) if len(current_key) > 4 else ""

    new_key = st.text_input(
        "Clé API Google Gemini :",
        value="",
        type="password",
        placeholder="AIza...",
        help="Obtenez votre clé sur https://aistudio.google.com/apikey",
        key="copilot_key_input"
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✅ Valider", key="copilot_key_save",
                     use_container_width=True):
            if new_key.strip():
                st.session_state["copilot_api_key"] = new_key.strip()
                st.success("Clé sauvegardée !")
            else:
                st.warning("Saisissez une clé valide.")
    with col_btn2:
        if st.button("🗑️ Effacer", key="copilot_key_clear",
                     use_container_width=True):
            st.session_state["copilot_api_key"] = ""
            st.info("Clé supprimée.")

    # Indicateur de statut
    api_key = st.session_state.get("copilot_api_key", "")
    if api_key:
        st.markdown(
            '<div class="rl-card-ok"><small>🟢 Clé configurée : '
            '<code>{}...{}</code></small></div>'.format(
                api_key[:4], api_key[-4:] if len(api_key) > 8 else "****"),
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="rl-card-warn"><small>🟡 Aucune clé — '
            'mode hors-ligne actif</small></div>',
            unsafe_allow_html=True)

    if not GEMINI_OK:
        st.markdown(
            '<div class="rl-card-danger"><small>❌ google-generativeai '
            'non installé</small></div>',
            unsafe_allow_html=True)
        st.code("pip install google-generativeai", language="bash")

    st.markdown("---")

    # ── 2. CONTEXTE ROTOR ─────────────────────────────────────────────────
    st.markdown(
        '<div class="rl-section-header">🔩 Contexte du rotor</div>',
        unsafe_allow_html=True)

    context = _build_context()
    rotor   = st.session_state.get("rotor")

    if rotor:
        st.success("{} nœuds · {:.2f} kg · {} DDL".format(
            context.get("n_nodes"),
            context.get("mass_kg"),
            context.get("ndof")))
    else:
        st.warning("Aucun rotor chargé.")

    modal = st.session_state.get("res_modal")
    if modal and context.get("modal"):
        fn_list = context["modal"]["fn_hz"]
        ld_list = context["modal"]["log_dec"]
        n_inst  = context["modal"]["n_instable"]
        for i, (f, ld) in enumerate(zip(fn_list, ld_list)):
            if ld <= 0:
                st.markdown("- M{} : {:.2f} Hz · δ={:.4f} **⚠️ INST.**".format(
                    i+1, f, ld))
            elif ld < 0.1:
                st.markdown("- M{} : {:.2f} Hz · δ={:.4f} 🟡".format(
                    i+1, f, ld))
            else:
                st.markdown("- M{} : {:.2f} Hz · δ={:.4f} 🟢".format(
                    i+1, f, ld))
        if n_inst > 0:
            st.error("⚠️ {} mode(s) INSTABLE(S) !".format(n_inst))

    if context.get("api684"):
        score = context["api684"]["score"]
        color = "#22863A" if score >= 100 else \
                "#C55A11" if score >= 67 else "#C00000"
        st.markdown(
            "**API 684 :** <span style='color:{};font-weight:bold;'>"
            "{:.0f}%</span>".format(color, score),
            unsafe_allow_html=True)

    st.markdown("---")

    # ── 3. STATISTIQUES CONVERSATION ──────────────────────────────────────
    n_msgs = len(st.session_state.get("copilot_chat_history", []))
    n_user = sum(1 for m in st.session_state.get("copilot_chat_history", [])
                 if m["role"] == "user")
    if n_msgs > 0:
        st.caption("💬 {} messages · {} questions".format(n_msgs, n_user))

    with st.expander("📋 Contexte JSON complet"):
        st.json(context)


# =============================================================================
# ZONE DE CHAT PRINCIPALE
# =============================================================================
def _render_chat_area():
    """Zone de chat : questions rapides + historique + saisie permanente."""

    # ── Traitement de la demande d'effacement (callback-safe) ─────────────
    if st.session_state.get("copilot_clear_requested"):
        st.session_state["copilot_chat_history"] = []
        st.session_state["copilot_clear_requested"] = False
        st.session_state["copilot_pending_response"] = None

    # ── En-tête avec bouton Effacer TOUJOURS VISIBLE ──────────────────────
    col_title, col_clear = st.columns([4, 1])
    with col_title:
        st.markdown(
            '<div class="rl-graphics-title">✨ SmartRotor Copilot'
            ' — Powered by Gemini AI</div>',
            unsafe_allow_html=True)
    with col_clear:
        st.button(
            "🗑️ Effacer",
            key="copilot_clear_btn",
            use_container_width=True,
            on_click=_cb_clear_history,
            help="Effacer tout l'historique de conversation"
        )

    # ── Questions rapides ──────────────────────────────────────────────────
    with st.expander("⚡ Questions rapides", expanded=False):
        quick_prompts = [
            "Comment créer un rotor simple avec ROSS ?",
            "Explique le diagramme de Campbell",
            "Pourquoi le Log Dec peut-il être négatif ?",
            "Comment améliorer la stabilité du rotor ?",
            "Différence entre précession avant et arrière ?",
            "Calculer le DAF (Dynamic Amplification Factor) ?",
            "Modéliser un défaut de fissure avec ROSS ?",
            "Vérifier la conformité API 684 ?",
            "Calculer le balourd toléré ISO 1940 ?",
            "Qu'est-ce que la carte UCS Map ?",
            "Comment fonctionne un palier hydrodynamique ?",
            "Modéliser un MultiRotor avec GearElement ?",
        ]
        cols = st.columns(2)
        for i, qp in enumerate(quick_prompts):
            with cols[i % 2]:
                if st.button(
                        qp[:55] + ("…" if len(qp) > 55 else ""),
                        key="qp_{}".format(i),
                        use_container_width=True):
                    # Injecter la question dans l'historique comme message user
                    st.session_state["copilot_chat_history"].append(
                        {"role": "user", "content": qp})
                    st.session_state["copilot_pending_response"] = qp
                    st.rerun()

    # ── Traitement de la réponse en attente (quick prompts) ───────────────
    if st.session_state.get("copilot_pending_response"):
        pending = st.session_state.pop("copilot_pending_response")
        context  = _build_context()
        history  = st.session_state["copilot_chat_history"][:-1]
        with st.spinner("SmartRotor Copilot réfléchit…"):
            response = _call_gemini(pending, context, history)
        st.session_state["copilot_chat_history"].append(
            {"role": "assistant", "content": response})

    # ── Affichage de l'historique ──────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        history = st.session_state.get("copilot_chat_history", [])
        if not history:
            st.markdown("""
            <div style="text-align:center;padding:40px 20px;color:#9CA3AF;">
              <div style="font-size:2.5em;margin-bottom:12px;">✨</div>
              <div style="font-size:1.1em;font-weight:600;color:#6B7280;">
                SmartRotor Copilot
              </div>
              <div style="font-size:0.9em;margin-top:6px;">
                Posez une question ou choisissez une question rapide ci-dessus.
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    # ── Zone de saisie — TOUJOURS VISIBLE ─────────────────────────────────
    user_input = st.chat_input(
        "Posez votre question sur la dynamique des rotors…",
        key="copilot_chat_input"
    )

    if user_input:
        # Ajout du message user
        st.session_state["copilot_chat_history"].append(
            {"role": "user", "content": user_input})

        # Affichage immédiat du message user
        with st.chat_message("user"):
            st.markdown(user_input)

        # Génération de la réponse
        context  = _build_context()
        history  = st.session_state["copilot_chat_history"][:-1]
        with st.chat_message("assistant"):
            with st.spinner("SmartRotor Copilot réfléchit…"):
                response = _call_gemini(user_input, context, history)
            st.markdown(response)

        # Sauvegarde de la réponse
        st.session_state["copilot_chat_history"].append(
            {"role": "assistant", "content": response})


# =============================================================================
# CALLBACK — Effacer l'historique
# =============================================================================
def _cb_clear_history():
    """Callback on_click : marque la demande d'effacement pour le prochain rendu."""
    st.session_state["copilot_clear_requested"] = True


# =============================================================================
# CONSTRUCTION DU CONTEXTE SESSION
# =============================================================================
def _build_context():
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
        ld = getattr(modal, 'log_dec', np.zeros(len(fn)))
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
# APPEL API GEMINI
# =============================================================================
def _call_gemini(user_msg, context, history):
    """Appel à l'API Google Gemini avec clé stockée en session."""
    if not GEMINI_OK:
        return _fallback(user_msg, context)

    api_key = st.session_state.get("copilot_api_key", "")

    # Fallback sur st.secrets si pas de clé en session
    if not api_key:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass

    if not api_key:
        return (
            "⚠️ **Aucune clé API configurée.**\n\n"
            "Veuillez saisir votre clé API Gemini dans le panneau de "
            "configuration à gauche (champ **Clé API Google Gemini**).\n\n"
            "Obtenez une clé gratuite sur : https://aistudio.google.com/apikey\n\n"
            "---\n"
            "**Réponse hors-ligne :**\n\n"
            + _fallback(user_msg, context)
        )

    try:
        genai.configure(api_key=api_key)

        # Détection automatique du modèle disponible
        valid_models = []
        try:
            valid_models = [
                m.name for m in genai.list_models()
                if 'generateContent' in m.supported_generation_methods
            ]
        except Exception:
            valid_models = ["models/gemini-1.5-flash"]

        if not valid_models:
            valid_models = ["models/gemini-1.5-flash"]

        # Priorité : flash > pro
        model_name = valid_models[0]
        for m in valid_models:
            if "flash" in m:
                model_name = m
                break
            elif "pro" in m and "vision" not in m:
                model_name = m

        system_prompt = (
            "Tu es SmartRotor Copilot, un ingénieur expert en dynamique des "
            "rotors, mécanique vibratoire et spécialiste absolu de la "
            "bibliothèque Python ROSS.\n\n"
            "Tes domaines d'expertise :\n"
            "- Modélisation ROSS (ShaftElement, DiskElement, BearingElement, "
            "GearElement, MultiRotor)\n"
            "- Analyse modale, Campbell, réponse au balourd, temporelle, défauts\n"
            "- Orbites, instabilités (whirl/whip), paliers HD\n"
            "- Normes API 684, ISO 1940, ISO 7919-3\n"
            "- Carte UCS, systèmes MultiRotor\n\n"
            "Règles :\n"
            "1. Sois précis, scientifique et pédagogique\n"
            "2. Fournis du code ROSS fonctionnel quand pertinent\n"
            "3. Réponds TOUJOURS en français avec Markdown structuré\n"
            "4. Personnalise avec les données du rotor actuel\n\n"
            "Paramètres du rotor dans RotorLab Suite 2.0 :\n"
            + json.dumps(context, ensure_ascii=False, indent=2)
        )

        model = genai.GenerativeModel(model_name)

        gemini_history = [
            {"role": "user",  "parts": [system_prompt]},
            {"role": "model", "parts": [
                "C'est bien noté. Je suis SmartRotor Copilot, prêt à analyser "
                "vos rotors et générer du code ROSS !"
            ]}
        ]
        for h in history[-8:]:
            role = "user" if h["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [h["content"]]})

        chat     = model.start_chat(history=gemini_history)
        response = chat.send_message(user_msg)
        return response.text

    except Exception as e:
        err_str = str(e)
        # Clé invalide
        if "API_KEY" in err_str.upper() or "401" in err_str or \
                "403" in err_str or "invalid" in err_str.lower():
            return (
                "❌ **Clé API invalide ou expirée.**\n\n"
                "Vérifiez votre clé dans le panneau de configuration.\n\n"
                "---\n**Réponse hors-ligne :**\n\n"
                + _fallback(user_msg, context)
            )
        return (
            "⚠️ **Erreur Gemini :** `{}`\n\n---\n"
            "**Réponse hors-ligne :**\n\n".format(err_str)
            + _fallback(user_msg, context)
        )


# =============================================================================
# FALLBACK OFFLINE
# =============================================================================
def _fallback(user_msg, context):
    msg_lower    = user_msg.lower()
    rotor_loaded = context.get("rotor_loaded", False)

    ctx_info = ""
    if rotor_loaded:
        ctx_info = "\n\n---\n*Rotor actuel : {} nœuds, {} kg*".format(
            context.get("n_nodes", "?"),
            context.get("mass_kg", "?"))
        if context.get("modal"):
            fn_list = context["modal"]["fn_hz"]
            ctx_info += "\n\nModes propres :\n"
            for i, (f, ld) in enumerate(
                    zip(fn_list, context["modal"]["log_dec"])):
                status = "⚠️ INSTABLE" if ld <= 0 else (
                    "🟢 API OK" if ld >= 0.1 else "🟡 Marginal")
                ctx_info += "- M{} : {:.2f} Hz | δ={:.4f} | {}\n".format(
                    i+1, f, ld, status)

    if any(k in msg_lower for k in ["créer", "premier rotor", "modélis"]):
        return (
            "## Créer un rotor avec ROSS\n\n"
            "```python\nimport ross as rs\nimport numpy as np\n\n"
            "steel = rs.Material(name='Steel', rho=7810, E=211e9, G_s=81.2e9)\n"
            "shaft = [rs.ShaftElement(L=0.25, idl=0.0, odl=0.05, "
            "material=steel) for _ in range(6)]\n"
            "disk  = rs.DiskElement(n=3, m=15.0, Id=0.025, Ip=0.047)\n"
            "b0    = rs.BearingElement(n=0, kxx=1e7, kyy=1e7, cxx=500, cyy=500)\n"
            "b6    = rs.BearingElement(n=6, kxx=1e7, kyy=1e7, cxx=500, cyy=500)\n"
            "rotor = rs.Rotor(shaft, [disk], [b0, b6])\n"
            "print('Masse : {:.2f} kg'.format(rotor.m))\n```"
            + ctx_info)

    if "campbell" in msg_lower:
        return (
            "## Diagramme de Campbell\n\n"
            "Superpose fréquences propres fn(Ω) et droites harmoniques kX.\n\n"
            "- **Intersection** fn avec 1X → vitesse critique\n"
            "- **API 684** : marge ≥ 15% obligatoire\n"
            "- **FW** (Forward) : fn croît avec Ω\n"
            "- **BW** (Backward) : fn décroît avec Ω\n\n"
            "```python\nspeeds = np.linspace(0, 10000*np.pi/30, 100)\n"
            "camp = rotor.run_campbell(speeds, frequencies=12)\n"
            "camp.plot()\n```"
            + ctx_info)

    if any(k in msg_lower for k in ["log dec", "instabilit", "stabilit"]):
        return (
            "## Log Décrément et Stabilité\n\n"
            "| δ | Statut | API 684 |\n"
            "|---|--------|---------|\n"
            "| δ > 0.3 | Très stable | ✅ |\n"
            "| 0.1 < δ ≤ 0.3 | Stable | ✅ |\n"
            "| 0 < δ ≤ 0.1 | Marginal | ⚠️ |\n"
            "| **δ ≤ 0** | **INSTABLE** | **❌** |\n\n"
            "**Cause principale :** raideur croisée Kxy des paliers HD.\n\n"
            "```python\nmodal = rotor.run_modal(speed=3000*np.pi/30)\n"
            "print(modal.log_dec[:6])\n```"
            + ctx_info)

    if any(k in msg_lower for k in ["api 684", "conformit", "norme"]):
        return (
            "## Vérification API 684\n\n"
            "**Critères :**\n"
            "1. Vc hors de [0.85·Nop, 1.15·Nop]\n"
            "2. Log Dec ≥ 0.1 pour tous les modes\n\n"
            "```python\nop_rpm = 3000\n"
            "modal  = rotor.run_modal(speed=0)\n"
            "vc_rpm = modal.wn / (2*np.pi) * 60\n"
            "for i, (vc, ld) in enumerate(zip(vc_rpm[:6], modal.log_dec[:6])):\n"
            "    ok = (vc < op_rpm*0.85 or vc > op_rpm*1.15) and ld >= 0.1\n"
            "    print('M{} : {:.0f} RPM | δ={:.3f} | {}'.format(\n"
            "        i+1, vc, ld, 'OK' if ok else 'NON CONFORME'))\n```"
            + ctx_info)

    if any(k in msg_lower for k in ["iso 1940", "balourd", "déséquilibr"]):
        return (
            "## ISO 1940 — Balourd Résiduel\n\n"
            "**Uper = m·G / (1000·ω)**\n\n"
            "| Grade | Application | Uper typique |\n"
            "|-------|-------------|---------------|\n"
            "| G0.4 | Turbines HP, gyroscopes | Très faible |\n"
            "| G2.5 | Compresseurs, turbines | Standard |\n"
            "| G6.3 | Machines-outils | Industriel |\n\n"
            "```python\nop_rpm = 3000\nomega  = op_rpm * np.pi / 30\n"
            "G      = 2.5  # Grade ISO\n"
            "Uper   = rotor.m * G / (1000 * omega)\n"
            "print('Uper G2.5 = {:.6f} kg.m'.format(Uper))\n```"
            + ctx_info)

    if any(k in msg_lower for k in ["palier hydro", "fluid film", "oil whirl"]):
        return (
            "## Paliers Hydrodynamiques\n\n"
            "Coefficients : **Kxx, Kyy** (stabilisants) · "
            "**Kxy** (déstabilisant si > 0)\n\n"
            "- Oil whirl ≈ **0.46·Ω** (sous-synchrone)\n"
            "- Oil whip si fn_rotor ≈ 0.46·Ω → instabilité explosive\n\n"
            "```python\nbearing = rs.BearingElement(\n"
            "    n=0, kxx=1e7, kyy=5e6,\n"
            "    kxy=2e6, kyx=-2e6,  # couplage déstabilisant\n"
            "    cxx=2000, cyy=2000)\n```\n\n"
            "**Paliers tilting-pad** : Kxy ≈ 0 → plus stable."
            + ctx_info)

    if any(k in msg_lower for k in ["multirotor", "gear", "engrenage"]):
        return (
            "## MultiRotor & GearElement\n\n"
            "**Fréquence d'engrènement :** fe = N1·z1/60\n\n"
            "```python\ngear = rs.GearElement(\n"
            "    n=3, m=14.37, Id=0.068, Ip=0.136,\n"
            "    width=0.07, n_teeth=37,\n"
            "    base_diameter=0.19, pressure_angle=22.5)\n\n"
            "multi = rs.MultiRotor(rotors=[r1, r2], "
            "gear_mesh_stiffness=1e8)\n"
            "camp  = multi.run_campbell(\n"
            "    rs.Q_(np.linspace(0, 5000, 50), 'RPM'),\n"
            "    frequencies=12)\n```"
            + ctx_info)

    # Réponse générique
    return (
        "Je suis **SmartRotor Copilot**, spécialisé en dynamique des rotors.\n\n"
        "Votre question : *{}*\n\n"
        "Je peux vous aider avec :\n"
        "- Création et modélisation ROSS\n"
        "- Analyse modale, Campbell, balourd, temporelle\n"
        "- Défauts (fissure, désalignement, frottement)\n"
        "- Normes API 684, ISO 1940\n"
        "- Carte UCS, paliers HD, MultiRotor\n\n"
        "Configurez votre clé API Gemini pour des réponses personnalisées."
        + ctx_info
    ).format(user_msg)
