import streamlit as st
import json

try:
    import google.generativeai as genai
    GEMINI_OK = True
except ImportError:
    GEMINI_OK = False


def render_copilot(col_settings, col_graphics):
    with col_settings:
        st.markdown(
            '<div class="rl-settings-title">SmartRotor Copilot</div>',
            unsafe_allow_html=True
        )
        st.caption("Assistant IA specialise en dynamique des rotors")
        st.markdown("---")
        st.markdown("**Contexte injecte automatiquement :**")
        ctx = _build_context()
        rotor = st.session_state.get("rotor")
        if rotor:
            st.success("Rotor : {} noeuds, {:.2f} kg".format(
                ctx.get("n_nodes"), ctx.get("mass_kg")))
            if ctx.get("modal"):
                fn = ctx["modal"]["fn_hz"]
                st.info("Modes : " + ", ".join(
                    "{:.1f} Hz".format(f) for f in fn))
        else:
            st.warning("Aucun rotor charge.")
        st.markdown("---")
        st.caption("Gemini : " + ("Connecte" if GEMINI_OK else "Mode offline"))

    with col_graphics:
        _render_chat_interface()


def render_copilot_fullscreen():
    st.subheader("SmartRotor Copilot - Powered by Google Gemini")
    col1, col2 = st.columns([1, 3])
    with col1:
        ctx = _build_context()
        rotor = st.session_state.get("rotor")
        st.markdown("**Contexte session :**")
        if rotor:
            st.success("Rotor charge\n{} noeuds\n{:.2f} kg".format(
                ctx.get("n_nodes"), ctx.get("mass_kg")))
            if ctx.get("modal"):
                st.info("Modes calcules : {}".format(
                    len(ctx["modal"]["fn_hz"])))
            if ctx.get("campbell"):
                st.info("Campbell disponible")
        else:
            st.warning("Aucun rotor charge")
        st.caption("Gemini : " + ("Connecte" if GEMINI_OK else "Mode offline"))
    with col2:
        _render_chat_interface()


