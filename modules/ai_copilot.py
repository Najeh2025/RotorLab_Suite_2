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
    with col_graphics:
        _render_chat_interface()


def render_copilot_fullscreen():
    st.subheader("SmartRotor Copilot - Powered by Google Gemini")
    _render_chat_interface()


def _render_chat_interface():
    st.markdown(
        '<div class="rl-card-info">'
        '<strong>Votre expert virtuel en dynamique des rotors</strong><br>'
        '<small>Posez vos questions sur ROSS, les resultats de votre '
        'simulation, les normes API 684 / ISO 1940.</small>'
        '</div>',
        unsafe_allow_html=True
    )

    quick = [
        "Comment interpreter mon diagramme de Campbell ?",
        "Que signifie un Log Dec negatif ?",
        "Comment verifier la conformite API 684 ?",
        "Quelle est la difference entre precession FW et BW ?",
        "Comment calculer le balourd tolere ISO 1940 ?",
        "Comment ameliorer la stabilite de mon rotor ?",
    ]

    st.markdown("**Questions rapides :**")
    cols = st.columns(3)
    for i, q in enumerate(quick):
        with cols[i % 3]:
            label = q[:38] + "..." if len(q) > 38 else q
            if st.button(label, key="qp_{}".format(i),
                         use_container_width=True):
                st.session_state["gpt_input"] = q

    st.markdown("---")

    for msg in st.session_state.get("chat_history", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Posez votre question...")
    if not user_input:
        user_input = st.session_state.pop("gpt_input", None)

    if user_input:
        st.session_state.setdefault("chat_history", [])
        st.session_state["chat_history"].append(
            {"role": "user", "content": user_input}
        )
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
                {"role": "assistant", "content": response}
            )

    if st.session_state.get("chat_history"):
        if st.button("Effacer la conversation", key="clear_chat"):
            st.session_state["chat_history"] = []


def _build_context():
    rotor = st.session_state.get("rotor")
    modal = st.session_state.get("res_modal")
    ctx   = {"rotor_loaded": rotor is not None}
    if rotor:
        ctx["n_nodes"] = len(rotor.nodes)
        ctx["mass_kg"] = round(float(rotor.m), 2)
    if modal:
        import numpy as np
        fn = modal.wn / (2 * np.pi)
        ld = getattr(modal, 'log_dec', [])
        ctx["modal"] = {
            "fn_hz":   [round(float(v), 2) for v in fn[:4]],
            "log_dec": [round(float(v), 4) for v in ld[:4]],
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
            "Tu es SmartRotor Copilot, ingenieur expert en dynamique "
            "des rotors et specialiste Python ROSS. "
            "Reponds toujours en francais avec rigueur academique. "
            "Contexte du rotor actuel : "
            + json.dumps(context, ensure_ascii=False)
        )
        model = genai.GenerativeModel(model_name)
        hist  = [
            {"role": "user",  "parts": [system_prompt]},
            {"role": "model", "parts": ["Compris. Je suis SmartRotor Copilot, pret."]}
        ]
        for h in history[-6:]:
            role = "user" if h["role"] == "user" else "model"
            hist.append({"role": role, "parts": [h["content"]]})
        chat = model.start_chat(history=hist)
        return chat.send_message(user_msg).text
    except Exception as e:
        return "Erreur Gemini : {}\n\n{}".format(e, _fallback(user_msg, context))


def _fallback(user_msg, context):
    msg = user_msg.lower()

    if any(k in msg for k in ["campbell", "vitesse critique", "1x"]):
        return (
            "## Diagramme de Campbell\n\n"
            "Le Campbell trace les **frequences des modes** en fonction de "
            "la vitesse de rotation.\n\n"
            "- **FW** : precession dans le sens de rotation\n"
            "- **BW** : precession inverse\n"
            "- **Intersections 1X** : vitesses critiques\n\n"
            "**Norme API 684** : vitesses critiques a +/-15% de Nop.\n\n"
            "```python\n"
            "speeds = np.linspace(0, 10000*np.pi/30, 100)\n"
            "camp   = rotor.run_campbell(speeds, frequencies=12)\n"
            "camp.plot()\n"
            "```"
        )

    if any(k in msg for k in ["log dec", "stabilit", "instabil"]):
        return (
            "## Log Decrement et Stabilite\n\n"
            "**delta = 2*pi*xi / sqrt(1 - xi^2)**\n\n"
            "| Valeur | Interpretation |\n"
            "|--------|----------------|\n"
            "| delta > 0.3 | Tres stable |\n"
            "| 0.1 < delta <= 0.3 | Conforme API 684 |\n"
            "| 0 < delta <= 0.1 | Marginalement stable |\n"
            "| **delta <= 0** | **INSTABLE** |\n"
        )

    if any(k in msg for k in ["balourd", "iso 1940"]):
        return (
            "## Balourd tolere - ISO 1940\n\n"
            "**Uper = m * G / (1000 * omega)**\n\n"
            "- m : masse du rotor (kg)\n"
            "- G : grade (G0.4 a G16)\n"
            "- omega : vitesse (rad/s)\n\n"
            "Grade G2.5 recommande pour turbines et compresseurs."
        )

    if any(k in msg for k in ["api 684", "conformite", "zone interdite"]):
        return (
            "## Verification API 684\n\n"
            "1. **Marge vitesses critiques >= 15%** de la vitesse operationnelle\n"
            "2. **Log Dec >= 0.1** pour tous les modes\n\n"
            "```python\n"
            "op_rpm  = 3000\n"
            "zone_lo = op_rpm * 0.85\n"
            "zone_hi = op_rpm * 1.15\n"
            "```"
        )

    ctx_str = ""
    if context.get("rotor_loaded"):
        ctx_str = "\n\n*Rotor actuel : {} noeuds, {} kg*".format(
            context.get("n_nodes", "?"),
            context.get("mass_kg", "?")
        )

    return (
        "Je suis SmartRotor Copilot. Votre question : **{}**\n\n"
        "Utilisez les boutons de questions rapides ou precisez "
        "votre demande (Campbell, stabilite, balourd, API 684...).{}"
    ).format(user_msg, ctx_str)
