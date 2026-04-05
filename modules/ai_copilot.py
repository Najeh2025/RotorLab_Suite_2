# modules/ai_copilot.py — SmartRotor Copilot (sera complété en Phase 6)
import streamlit as st
import json

try:
    import google.generativeai as genai
    GEMINI_OK = True
except ImportError:
    GEMINI_OK = False


def render_copilot(col_settings, col_graphics):
    """SmartRotor Copilot intégré dans le layout 3 panneaux."""
    with col_settings:
        st.markdown('<div class="rl-settings-title">✨ SmartRotor Copilot</div>',
                    unsafe_allow_html=True)
        st.caption("Assistant IA spécialisé en dynamique des rotors")

    with col_graphics:
        _render_chat_interface()


def render_copilot_fullscreen():
    """SmartRotor Copilot en plein écran (mode Copilot)."""
    st.subheader("✨ SmartRotor Copilot — Powered by Google Gemini")
    _render_chat_interface()


def _render_chat_interface():
    """Interface de chat commune."""
    st.markdown("""
    <div class="rl-card-info">
      <strong>💡 Votre expert virtuel en dynamique des rotors</strong><br>
      <small>Posez vos questions sur ROSS, les résultats de votre simulation,
      les normes API 684 / ISO 1940, ou demandez de l'aide pour interpréter
      vos graphiques.</small>
    </div>
    """, unsafe_allow_html=True)

    # Quick prompts
    st.markdown("**Questions rapides :**")
    quick = [
        "Comment interpréter mon diagramme de Campbell ?",
        "Que signifie un Log Dec négatif ?",
        "Comment vérifier la conformité API 684 ?",
        "Quelle est la différence entre précession FW et BW ?",
        "Comment calculer le balourd toléré (ISO 1940) ?",
        "Comment améliorer la stabilité de mon rotor ?",
    ]
    cols = st.columns(3)
    for i, q in enumerate(quick):
        with cols[i % 3]:
            if st.button(q[:38] + "…" if len(q) > 38 else q,
                         key=f"qp_{i}", use_container_width=True):
                st.session_state["gpt_input"] = q

    st.markdown("---")

    # Historique du chat
    for msg in st.session_state.get("chat_history", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Saisie utilisateur
    user_input = st.chat_input("Posez votre question…")
    if not user_input:
        user_input = st.session_state.pop("gpt_input", None)

    if user_input:
        st.session_state.setdefault("chat_history", [])
        st.session_state["chat_history"].append(
            {"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("SmartRotor Copilot réfléchit…"):
                context = _build_context()
                response = _call_gemini(
                    user_input, context,
                    st.session_state["chat_history"][:-1]
                )
            st.markdown(response)
            st.session_state["chat_history"].append(
                {"role": "assistant", "content": response})

    if st.session_state.get("chat_history"):
        if st.button("🗑️ Effacer la conversation", key="clear_chat"):
            st.session_state["chat_history"] = []
            st.rerun()


def _build_context() -> dict:
    """Construit le contexte de la session courante."""
    rotor  = st.session_state.get("rotor")
    modal  = st.session_state.get("res_modal")
    ctx    = {"rotor_loaded": rotor is not None}
    if rotor:
        ctx.update({"n_nodes": len(rotor.nodes), "mass_kg": round(float(rotor.m), 2)})
    if modal:
        import numpy as np
        fn = modal.wn / (2 * np.pi)
        ld = getattr(modal, 'log_dec', [])
        ctx["modal"] = {
            "fn_hz":   [round(float(v), 2) for v in fn[:4]],
            "log_dec": [round(float(v), 4) for v in ld[:4]],
        }
    return ctx


def _call_gemini(user_msg: str, context: dict, history: list) -> str:
    """Appel à l'API Gemini avec fallback offline."""
    if not GEMINI_OK:
        return _fallback(user_msg, context)
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            return _fallback(user_msg, context)
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        valid = [m.name for m in genai.list_models()
                 if 'generateContent' in m.supported_generation_methods]
        if not valid:
            return _fallback(user_msg, context)
        model_name = next((m for m in valid if "flash" in m), valid[0])
        system_prompt = f"""Tu es SmartRotor Copilot, ingénieur expert en dynamique
des rotors et spécialiste Python ROSS. Tu aides des ingénieurs et étudiants en Master.
Réponds toujours en français, avec rigueur académique et du code ROSS si pertinent.
Contexte du rotor actuel : {json.dumps(context, ensure_ascii=False)}"""
        model = genai.GenerativeModel(model_name)
        hist  = [{"role":"user","parts":[system_prompt]},
                 {"role":"model","parts":["Compris. Je suis SmartRotor Copilot, prêt."]}]
        for h in history[-6:]:
            hist.append({"role": "user" if h["role"]=="user" else "model",
                         "parts": [h["content"]]})
        chat = model.start_chat(history=hist)
        return chat.send_message(user_msg).text
    except Exception as e:
        return f"⚠️ Erreur Gemini : {e}\n\n{_fallback(user_msg, context)}"


def _fallback(user_msg: str, context: dict) -> str:
    """Réponses offline pré-programmées."""
    msg = user_msg.lower()
    if any(k in msg for k in ["campbell","vitesse critique","1x"]):
        return """## Diagramme de Campbell

Le diagramme de Campbell trace les **fréquences des modes propres** en fonction
de la vitesse de rotation Ω.

**Interprétation :**
- **FW (Forward Whirl)** : précession dans le sens de rotation → fréquence ↑ avec Ω
- **BW (Backward Whirl)** : précession inverse → fréquence ↓ avec Ω
- **Intersections avec 1X** : vitesses critiques synchrones

**Norme API 684** : les vitesses critiques doivent être à ±15 % de la vitesse
opérationnelle.
``````````python
speeds = np.linspace(0, 10000*np.pi/30, 100)
camp   = rotor.run_campbell(speeds, frequencies=12)
camp.plot()
`````````"""
    if any(k in msg for k in ["log dec","stabilit","instabil"]):
        return """## Log Décrément et Stabilité

**δ = 2π·ξ / √(1−ξ²)**

| Valeur | Interprétation |
|--------|----------------|
| δ > 0.3 | ✅ Très stable |
| 0.1 < δ ≤ 0.3 | ✅ Conforme API 684 |
| 0 < δ ≤ 0.1 | ⚠️ Marginalement stable |
| **δ ≤ 0** | **❌ INSTABLE** |

La cause principale d'instabilité : raideur croisée **Kxy** dans les paliers
hydrodynamiques (phénomène *oil whirl*).
````````python
modal = rotor.run_modal(speed=3000*np.pi/30)
print("Log Dec :", modal.log_dec[:6])
```````"""
    if any(k in msg for k in ["balourd","iso 1940","déséquil"]):
        return """## Balourd toléré — Norme ISO 1940

**Uper = m · G / (1000 · ω)**

- **m** : masse du rotor (kg)
- **G** : grade de qualité (G0.4 à G16)
- **ω** : vitesse angulaire (rad/s)

| Grade | Application typique |
|-------|---------------------|
| G0.4 | Gyroscopes, turbines précision |
| G1.0 | Turbines à gaz |
| **G2.5** | **Turbines vapeur, compresseurs** |
| G6.3 | Machines-outils |
``````python
omega  = 3000 * np.pi / 30
m_rot  = rotor.m
Uper   = (m_rot * 2.5) / (1000 * omega)
print(f"Balourd toléré G2.5 : {Uper:.6f} kg·m")
`````"""
    if any(k in msg for k in ["api 684","conformité","zone interdite"]):
        return """## Vérification API 684

**Critères** (2ème édition) :

1. **Marge vitesses critiques ≥ ±15 %** de la vitesse opérationnelle
2. **Log Dec ≥ 0.1** pour tous les modes dans la plage opérationnelle
````python
op_rpm  = 3000
zone_lo = op_rpm * 0.85   # 2 550 RPM
zone_hi = op_rpm * 1.15   # 3 450 RPM

modal   = rotor.run_modal(speed=0)
fn_hz   = modal.wn / (2*np.pi)
vc_rpm  = fn_hz * 60

for i, (vc, ld) in enumerate(zip(vc_rpm[:6], modal.log_dec[:6])):
    in_zone = zone_lo <= vc <= zone_hi
    ok      = not in_zone and ld >= 0.1
    print(f"Mode {i+1}: Vc={vc:.0f} RPM | δ={ld:.3f} | "
          f"{'✅ Conforme' if ok else '❌ Non conforme'}")
```"""
    ctx_str = ""
    if context.get("rotor_loaded"):
        ctx_str = (f"\n\n*Votre rotor : {context.get('n_nodes','?')} nœuds, "
                   f"{context.get('mass_kg','?')} kg*")
    return (f"Je suis SmartRotor Copilot. Votre question : **{user_msg}**\n\n"
            f"Utilisez les boutons de questions rapides ou précisez votre demande "
            f"(Campbell, stabilité, balourd, API 684, ROSS syntax…).{ctx_str}")
```

---

