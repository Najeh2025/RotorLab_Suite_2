# modules/ai_copilot.py — SmartRotor Copilot v2.0
# Adapte depuis RotorLab Suite 1.0 — Pr. Najeh Ben Guedria
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
# POINTS D'ENTREE
# =============================================================================
def render_copilot(col_settings, col_graphics):
    """Copilot integre dans le layout 3 panneaux."""
    with col_settings:
        st.markdown(
            '<div class="rl-settings-title">SmartRotor Copilot</div>',
            unsafe_allow_html=True
        )
        _render_context_panel()

    with col_graphics:
        _render_chat_interface()


def render_copilot_fullscreen():
    """Copilot en mode plein ecran."""
    st.markdown("""
    <div style='background:#f0f7ff;padding:15px;border-left:5px solid #1F5C8B;
    border-radius:5px;margin-bottom:20px;'>
    <strong>SmartRotor Copilot — Powered by Gemini AI</strong><br>
    Assistant virtuel specialise en dynamique des rotors, ROSS, API 684 et ISO 1940.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])
    with col1:
        _render_context_panel()
    with col2:
        _render_chat_interface()


# =============================================================================
# PANNEAU CONTEXTE (Settings)
# =============================================================================
def _render_context_panel():
    """Affiche le contexte du rotor actuel."""
    rotor = st.session_state.get("rotor")
    modal = st.session_state.get("res_modal")

    st.caption("Contexte injecte automatiquement")

    context_json = _build_context()

    if rotor:
        st.success("Rotor : {} noeuds | {:.2f} kg | {} DDL".format(
            context_json.get("n_nodes"),
            context_json.get("mass_kg"),
            context_json.get("ndof")
        ))
    else:
        st.warning("Aucun rotor charge.")

    if modal and context_json.get("modal"):
        fn_list = context_json["modal"]["fn_hz"]
        ld_list = context_json["modal"]["log_dec"]
        n_inst  = context_json["modal"]["n_instable"]
        st.markdown("**Modes propres :**")
        for i, (f, ld) in enumerate(zip(fn_list, ld_list)):
            if ld <= 0:
                st.markdown("- Mode {} : {:.2f} Hz | delta={:.4f} INSTABLE".format(
                    i+1, f, ld))
            elif ld < 0.1:
                st.markdown("- Mode {} : {:.2f} Hz | delta={:.4f} marginal".format(
                    i+1, f, ld))
            else:
                st.markdown("- Mode {} : {:.2f} Hz | delta={:.4f} OK".format(
                    i+1, f, ld))
        if n_inst > 0:
            st.error("{} mode(s) INSTABLE(S) detecte(s) !".format(n_inst))

    if context_json.get("api684"):
        score = context_json["api684"]["score"]
        color = "green" if score >= 100 else "orange" if score >= 67 else "red"
        st.markdown(
            "**API 684 :** <span style='color:{};font-weight:bold;'>"
            "{:.0f}%</span>".format(color, score),
            unsafe_allow_html=True
        )

    st.markdown("---")
    status = "Connecte" if GEMINI_OK else "Mode offline"
    st.caption("Gemini : {}".format(status))

    with st.expander("Voir le contexte JSON complet"):
        st.json(context_json)


# =============================================================================
# INTERFACE CHAT
# =============================================================================
def _render_chat_interface():
    """Interface de chat principale."""
    st.markdown("### Questions rapides")

    quick_prompts = [
        "Comment creer un rotor simple avec ROSS ?",
        "Explique-moi le diagramme de Campbell",
        "Pourquoi le Log Dec peut-il etre negatif ?",
        "Comment ameliorer la stabilite de mon rotor ?",
        "Quelle est la difference entre precession avant et arriere ?",
        "Comment calculer le DAF (Dynamic Amplification Factor) ?",
        "Comment modeliser un defaut de fissure avec ROSS ?",
        "Comment verifier la conformite API 684 ?",
        "Comment calculer le balourd tolere ISO 1940 ?",
        "Qu'est-ce que la carte UCS Map ?",
        "Comment fonctionne un palier hydrodynamique ?",
        "Comment modeliser un MultiRotor avec GearElement ?",
    ]

    cols = st.columns(4)
    for i, qp in enumerate(quick_prompts):
        with cols[i % 4]:
            label = qp[:40] + ("..." if len(qp) > 40 else "")
            if st.button(label, key="qp_{}".format(i),
                         use_container_width=True):
                st.session_state["gpt_input"] = qp

    st.markdown("---")

    # Historique du chat
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Saisie
    user_input = st.chat_input("Posez votre question...")
    if not user_input:
        user_input = st.session_state.pop("gpt_input", None)

    if user_input:
        st.session_state["chat_history"].append(
            {"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("SmartRotor Copilot reflechit..."):
                context  = _build_context()
                response = _call_gemini(
                    user_input, context,
                    st.session_state["chat_history"][:-1]
                )
            st.markdown(response)
            st.session_state["chat_history"].append(
                {"role": "assistant", "content": response})

    if st.session_state.get("chat_history"):
        if st.button("Effacer la conversation", key="gpt_clear"):
            st.session_state["chat_history"] = []


# =============================================================================
# CONSTRUCTION DU CONTEXTE SESSION
# =============================================================================
def _build_context():
    """Construit le dictionnaire de contexte depuis la session."""
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
            "score":   api_p.get("score", 0),
            "op_rpm":  api_p.get("op_rpm", 0),
            "n_total": len(df_api),
        }

    return ctx


# =============================================================================
# APPEL API GEMINI
# =============================================================================
def _call_gemini(user_msg, context, history):
    """Appel a l'API Google Gemini avec detection automatique du modele."""
    if not GEMINI_OK:
        return _fallback(user_msg, context)

    try:
        if "GEMINI_API_KEY" not in st.secrets:
            return (
                "La cle GEMINI_API_KEY n'est pas configuree.\n\n"
                + _fallback(user_msg, context)
            )

        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

        # Detection automatique du meilleur modele disponible
        valid_models = [
            m.name for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
        if not valid_models:
            return (
                "Aucun modele Gemini disponible pour cette cle.\n\n"
                + _fallback(user_msg, context)
            )

        # Selection intelligente : flash > pro > premier disponible
        model_name = valid_models[0]
        for m in valid_models:
            if "flash" in m:
                model_name = m
                break
            elif "pro" in m and "vision" not in m:
                model_name = m

        # Prompt systeme
        system_prompt = (
            "Tu es SmartRotor Copilot, un ingenieur expert en dynamique des rotors, "
            "mecanique vibratoire et specialiste absolu de la bibliotheque Python ROSS. "
            "Ton role est d'assister des ingenieurs et des etudiants en Master.\n\n"
            "Tes domaines d'expertise couvrent :\n"
            "- La modelisation avec ROSS (ShaftElement, DiskElement, BearingElement, "
            "SealElement, GearElement, MultiRotor).\n"
            "- L'analyse modale, les diagrammes de Campbell, les reponses au balourd "
            "(Bode, Nyquist), la reponse temporelle, les defauts.\n"
            "- Les orbites temporelles et l'identification des instabilites "
            "(whirl, whip).\n"
            "- Les normes industrielles (API 684, ISO 1940, ISO 7919-3).\n"
            "- La carte UCS, les paliers hydrodynamiques, les systemes MultiRotor.\n\n"
            "Regles de comportement :\n"
            "1. Sois extremement precis, scientifique et pedagogique.\n"
            "2. Utilise le vocabulaire technique approprie (Log Dec, amortissement "
            "croise, frequences naturelles, couplage gyroscopique, etc.).\n"
            "3. Fournis du code ROSS fonctionnel quand c'est pertinent.\n"
            "4. Reponds toujours en francais avec du Markdown structure.\n"
            "5. Personnalise tes reponses avec les donnees du rotor actuel.\n\n"
            "Parametres du rotor actuellement charge dans RotorLab Suite 2.0 :\n"
            + json.dumps(context, ensure_ascii=False, indent=2)
        )

        model = genai.GenerativeModel(model_name)

        # Construction de l'historique Gemini
        gemini_history = [
            {"role": "user",  "parts": [system_prompt]},
            {"role": "model", "parts": [
                "C'est bien note. Je suis SmartRotor Copilot, pret a analyser "
                "vos rotors et a generer du code ROSS !"
            ]}
        ]
        for h in history[-6:]:
            role = "user" if h["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [h["content"]]})

        chat     = model.start_chat(history=gemini_history)
        response = chat.send_message(user_msg)
        return response.text

    except ImportError:
        return (
            "La bibliotheque google-generativeai n'est pas installee.\n\n"
            + _fallback(user_msg, context)
        )
    except Exception as e:
        nom_modele = model_name if 'model_name' in dir() else 'Inconnu'
        return (
            "Erreur Gemini (modele : {}) : {}\n\n".format(nom_modele, str(e))
            + _fallback(user_msg, context)
        )


# =============================================================================
# FALLBACK OFFLINE — Reponses pre-programmees
# =============================================================================
def _fallback(user_msg, context):
    """Reponses intelligentes pre-programmees sans API (mode offline)."""
    msg_lower = user_msg.lower()
    rotor_loaded = context.get("rotor_loaded", False)

    # Contexte rotor
    ctx_info = ""
    if rotor_loaded:
        ctx_info = (
            "\n\n---\n*Votre rotor : {} noeuds, {} kg*".format(
                context.get("n_nodes", "?"),
                context.get("mass_kg", "?")
            )
        )
        if context.get("modal"):
            fn_list = context["modal"]["fn_hz"]
            n_inst  = context["modal"]["n_instable"]
            ctx_info += "\n\nModes propres calcules :\n"
            for i, (f, ld) in enumerate(zip(
                    fn_list, context["modal"]["log_dec"])):
                status = "INSTABLE" if ld <= 0 else (
                    "Conforme API" if ld >= 0.1 else "Marginal")
                ctx_info += "- Mode {} : {:.2f} Hz | delta={:.4f} | {}\n".format(
                    i+1, f, ld, status)
            if n_inst > 0:
                ctx_info += "\n**{} mode(s) INSTABLE(S) !**".format(n_inst)

    # ── Reponses thematiques ──────────────────────────────────────────────

    if any(k in msg_lower for k in ["creer", "premier rotor", "modeliser"]):
        return (
            "## Creer un rotor avec ROSS\n\n"
            "```python\n"
            "import ross as rs\n"
            "import numpy as np\n\n"
            "# 1. Materiau\n"
            "steel = rs.Material(name='Steel', rho=7810, E=211e9, G_s=81.2e9)\n\n"
            "# 2. Arbre (6 elements de 250mm, diam 50mm)\n"
            "shaft = [rs.ShaftElement(L=0.25, idl=0.0, odl=0.05, material=steel)\n"
            "         for _ in range(6)]\n\n"
            "# 3. Disque au noeud central\n"
            "disk = rs.DiskElement.from_geometry(\n"
            "    n=3, material=steel, width=0.07, i_d=0.05, o_d=0.25)\n\n"
            "# 4. Paliers aux extremites\n"
            "b0 = rs.BearingElement(n=0, kxx=1e7, kyy=1e7, cxx=500, cyy=500)\n"
            "b6 = rs.BearingElement(n=6, kxx=1e7, kyy=1e7, cxx=500, cyy=500)\n\n"
            "# 5. Assemblage\n"
            "rotor = rs.Rotor(shaft, [disk], [b0, b6])\n"
            "print('Masse : {:.2f} kg'.format(rotor.m))\n"
            "rotor.plot_rotor()\n"
            "```\n\n"
            "**Conseils :**\n"
            "- Noeuds numerotes de 0 a N (N = nombre d elements)\n"
            "- Les paliers DOIVENT etre sur des noeuds existants\n"
            "- `from_geometry()` calcule masse et inerties automatiquement"
            + ctx_info
        )

    if "campbell" in msg_lower:
        return (
            "## Diagramme de Campbell\n\n"
            "Le Campbell trace les **frequences des modes** en fonction "
            "de la vitesse de rotation Omega.\n\n"
            "**Interpretation :**\n"
            "- **FW (Forward Whirl)** : precession dans le sens de rotation "
            "-> frequence augmente avec Omega\n"
            "- **BW (Backward Whirl)** : precession inverse "
            "-> frequence diminue avec Omega\n"
            "- **Droite 1X** (synchrone) : intersections = vitesses critiques\n"
            "- **Droites 2X, 3X** : excitations super-synchrones\n\n"
            "```python\n"
            "speeds = np.linspace(0, 10000*np.pi/30, 100)\n"
            "camp = rotor.run_campbell(speeds, frequencies=12)\n"
            "camp.plot()\n\n"
            "# Donnees numeriques\n"
            "print('Freq. amorties (rad/s) :', camp.wd[:5, :4])\n"
            "print('Log Dec :', camp.log_dec[:5, :4])\n"
            "```\n\n"
            "**Norme API 684 :** vitesses critiques a +/-15% de la vitesse "
            "operationnelle."
            + ctx_info
        )

    if any(k in msg_lower for k in ["log dec", "instabilit", "stabilit"]):
        return (
            "## Log Decrement et Stabilite\n\n"
            "**delta = 2*pi*xi / sqrt(1 - xi^2)**\n\n"
            "| delta | Interpretation | API 684 |\n"
            "|-------|----------------|---------|\n"
            "| delta > 0.3 | Tres bien amorti | OK |\n"
            "| 0.1 < delta <= 0.3 | Correctement amorti | OK |\n"
            "| 0 < delta <= 0.1 | Peu amorti | Limite |\n"
            "| **delta <= 0** | **INSTABLE** | **NON** |\n\n"
            "**Cause principale :** raideur croisee Kxy des paliers "
            "hydrodynamiques (oil whirl).\n\n"
            "```python\n"
            "modal = rotor.run_modal(speed=3000*np.pi/30)\n"
            "for i, ld in enumerate(modal.log_dec[:6]):\n"
            "    fn = modal.wn[i] / (2*np.pi)\n"
            "    if ld <= 0:\n"
            "        status = 'INSTABLE'\n"
            "    elif ld < 0.1:\n"
            "        status = 'LIMITE'\n"
            "    else:\n"
            "        status = 'OK'\n"
            "    print('Mode {} : {:.2f} Hz | delta={:.4f} | {}'.format(\n"
            "        i+1, fn, ld, status))\n"
            "```"
            + ctx_info
        )

    if any(k in msg_lower for k in ["daf", "balourd", "desequilibr"]):
        return (
            "## Reponse au Balourd et DAF\n\n"
            "```python\n"
            "resp = rotor.run_unbalance_response(\n"
            "    node=[2],\n"
            "    magnitude=[0.001],   # kg.m\n"
            "    phase=[0.0],\n"
            "    frequency_range=np.linspace(0, 5000, 500)\n"
            ")\n"
            "resp.plot_magnitude(probe=[2, 0])\n"
            "resp.plot_phase(probe=[2, 0])\n"
            "resp.plot_polar_bode(probe=[2, 0])\n"
            "```\n\n"
            "**DAF = A_max / A_statique**\n"
            "- Systeme 1-DDL non amorti : DAF = 1/(2*xi)\n"
            "- Reduction du DAF : augmenter Cxx/Cyy des paliers"
            + ctx_info
        )

    if any(k in msg_lower for k in ["api 684", "conformite", "norme", "zone interdite"]):
        return (
            "## Verification API 684\n\n"
            "**Criteres obligatoires :**\n"
            "1. Marge vitesse critique >= 15% : "
            "pas de Vc dans [0.85*Nop, 1.15*Nop]\n"
            "2. Log Dec >= 0.1 pour tous les modes\n"
            "3. Reponse balourd < limites ISO 7919\n\n"
            "```python\n"
            "op_rpm    = 3000\n"
            "zone_low  = op_rpm * 0.85\n"
            "zone_high = op_rpm * 1.15\n\n"
            "modal  = rotor.run_modal(speed=0)\n"
            "fn_hz  = modal.wn / (2*np.pi)\n"
            "vc_rpm = fn_hz * 60\n\n"
            "for i, (vc, ld) in enumerate(zip(vc_rpm[:6], modal.log_dec[:6])):\n"
            "    in_zone = zone_low <= vc <= zone_high\n"
            "    ok = not in_zone and ld >= 0.1\n"
            "    print('Mode {} : Vc={:.0f} RPM | delta={:.3f} | {}'.format(\n"
            "        i+1, vc, ld, 'OK' if ok else 'NON CONFORME'))\n"
            "```"
            + ctx_info
        )

    if any(k in msg_lower for k in ["fissure", "crack"]):
        return (
            "## Simulation de Fissure Transversale (ROSS)\n\n"
            "```python\n"
            "crack_res = rotor.run_crack(\n"
            "    crack_depth=0.3,       # alpha = a/R (0 a 0.9)\n"
            "    crack_node=3,\n"
            "    speed=1500*np.pi/30,\n"
            "    model='gasch'          # 'gasch' ou 'mayes'\n"
            ")\n"
            "crack_res.plot_orbit(node=3)\n"
            "```\n\n"
            "**Signature vibratoire :**\n"
            "- Harmonique 2X caracteristique\n"
            "- Amplification 1X a la vitesse critique\n"
            "- Pic a N_crit/2 (demi-vitesse critique)\n"
            "- Orbites en forme de 8"
            + ctx_info
        )

    if any(k in msg_lower for k in ["ucs", "undamped"]):
        return (
            "## Undamped Critical Speed Map (UCS)\n\n"
            "La carte UCS montre les vitesses critiques non amorties "
            "en fonction de la raideur des paliers.\n\n"
            "**Utilite :** choisir K pour que les Vc soient hors "
            "de la plage operationnelle.\n\n"
            "```python\n"
            "stiffness = np.logspace(5, 9, 30)\n"
            "ucs = rotor.run_ucs(\n"
            "    stiffness_range=stiffness,\n"
            "    num_modes=6\n"
            ")\n"
            "ucs.plot()\n"
            "```"
            + ctx_info
        )

    if any(k in msg_lower for k in ["multirotor", "gear", "engrenage"]):
        return (
            "## MultiRotor et GearElement (ROSS)\n\n"
            "```python\n"
            "# Rotor 1 (moteur)\n"
            "shaft1 = [rs.ShaftElement(L=0.25, idl=0, odl=0.05, material=steel)\n"
            "          for _ in range(4)]\n"
            "# Rotor 2 (recepteur)\n"
            "shaft2 = [rs.ShaftElement(L=0.25, idl=0, odl=0.04, material=steel)\n"
            "          for _ in range(3)]\n\n"
            "# Element engrenage\n"
            "gear = rs.GearElement(\n"
            "    n=2,\n"
            "    pitch_diameter=0.1,\n"
            "    pressure_angle=np.radians(20),\n"
            "    helix_angle=0.0\n"
            ")\n"
            "```\n\n"
            "**Le Campbell couple montre :**\n"
            "- Modes lateraux de chaque rotor\n"
            "- Modes torsionnels\n"
            "- Modes couples lateral-torsionnel\n"
            "- Frequences d engrenement"
            + ctx_info
        )

    if any(k in msg_lower for k in ["palier hydrodynamique", "fluid film",
                                     "hydrodynamic"]):
        return (
            "## Paliers Hydrodynamiques (BearingFluidFilm)\n\n"
            "Les paliers HD ont des coefficients variables avec la vitesse.\n\n"
            "**Coefficients cles :**\n"
            "- Kxx, Kyy : raideurs directes (stabilisantes)\n"
            "- Kxy, Kyx : raideurs croisees (Kxy > 0 = destabilisant)\n"
            "- Cxx, Cyy : amortissements directs\n\n"
            "```python\n"
            "# Palier lisse avec termes croises\n"
            "bearing_hd = rs.BearingElement(\n"
            "    n=0,\n"
            "    kxx=1e7, kyy=5e6,\n"
            "    kxy=2e6, kyx=-2e6,  # Termes croises\n"
            "    cxx=2000, cyy=2000\n"
            ")\n"
            "```\n\n"
            "**Instabilite oil whirl :** se produit quand Kxy "
            "depasse l amortissement disponible. "
            "Verifiez toujours le Log Dec apres modification."
            + ctx_info
        )

    # Reponse generique
    return (
        "Je suis SmartRotor Copilot, specialise en dynamique des rotors.\n\n"
        "Votre question : **{}**\n\n"
        "Je peux vous aider avec :\n"
        "- Création de modeles ROSS\n"
        "- Analyses modales, Campbell, balourd, temporelle\n"
        "- Simulation de defauts (fissure, desalignement, frottement)\n"
        "- Normes API 684, ISO 1940, ISO 7919\n"
        "- Carte UCS, paliers hydrodynamiques\n"
        "- MultiRotor et GearElement\n\n"
        "Utilisez les boutons de questions rapides ou precisez votre demande."
        + ctx_info
    ).format(user_msg)