def _render_chat_interface():
    st.markdown(
        '<div class="rl-card-info">'
        '<strong>Votre expert virtuel en dynamique des rotors</strong><br>'
        '<small>Je connais le contenu de votre session en cours. '
        'Posez vos questions sur ROSS, vos resultats, '
        'les normes API 684 / ISO 1940, ou demandez de l\'aide '
        'pour interpreter vos graphiques.</small>'
        '</div>',
        unsafe_allow_html=True
    )

    # Questions rapides organisees par theme
    themes = {
        "Modelisation ROSS": [
            "Comment creer un rotor avec ROSS ?",
            "Comment modeliser un arbre conique ?",
            "Comment choisir la raideur des paliers ?",
        ],
        "Analyses": [
            "Que signifie un Log Dec negatif ?",
            "Comment interpreter mon Campbell ?",
            "Quelle est la difference FW et BW ?",
        ],
        "Normes": [
            "Comment verifier la conformite API 684 ?",
            "Comment calculer le balourd ISO 1940 ?",
            "Quelles sont les limites ISO 7919-3 ?",
        ],
        "Defauts": [
            "Quelle est la signature d'une fissure ?",
            "Comment detecter un desalignement ?",
            "Qu'est-ce que le frottement rotor-stator ?",
        ],
    }

    tab_labels = list(themes.keys())
    tabs = st.tabs(tab_labels)
    for tab, (theme, questions) in zip(tabs, themes.items()):
        with tab:
            cols = st.columns(3)
            for i, q in enumerate(questions):
                with cols[i % 3]:
                    label = q[:35] + "..." if len(q) > 35 else q
                    if st.button(label, key="qp_{}_{}".format(theme, i),
                                 use_container_width=True):
                        st.session_state["gpt_input"] = q

    st.markdown("---")

    # Historique
    for msg in st.session_state.get("chat_history", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Posez votre question en francais ou en anglais...")
    if not user_input:
        user_input = st.session_state.pop("gpt_input", None)

    if user_input:
        st.session_state.setdefault("chat_history", [])
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
        if st.button("Effacer la conversation", key="clear_chat"):
            st.session_state["chat_history"] = []


def _build_context():
    rotor  = st.session_state.get("rotor")
    modal  = st.session_state.get("res_modal")
    camp   = st.session_state.get("res_campbell")
    df_api = st.session_state.get("df_api")
    ctx    = {"rotor_loaded": rotor is not None}

    if rotor:
        ctx["n_nodes"]  = len(rotor.nodes)
        ctx["mass_kg"]  = round(float(rotor.m), 2)
        ctx["ndof"]     = rotor.ndof
        ctx["rotor_name"] = st.session_state.get("rotor_name", "Rotor")

    if modal:
        import numpy as np
        fn = modal.wn / (2 * np.pi)
        ld = getattr(modal, 'log_dec', [])
        ctx["modal"] = {
            "fn_hz":      [round(float(v), 2) for v in fn[:6]],
            "log_dec":    [round(float(v), 4) for v in ld[:6]],
            "n_instable": int(sum(1 for v in ld[:6] if v <= 0)),
        }

    if camp is not None:
        ctx["campbell"] = {"calculated": True}
        if st.session_state.get("df_campbell") is not None:
            df_c = st.session_state["df_campbell"]
            ctx["campbell"]["n_critical_speeds"] = len(df_c)

    if df_api is not None and not df_api.empty:
        api_p = st.session_state.get("api_params", {})
        ctx["api684"] = {
            "score":   api_p.get("score", 0),
            "op_rpm":  api_p.get("op_rpm", 0),
            "n_total": len(df_api),
        }

    return ctx


def _call_gemini(user_msg, context, history):
    if not GEMINI_OK:
        return _fallback(user_msg, context)
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            return _fallback(user_msg, context)

        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        valid = [
            m.name for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
        if not valid:
            return _fallback(user_msg, context)

        model_name = next((m for m in valid if "flash" in m), valid[0])

        system_prompt = (
            "Tu es SmartRotor Copilot, un ingenieur expert de niveau "
            "Professeur en dynamique des rotors, vibrations des machines "
            "tournantes et specialiste de la bibliotheque Python ROSS. "
            "Tu travailles avec le Pr. Najeh Ben Guedria de l'ISTLS "
            "Universite de Sousse, Tunisie.\n\n"
            "Tes competences couvrent :\n"
            "- Modelisation ROSS (ShaftElement, DiskElement, BearingElement, "
            "SealElement, GearElement, MultiRotor)\n"
            "- Analyses : statique, modale, Campbell, balourd, H(jw), "
            "temporelle, defauts\n"
            "- Normes : API 684 (vitesses critiques, stabilite), "
            "ISO 1940 (equilibrage), ISO 7919-3 (limites vibratoires)\n"
            "- Physique : couplage gyroscopique, effet gyroscopique, "
            "precession FW/BW, instabilite fluide\n\n"
            "Regles :\n"
            "1. Reponds TOUJOURS en francais\n"
            "2. Sois tres precis et pedagogique\n"
            "3. Fournis du code ROSS fonctionnel quand c'est utile\n"
            "4. Utilise le contexte du rotor actuel pour personnaliser "
            "tes reponses\n"
            "5. Structure tes reponses avec des titres ## et des listes\n\n"
            "Contexte du rotor actuellement charge dans RotorLab Suite 2.0 :\n"
            + json.dumps(context, ensure_ascii=False, indent=2)
        )

        model = genai.GenerativeModel(model_name)
        hist  = [
            {"role": "user",  "parts": [system_prompt]},
            {"role": "model", "parts": [
                "Compris. Je suis SmartRotor Copilot, expert en dynamique "
                "des rotors. Je connais le rotor actuellement charge et "
                "je suis pret a vous aider avec precision."
            ]}
        ]
        for h in history[-8:]:
            role = "user" if h["role"] == "user" else "model"
            hist.append({"role": role, "parts": [h["content"]]})

        chat = model.start_chat(history=hist)
        return chat.send_message(user_msg).text

    except Exception as e:
        return "Erreur Gemini : {}\n\n{}".format(e, _fallback(user_msg, context))


def _fallback(user_msg, context):
    """Reponses offline detaillees sans API."""
    msg = user_msg.lower()

    # Contexte du rotor actuel
    ctx_rotor = ""
    if context.get("rotor_loaded"):
        ctx_rotor = (
            "\n\n---\n**Votre rotor actuel :** {} noeuds, {} kg, {} DDL".format(
                context.get("n_nodes", "?"),
                context.get("mass_kg", "?"),
                context.get("ndof", "?")
            )
        )
        if context.get("modal"):
            fn_list = context["modal"]["fn_hz"]
            n_inst  = context["modal"]["n_instable"]
            ctx_rotor += "\n\n**Modes propres calcules :**\n"
            for i, f in enumerate(fn_list):
                ld = context["modal"]["log_dec"][i]
                status = "INSTABLE" if ld <= 0 else (
                    "Conforme API" if ld >= 0.1 else "Marginal")
                ctx_rotor += "- Mode {} : {:.2f} Hz | Log Dec = {:.4f} | {}\n".format(
                    i+1, f, ld, status)
        if context.get("api684"):
            score  = context["api684"]["score"]
            op_rpm = context["api684"]["op_rpm"]
            ctx_rotor += "\n**API 684 :** Score {:.0f}% a {:.0f} RPM".format(
                score, op_rpm)

    # ── Reponses thematiques ──────────────────────────────────────────────

    if any(k in msg for k in ["creer", "creer un rotor", "modeliser", "premier rotor"]):
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
            "# 3. Disque au noeud 3\n"
            "disk = rs.DiskElement.from_geometry(\n"
            "    n=3, material=steel, width=0.07, i_d=0.05, o_d=0.30)\n\n"
            "# 4. Paliers aux extremites\n"
            "b0 = rs.BearingElement(n=0, kxx=1e7, kyy=1e7, cxx=500, cyy=500)\n"
            "b6 = rs.BearingElement(n=6, kxx=1e7, kyy=1e7, cxx=500, cyy=500)\n\n"
            "# 5. Assemblage\n"
            "rotor = rs.Rotor(shaft, [disk], [b0, b6])\n"
            "print('Masse : {:.2f} kg'.format(rotor.m))\n"
            "print('Noeuds :', rotor.nodes)\n"
            "rotor.plot_rotor()\n"
            "```\n\n"
            "**Points cles :**\n"
            "- Les noeuds sont numerotes de 0 a N (N = nombre d'elements)\n"
            "- Les paliers DOIVENT etre sur des noeuds existants\n"
            "- `from_geometry()` calcule automatiquement masse et inerties"
            + ctx_rotor
        )

    if any(k in msg for k in ["campbell", "vitesse critique", "1x", "diagramme"]):
        return (
            "## Diagramme de Campbell\n\n"
            "Le Campbell trace les **frequences des modes propres** "
            "en fonction de la vitesse de rotation Omega.\n\n"
            "### Interpretation\n"
            "- **Courbes bleues (FW)** : modes de precession avant "
            "(dans le sens de rotation). Frequence augmente avec Omega.\n"
            "- **Courbes orange (BW)** : modes de precession arriere. "
            "Frequence diminue avec Omega.\n"
            "- **Droite rouge 1X** : excitation synchrone. "
            "Les intersections = **vitesses critiques**.\n"
            "- **Zone rouge hatchi** : zone interdite API 684 "
            "(+/-15% de la vitesse operationnelle).\n\n"
            "### Code ROSS\n"
            "```python\n"
            "speeds = np.linspace(0, 10000*np.pi/30, 100)  # 0 a 10000 RPM\n"
            "camp   = rotor.run_campbell(speeds, frequencies=12)\n"
            "camp.plot()\n\n"
            "# Acces aux donnees\n"
            "print('Frequences amorties (rad/s) :', camp.wd[:5, :4])\n"
            "print('Log Dec :', camp.log_dec[:5, :4])\n"
            "print('Precession :', camp.whirl[:5, :4])\n"
            "```\n\n"
            "### Effet gyroscopique\n"
            "L'effet gyroscopique est proporitionnel a la vitesse Omega et "
            "a l'inertie polaire Ip des disques. Il separe les modes FW et BW "
            "et peut provoquer des instabilites si la raideur croisee Kxy "
            "des paliers est elevee."
            + ctx_rotor
        )

    if any(k in msg for k in ["log dec", "stabilit", "instabil"]):
        return (
            "## Log Decrement et Stabilite\n\n"
            "Le Log Decrement **delta** quantifie l'amortissement de chaque mode :\n\n"
            "**delta = 2*pi*xi / sqrt(1 - xi^2)**\n\n"
            "| Valeur de delta | Interpretation | Conformite API 684 |\n"
            "|-----------------|----------------|--------------------|\n"
            "| delta > 0.3 | Tres bien amorti | Oui |\n"
            "| 0.1 < delta <= 0.3 | Correctement amorti | Oui |\n"
            "| 0 < delta <= 0.1 | Peu amorti | Limite |\n"
            "| **delta <= 0** | **INSTABLE** | **Non** |\n\n"
            "### Causes principales d'instabilite\n"
            "1. **Raideur croisee Kxy** des paliers hydrodynamiques "
            "(phenomene *oil whirl* / *oil whip*)\n"
            "2. **Forces aero-elastiques** dans les etages de compression\n"
            "3. **Friction interne** du materiau (amortissement interne > externe)\n\n"
            "### Solutions\n"
            "- Augmenter l'amortissement direct Cxx, Cyy des paliers\n"
            "- Reduire la raideur croisee (palier lobe, palier tilting-pad)\n"
            "- Modifier la vitesse operationnelle\n\n"
            "```python\n"
            "modal = rotor.run_modal(speed=3000*np.pi/30)\n"
            "for i, (fn, ld) in enumerate(\n"
            "        zip(modal.wn/(2*np.pi), modal.log_dec)):\n"
            "    status = 'INSTABLE' if ld <= 0 else (\n"
            "        'OK' if ld >= 0.1 else 'LIMITE')\n"
            "    print('Mode {} : {:.2f} Hz | delta={:.4f} | {}'.format(\n"
            "        i+1, fn, ld, status))\n"
            "```"
            + ctx_rotor
        )

    if any(k in msg for k in ["balourd", "iso 1940", "desequilibr", "equilibrage"]):
        return (
            "## Balourd tolere - Norme ISO 1940\n\n"
            "**Uper = m * G / (1000 * omega)**\n\n"
            "- **m** : masse du rotor (kg)\n"
            "- **G** : grade de qualite (voir tableau)\n"
            "- **omega** : vitesse angulaire (rad/s)\n\n"
            "| Grade | Application typique |\n"
            "|-------|---------------------|\n"
            "| G0.4 | Gyroscopes, turbines de precision |\n"
            "| G1.0 | Turbines a gaz, turbines vapeur |\n"
            "| **G2.5** | **Turbines, compresseurs, ventilateurs** |\n"
            "| G6.3 | Machines-outils, moteurs electriques |\n"
            "| G16 | Vilebrequins, transmissions |\n\n"
            "### Code ROSS\n"
            "```python\n"
            "op_rpm = 3000\n"
            "omega  = op_rpm * np.pi / 30\n"
            "m_rot  = rotor.m  # masse du rotor\n\n"
            "# Balourd tolere grade G2.5\n"
            "Uper = (m_rot * 2.5) / (1000 * omega)\n"
            "print('Balourd tolere G2.5 : {:.6f} kg.m'.format(Uper))\n\n"
            "# Reponse au balourd\n"
            "resp = rotor.run_unbalance_response(\n"
            "    node=[3], magnitude=[Uper], phase=[0.0],\n"
            "    frequency_range=np.linspace(0, 5000, 500))\n"
            "resp.plot_magnitude(probe=[3, 0])\n"
            "```"
            + ctx_rotor
        )

    if any(k in msg for k in ["api 684", "conformite", "zone interdite", "norme"]):
        return (
            "## Verification API 684 - 2eme edition\n\n"
            "La norme API 684 definit les criteres de qualification "
            "rotordynamique pour les turbomachines industrielles.\n\n"
            "### Criteres obligatoires\n"
            "1. **Marge vitesses critiques >= 15%** : "
            "aucune vitesse critique dans [0.85*Nop ; 1.15*Nop]\n"
            "2. **Log Dec >= 0.1** pour tous les modes dans la plage "
            "operationnelle\n"
            "3. **Reponse au balourd** : amplitudes < limites ISO 7919-3\n\n"
            "### Code de verification\n"
            "```python\n"
            "op_rpm  = 3000  # Vitesse operationnelle\n"
            "zone_lo = op_rpm * 0.85  # 2550 RPM\n"
            "zone_hi = op_rpm * 1.15  # 3450 RPM\n\n"
            "modal   = rotor.run_modal(speed=0)\n"
            "fn_hz   = modal.wn / (2*np.pi)\n"
            "vc_rpm  = fn_hz * 60\n\n"
            "for i, (vc, ld) in enumerate(\n"
            "        zip(vc_rpm[:6], modal.log_dec[:6])):\n"
            "    in_zone = zone_lo <= vc <= zone_hi\n"
            "    ok      = not in_zone and ld >= 0.1\n"
            "    print('Mode {} : Vc={:.0f} RPM | delta={:.3f} | {}'.format(\n"
            "        i+1, vc, ld,\n"
            "        'CONFORME' if ok else 'NON CONFORME'))\n"
            "```"
            + ctx_rotor
        )

    if any(k in msg for k in ["fissure", "crack", "defaut"]):
        return (
            "## Simulation de Fissure Transversale (ROSS)\n\n"
            "### Modeles disponibles\n"
            "- **Gasch** : variation de raideur respirante (breathing crack)\n"
            "- **Mayes** : modele lineaire de la variation de raideur\n\n"
            "### Signature vibratoire d'une fissure\n"
            "- Composante **2X** caracteristique "
            "(variation de raideur 2 fois par tour)\n"
            "- Amplification 1X et 2X a la **demi-vitesse critique** (0.5*Vc)\n"
            "- Orbites en forme de **huit** au lieu d'ellipses\n\n"
            "### Code ROSS\n"
            "```python\n"
            "crack_res = rotor.run_crack(\n"
            "    crack_depth=0.3,       # alpha = a/R = 0 a 0.9\n"
            "    crack_node=3,          # noeud de la fissure\n"
            "    speed=1500*np.pi/30,   # vitesse en rad/s\n"
            "    model='gasch'          # 'gasch' ou 'mayes'\n"
            ")\n"
            "crack_res.plot_orbit(node=3)\n"
            "```\n\n"
            "### Profondeur et severite\n"
            "| alpha (a/R) | Effet sur la raideur | Detectabilite |\n"
            "|-------------|---------------------|---------------|\n"
            "| 0.1 | Variation < 5% | Difficile |\n"
            "| 0.3 | Variation ~20% | Moderee |\n"
            "| 0.5 | Variation ~40% | Facile |\n"
            "| > 0.7 | Rupture imminente | Critique |"
            + ctx_rotor
        )

    if any(k in msg for k in ["desalignement", "misalignment", "accouplement"]):
        return (
            "## Desalignement (Misalignment)\n\n"
            "### Types de desalignement\n"
            "- **Parallele** : decalage lateral des axes (mis_distance_x/y)\n"
            "- **Angulaire** : angle entre les axes (mis_angle)\n\n"
            "### Signature vibratoire\n"
            "- Forte composante **2X** (desalignement parallele)\n"
            "- Composantes **1X + 2X + 3X** (desalignement angulaire)\n"
            "- Orbites aplaties ou en forme de banane\n\n"
            "### Code ROSS\n"
            "```python\n"
            "mis_res = rotor.run_misalignment(\n"
            "    n=3,\n"
            "    mis_type='parallel',\n"
            "    mis_distance_x=0.001,  # 1 mm de desalignement\n"
            "    mis_distance_y=0.0,\n"
            "    radial_stiffness=5e7,\n"
            "    bending_stiffness=5e7,\n"
            "    speed=3000*np.pi/30\n"
            ")\n"
            "mis_res.plot_orbit(node=3)\n"
            "```"
            + ctx_rotor
        )

    if any(k in msg for k in ["palier", "bearing", "raideur", "rigidite"]):
        return (
            "## Choix et parametrage des paliers\n\n"
            "### Types de paliers dans ROSS\n"
            "| Type | Classe ROSS | Usage typique |\n"
            "|------|-------------|---------------|\n"
            "| Roulement rigide | BearingElement | Machines standard |\n"
            "| Palier lisse HD | BearingFluidFilm | Turbines, compresseurs |\n"
            "| Joint annulaire | SealElement | Etancheite |\n"
            "| Palier magnetique | BearingElement | Tres haute vitesse |\n\n"
            "### Valeurs typiques de raideur\n"
            "| Machine | Kxx typique (N/m) | Cxx typique (N.s/m) |\n"
            "|---------|-------------------|---------------------|\n"
            "| Moteur electrique | 1e7 - 1e8 | 500 - 2000 |\n"
            "| Compresseur centrifuge | 5e6 - 5e7 | 1000 - 5000 |\n"
            "| Turbine vapeur | 1e7 - 1e8 | 2000 - 10000 |\n"
            "| Machine-outil | 1e8 - 1e9 | 200 - 1000 |\n\n"
            "### Code ROSS\n"
            "```python\n"
            "# Palier avec raideur croisee (palier lisse)\n"
            "bearing = rs.BearingElement(\n"
            "    n=0, kxx=1e7, kyy=5e6,\n"
            "    kxy=2e6, kyx=-2e6,  # Termes croises (instabilisant)\n"
            "    cxx=2000, cyy=2000\n"
            ")\n"
            "```\n\n"
            "**Attention** : Kxy > 0 est destabilisant. "
            "Verifiez toujours le Log Dec apres modification."
            + ctx_rotor
        )

    if any(k in msg for k in ["ucs", "undamped critical", "carte"]):
        return (
            "## Undamped Critical Speed Map (UCS Map)\n\n"
            "La carte UCS montre les **vitesses critiques non amorties** "
            "en fonction de la raideur des paliers.\n\n"
            "### Utilite\n"
            "- Choisir la raideur des paliers pour **eviter les resonances** "
            "a la vitesse operationnelle\n"
            "- Identifier les **plages de raideur acceptables**\n"
            "- Outil de conception en phase preliminaire\n\n"
            "### Lecture\n"
            "- Axe X (log) : raideur des paliers K (N/m)\n"
            "- Axe Y : vitesse critique (RPM)\n"
            "- Ligne horizontale rouge : vitesse operationnelle\n"
            "- **Zone favorable** : courbes loin de la ligne rouge\n\n"
            "### Code ROSS\n"
            "```python\n"
            "stiffness = np.logspace(5, 9, 30)  # 10^5 a 10^9 N/m\n"
            "ucs = rotor.run_ucs(\n"
            "    stiffness_range=stiffness,\n"
            "    num_modes=6\n"
            ")\n"
            "ucs.plot()\n"
            "```"
            + ctx_rotor
        )

    # Reponse generique enrichie
    return (
        "## SmartRotor Copilot\n\n"
        "Votre question : **{}**\n\n"
        "Je peux vous aider sur les themes suivants. "
        "Cliquez sur les boutons rapides ou reformulez :\n\n"
        "| Theme | Mots-cles |\n"
        "|-------|-----------|\n"
        "| Modelisation | creer rotor, arbre, disque, palier |\n"
        "| Campbell | diagramme, vitesse critique, FW, BW |\n"
        "| Stabilite | log dec, instabilite, oil whirl |\n"
        "| Equilibrage | balourd, ISO 1940, grade G |\n"
        "| Normes | API 684, conformite, zone interdite |\n"
        "| Defauts | fissure, desalignement, frottement |\n"
        "| Paliers | raideur, amortissement, UCS map |"
        + ctx_rotor
    )
