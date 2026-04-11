# =============================================================================
# tutorials/tutorial_data.py — Mode Pédagogique
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria — ISTLS, Université de Sousse
# 6 Tutoriels interactifs avec théorie, exercices et quiz
# =============================================================================
# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =============================================================================
# DONNÉES DES TUTORIELS
# =============================================================================
TUTORIALS = [
    {
        "id": "T1",
        "icon": "🏗️",
        "title": "Modélisation d'un Rotor",
        "subtitle": "Éléments finis, géométrie et matériaux",
        "level": "Débutant",
        "duration": "20 min",
        "module": "M1",
        "color": "#1F5C8B",
    },
    {
        "id": "T2",
        "icon": "📊",
        "title": "Analyse Modale",
        "subtitle": "Fréquences propres, modes et stabilité",
        "level": "Intermédiaire",
        "duration": "25 min",
        "module": "M2",
        "color": "#22863A",
    },
    {
        "id": "T3",
        "icon": "📈",
        "title": "Diagramme de Campbell",
        "subtitle": "Vitesses critiques et normes API 684",
        "level": "Intermédiaire",
        "duration": "30 min",
        "module": "M3",
        "color": "#C55A11",
    },
    {
        "id": "T4",
        "icon": "🌀",
        "title": "Réponse au Balourd",
        "subtitle": "Excitation synchrone, ISO 1940, orbites",
        "level": "Avancé",
        "duration": "25 min",
        "module": "M4",
        "color": "#7B1FA2",
    },
    {
        "id": "T5",
        "icon": "💧",
        "title": "Paliers Hydrodynamiques",
        "subtitle": "Film fluide, coefficients dynamiques",
        "level": "Avancé",
        "duration": "30 min",
        "module": "M5",
        "color": "#00695C",
    },
    {
        "id": "T6",
        "icon": "⚙️",
        "title": "Systèmes MultiRotors",
        "subtitle": "Engrenages, couplage torsionnel, GearElement",
        "level": "Expert",
        "duration": "35 min",
        "module": "M8",
        "color": "#8B1F1F",
    },
]

LEVEL_COLORS = {
    "Débutant":     ("#e8f5e9", "#22863A"),
    "Intermédiaire":("#fff3e0", "#C55A11"),
    "Avancé":       ("#f3e5f5", "#7B1FA2"),
    "Expert":       ("#ffebee", "#8B1F1F"),
}

# =============================================================================
# POINT D'ENTRÉE PRINCIPAL
# =============================================================================
def render_tutorials():
    _inject_tutorial_css()

    view = st.session_state.get("tut_view", "grid")

    if view == "grid":
        _render_grid()
    else:
        tut_id = st.session_state.get("tut_active_id", "T1")
        tut = next((t for t in TUTORIALS if t["id"] == tut_id), TUTORIALS[0])
        _render_tutorial_page(tut)


# =============================================================================
# PAGE GRILLE — CATALOGUE DES TUTORIELS
# =============================================================================
def _render_grid():
    tut_done = st.session_state.get("tut_done", set())
    pct = int(len(tut_done) / len(TUTORIALS) * 100)

    # ── En-tête ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="tut-hero">
      <div class="tut-hero-text">
        <h1>🎓 Mode Pédagogique</h1>
        <p>Maîtrisez la dynamique des rotors pas à pas — théorie, simulation, quiz</p>
      </div>
      <div class="tut-hero-stats">
        <div class="tut-stat">{done}<span>terminés</span></div>
        <div class="tut-stat">{total}<span>tutoriels</span></div>
        <div class="tut-stat">{pct}%<span>progression</span></div>
      </div>
    </div>
    """.format(done=len(tut_done), total=len(TUTORIALS), pct=pct),
                unsafe_allow_html=True)

    # ── Barre de progression ──────────────────────────────────────────────
    st.markdown("""
    <div class="tut-progress-bar-wrap">
      <div class="tut-progress-bar-fill" style="width:{pct}%"></div>
    </div>
    """.format(pct=pct), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Cartes des tutoriels ──────────────────────────────────────────────
    cols = st.columns(3)
    for i, tut in enumerate(TUTORIALS):
        with cols[i % 3]:
            done = tut["id"] in tut_done
            bg, fg = LEVEL_COLORS.get(tut["level"], ("#F0F4FF","#1F5C8B"))
            badge = "✅ Terminé" if done else tut["level"]
            badge_bg = "#22863A" if done else fg
            st.markdown("""
            <div class="tut-card" style="border-top:4px solid {color};">
              <div class="tut-card-header">
                <span class="tut-icon">{icon}</span>
                <span class="tut-badge" style="background:{badge_bg};color:white;">
                  {badge}
                </span>
              </div>
              <div class="tut-card-title">{title}</div>
              <div class="tut-card-sub">{subtitle}</div>
              <div class="tut-card-meta">
                <span>⏱ {dur}</span>
                <span>🔧 {mod}</span>
              </div>
            </div>
            """.format(
                color=tut["color"], icon=tut["icon"],
                badge=badge, badge_bg=badge_bg,
                title=tut["title"], subtitle=tut["subtitle"],
                dur=tut["duration"], mod=tut["module"]
            ), unsafe_allow_html=True)

            if st.button(
                    "▶  Commencer {}".format(tut["id"]),
                    key="tut_open_{}".format(tut["id"]),
                    use_container_width=True,
                    type="primary"):
                st.session_state["tut_view"]      = "detail"
                st.session_state["tut_active_id"] = tut["id"]
                st.session_state["tut_step"]      = 0
                st.rerun()

    # ── Résumé des badges ─────────────────────────────────────────────────
    if tut_done:
        st.markdown("---")
        st.markdown("### 🏅 Vos badges")
        badge_row = ""
        for tid in tut_done:
            t = next((x for x in TUTORIALS if x["id"] == tid), None)
            if t:
                badge_row += """<span class="tut-earned-badge"
                    style="background:{c};">{icon} {id}</span>""".format(
                    c=t["color"], icon=t["icon"], id=t["id"])
        st.markdown('<div class="tut-badge-row">{}</div>'.format(badge_row),
                    unsafe_allow_html=True)


# =============================================================================
# PAGE DÉTAIL D'UN TUTORIEL
# =============================================================================
def _render_tutorial_page(tut):
    step = st.session_state.get("tut_step", 0)

    # ── Navigation haut ───────────────────────────────────────────────────
    col_back, col_title, col_nav = st.columns([1, 4, 2])
    with col_back:
        if st.button("← Catalogue", key="tut_back"):
            st.session_state["tut_view"] = "grid"
            st.rerun()
    with col_title:
        st.markdown("""
        <div style="padding:6px 0;">
          <span style="font-size:1.3em;font-weight:700;color:{color};">
            {icon} {title}
          </span>
          <br><span style="color:#888;font-size:0.85em;">{sub}</span>
        </div>
        """.format(**tut), unsafe_allow_html=True)

    # ── Dispatch vers le bon tutoriel ─────────────────────────────────────
    fn = {
        "T1": _tutorial_t1,
        "T2": _tutorial_t2,
        "T3": _tutorial_t3,
        "T4": _tutorial_t4,
        "T5": _tutorial_t5,
        "T6": _tutorial_t6,
    }.get(tut["id"], _tutorial_t1)

    steps = fn()   # Retourne la liste des étapes

    # ── Barre d'étapes ────────────────────────────────────────────────────
    n = len(steps)
    step_labels = " → ".join(
        "**{}**".format(steps[i]["title"]) if i == step
        else steps[i]["title"]
        for i in range(n))
    st.caption("Étape {}/{} — {}".format(step + 1, n, step_labels))

    prog = int((step + 1) / n * 100)
    st.markdown("""
    <div class="tut-progress-bar-wrap" style="margin-bottom:12px;">
      <div class="tut-progress-bar-fill"
           style="width:{p}%;background:{c};"></div>
    </div>""".format(p=prog, c=tut["color"]), unsafe_allow_html=True)

    # ── Contenu de l'étape ────────────────────────────────────────────────
    current = steps[step]
    _render_step(current, tut)

    # ── Boutons de navigation ─────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        if step > 0:
            if st.button("◀ Précédent", key="tut_prev", use_container_width=True):
                st.session_state["tut_step"] = step - 1
                st.rerun()
    with c3:
        if step < n - 1:
            if st.button("Suivant ▶", key="tut_next",
                         type="primary", use_container_width=True):
                st.session_state["tut_step"] = step + 1
                st.rerun()
        else:
            if st.button("✅ Terminer", key="tut_finish",
                         type="primary", use_container_width=True):
                done = st.session_state.get("tut_done", set())
                done.add(tut["id"])
                st.session_state["tut_done"] = done
                st.session_state["tut_view"] = "grid"
                st.balloons()
                st.rerun()


# =============================================================================
# RENDERER D'UNE ÉTAPE
# =============================================================================
def _render_step(step_data, tut):
    kind = step_data.get("kind", "theory")

    if kind == "theory":
        _step_theory(step_data, tut)
    elif kind == "formula":
        _step_formula(step_data, tut)
    elif kind == "interactive":
        _step_interactive(step_data, tut)
    elif kind == "quiz":
        _step_quiz(step_data, tut)
    elif kind == "exercise":
        _step_exercise(step_data, tut)
    elif kind == "summary":
        _step_summary(step_data, tut)


def _step_theory(s, tut):
    st.markdown("### {}".format(s["title"]))
    st.markdown(s["content"])
    if "figure" in s:
        s["figure"]()
    if "tip" in s:
        st.info("💡 **Conseil :** " + s["tip"])
    if "warning" in s:
        st.warning("⚠️ " + s["warning"])


def _step_formula(s, tut):
    st.markdown("### {}".format(s["title"]))
    st.markdown(s.get("intro", ""))
    for eq in s.get("equations", []):
        st.markdown("**{}**".format(eq["name"]))
        st.latex(eq["latex"])
        st.caption(eq.get("desc", ""))
    if s.get("table") is not None:
        st.dataframe(s["table"], use_container_width=True, hide_index=True)
    if "note" in s:
        st.info(s["note"])


def _step_interactive(s, tut):
    st.markdown("### {}".format(s["title"]))
    st.markdown(s.get("desc", ""))
    s["widget"]()


def _step_quiz(s, tut):
    st.markdown("### 🧠 Quiz — {}".format(s["title"]))
    st.markdown(s.get("intro", "Testez votre compréhension :"))
    score = 0
    answers = {}
    for qi, q in enumerate(s["questions"]):
        key = "quiz_{}_{}".format(tut["id"], qi)
        ans = st.radio(
            "**Q{}.** {}".format(qi + 1, q["q"]),
            q["choices"], key=key, index=None)
        answers[qi] = ans

    if st.button("Vérifier mes réponses", key="quiz_check_{}".format(tut["id"]),
                 type="primary"):
        for qi, q in enumerate(s["questions"]):
            if answers[qi] == q["answer"]:
                score += 1
                st.success("Q{} ✅ Correct ! {}".format(qi + 1, q.get("explain", "")))
            else:
                st.error("Q{} ❌ Réponse correcte : **{}** — {}".format(
                    qi + 1, q["answer"], q.get("explain", "")))
        pct = int(score / len(s["questions"]) * 100)
        if pct == 100:
            st.balloons()
            st.success("🏆 Parfait ! {}/{}".format(score, len(s["questions"])))
        elif pct >= 60:
            st.info("👍 {}/{} — Bien ! Relisez les points manqués.".format(
                score, len(s["questions"])))
        else:
            st.warning("📚 {}/{} — Relisez la théorie avant de continuer.".format(
                score, len(s["questions"])))


def _step_exercise(s, tut):
    st.markdown("### 🔧 Exercice Pratique — {}".format(s["title"]))
    st.markdown(s.get("desc", ""))
    st.markdown("""
    <div class="tut-exercise-box">
      <strong>🎯 Objectif :</strong> {obj}
    </div>""".format(obj=s.get("objective", "")), unsafe_allow_html=True)
    for i, step_txt in enumerate(s.get("steps", []), 1):
        st.markdown("**Étape {}** — {}".format(i, step_txt))
    if s.get("module_link"):
        mod, node = s["module_link"]
        st.markdown("---")
        if st.button(
                "🚀 Ouvrir le module {} dans la simulation".format(mod),
                key="ex_link_{}_{}".format(tut["id"], mod),
                type="primary"):
            st.session_state["active_module"] = mod
            st.session_state["active_node"]   = node
            st.session_state["nav_mode"]      = "simulation"
            st.rerun()
    if "expected" in s:
        with st.expander("📋 Résultats attendus (spoiler)"):
            st.markdown(s["expected"])


def _step_summary(s, tut):
    st.markdown("### 🎯 Récapitulatif — {}".format(s["title"]))
    st.success("Vous avez couvert tous les concepts essentiels de ce tutoriel !")
    cols = st.columns(2)
    for i, point in enumerate(s.get("key_points", [])):
        with cols[i % 2]:
            st.markdown("✅ " + point)
    if s.get("formulas"):
        st.markdown("#### Formules clés à retenir")
        for f in s["formulas"]:
            st.latex(f)
    if s.get("next_steps"):
        st.markdown("#### 🔜 Pour aller plus loin")
        for ns in s["next_steps"]:
            st.markdown("→ " + ns)


# =============================================================================
# ── T1 : MODÉLISATION ────────────────────────────────────────────────────────
# =============================================================================
def _tutorial_t1():
    def _fig_shaft():
        fig = go.Figure()
        sections = [(0, 0.2, 0.05), (0.2, 0.35, 0.075), (0.35, 0.55, 0.075),
                    (0.55, 0.70, 0.075), (0.70, 0.90, 0.05)]
        for x0, x1, r in sections:
            fig.add_shape(type="rect", x0=x0, x1=x1, y0=-r, y1=r,
                          fillcolor="rgba(31,92,139,0.25)",
                          line=dict(color="#1F5C8B", width=1.5))
        for xb in [0.1, 0.80]:
            fig.add_shape(type="rect", x0=xb-0.015, x1=xb+0.015,
                          y0=-0.09, y1=0.09,
                          fillcolor="rgba(197,90,17,0.6)",
                          line=dict(color="#C55A11", width=1))
        fig.add_shape(type="circle",
                      x0=0.425, x1=0.475, y0=-0.09, y1=0.09,
                      fillcolor="rgba(123,31,162,0.5)",
                      line=dict(color="#7B1FA2", width=1.5))
        fig.update_layout(
            height=180, xaxis=dict(title="Position axiale (m)", range=[-0.05, 0.95]),
            yaxis=dict(title="Rayon (m)", range=[-0.12, 0.12]),
            plot_bgcolor="white", showlegend=False,
            title="Modèle EF d'un rotor (arbre + disque + paliers)",
            margin=dict(l=10, r=10, t=40, b=30))
        st.plotly_chart(fig, use_container_width=True, key="t1_shaft_fig")

    def _widget_shaft():
        st.markdown("**Paramétrez un élément d'arbre et observez sa masse :**")
        c1, c2, c3 = st.columns(3)
        with c1:
            L  = st.slider("Longueur L (m)", 0.05, 0.50, 0.20, 0.01, key="t1_L")
        with c2:
            od = st.slider("Diamètre ext. (m)", 0.02, 0.20, 0.05, 0.005, key="t1_od")
        with c3:
            id_ = st.slider("Diamètre int. (m)", 0.0, 0.18, 0.0, 0.005, key="t1_id")
        if id_ >= od:
            st.error("Le diamètre intérieur doit être inférieur au diamètre extérieur.")
            return
        rho = 7810
        A   = np.pi / 4 * (od**2 - id_**2)
        m   = rho * A * L
        Ip  = rho * A * L * (od**2 + id_**2) / 8
        col1, col2, col3 = st.columns(3)
        col1.metric("Section A (m²)", "{:.4e}".format(A))
        col2.metric("Masse (kg)", "{:.3f}".format(m))
        col3.metric("Ip (kg·m²)", "{:.4e}".format(Ip))
        fig = go.Figure()
        theta = np.linspace(0, 2*np.pi, 60)
        fig.add_trace(go.Scatter(x=np.cos(theta)*od/2, y=np.sin(theta)*od/2,
                                 fill="toself", fillcolor="rgba(31,92,139,0.3)",
                                 line=dict(color="#1F5C8B"), name="Ext."))
        if id_ > 0:
            fig.add_trace(go.Scatter(x=np.cos(theta)*id_/2, y=np.sin(theta)*id_/2,
                                     fill="toself", fillcolor="white",
                                     line=dict(color="#C55A11"), name="Int."))
        fig.update_layout(height=220, xaxis_scaleanchor="y",
                          title="Section transversale",
                          margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True, key="t1_sec_fig")

    return [
        {
            "title": "Introduction",
            "kind":  "theory",
            "content": """
La **méthode des éléments finis (MEF)** est la technique standard pour modéliser un rotor.
L'arbre est discrétisé en **éléments de poutre de Timoshenko** qui prennent en compte :

- La **flexion** (effets de Rayleigh)
- Le **cisaillement transverse** (correction de Timoshenko)
- L'**inertie de rotation** des sections
- Les **effets gyroscopiques** (couplage des plans XZ et YZ)

Chaque nœud possède **4 degrés de liberté (DDL)** : deux translations (x, y) et deux rotations (θx, θy).
            """,
            "figure": _fig_shaft,
            "tip": "ROSS utilise la classe `ShaftElement` qui implémente la formulation de Timoshenko avec termes gyroscopiques automatiques.",
        },
        {
            "title": "Formules",
            "kind":  "formula",
            "intro": "Les matrices élémentaires de l'élément d'arbre sont construites à partir des paramètres géométriques et matériaux :",
            "equations": [
                {
                    "name": "Masse d'un élément cylindrique creux",
                    "latex": r"m_e = \rho \cdot A \cdot L \quad \text{avec } A = \frac{\pi}{4}(D_e^2 - D_i^2)",
                    "desc": "ρ = masse volumique (kg/m³), L = longueur (m)"
                },
                {
                    "name": "Moment d'inertie polaire",
                    "latex": r"I_p = \frac{\pi \rho L}{8}(D_e^4 - D_i^4)",
                    "desc": "Gouverne l'effet gyroscopique"
                },
                {
                    "name": "Raideur en flexion (Euler-Bernoulli)",
                    "latex": r"k_{flex} = \frac{EI}{L^3} \begin{bmatrix} 12 & 6L & -12 & 6L \\ & 4L^2 & -6L & 2L^2 \\ & & 12 & -6L \\ \text{sym.} & & & 4L^2 \end{bmatrix}",
                    "desc": "E = module d'Young, I = moment quadratique de section"
                },
            ],
            "note": "Le paramètre de cisaillement de Timoshenko κ ≈ 0.886 pour un arbre plein circulaire."
        },
        {
            "title": "Simulation",
            "kind":  "interactive",
            "title": "Calcul Interactif",
            "desc":  "Explorez l'influence des dimensions sur les propriétés inertielles :",
            "widget": _widget_shaft,
        },
        {
            "title": "Quiz",
            "kind":  "quiz",
            "title": "Vérification des acquis",
            "questions": [
                {
                    "q": "Combien de DDL par nœud dans un modèle EF de rotor (formulation 3D) ?",
                    "choices": ["2 (Ux, Uy)", "4 (Ux, Uy, θx, θy)", "6 (Ux, Uy, Uz, θx, θy, θz)", "3 (Ux, Uy, θz)"],
                    "answer":  "4 (Ux, Uy, θx, θy)",
                    "explain": "Le modèle de Timoshenko rotatif utilise 2 translations et 2 rotations dans le plan transverse."
                },
                {
                    "q": "Quelle matrice supplémentaire apparaît dans un rotor en rotation, absente dans une structure statique ?",
                    "choices": ["Matrice de masse", "Matrice de raideur géométrique", "Matrice gyroscopique [G]", "Matrice de Coriolis"],
                    "answer":  "Matrice gyroscopique [G]",
                    "explain": "L'effet gyroscopique couple les deux plans de flexion et dépend de la vitesse Ω."
                },
                {
                    "q": "Doubler le diamètre d'un arbre plein multiplie sa raideur en flexion par :",
                    "choices": ["2", "4", "8", "16"],
                    "answer":  "16",
                    "explain": "I ∝ D⁴ pour un cercle plein, donc k_flex ∝ D⁴ → facteur 2⁴ = 16."
                },
            ]
        },
        {
            "title": "Exercice",
            "kind":  "exercise",
            "title": "Construire votre premier rotor",
            "desc":  "Mettez en pratique la modélisation dans le module M1.",
            "objective": "Créer un rotor simple de 5 éléments d'arbre avec un disque central et deux paliers.",
            "steps": [
                "Accéder au module M1 (Constructeur)",
                "Définir le matériau : Acier AISI 1045 (E=211 GPa, ρ=7810 kg/m³)",
                "Saisir 5 éléments d'arbre : L=0.2m, D=50mm chacun",
                "Ajouter un disque au nœud central (nœud 2 ou 3) : m=15kg, Ip=0.047 kg·m²",
                "Placer deux paliers aux extrémités (nœuds 0 et 5) : kxx=kyy=1×10⁶ N/m",
                "Cliquer sur 'Assembler le rotor' et vérifier la masse totale",
            ],
            "module_link": ("M1", "shaft"),
            "expected": """
**Résultats attendus :**
- Masse totale ≈ 17.6 kg (arbre + disque)
- 6 nœuds, 24 DDL
- La géométrie 3D doit montrer un arbre uniforme avec un disque central
            """
        },
        {
            "title": "Résumé",
            "kind":  "summary",
            "title": "T1 — Modélisation EF",
            "key_points": [
                "4 DDL par nœud (Ux, Uy, θx, θy)",
                "Éléments de Timoshenko (cisaillement + inertie de rotation)",
                "Matrice gyroscopique [G] = f(Ω)",
                "Disques → masse concentrée (DiskElement)",
                "Paliers → ressorts/amortisseurs (BearingElement)",
                "ROSS : ShaftElement, DiskElement, BearingElement",
            ],
            "formulas": [
                r"m_e = \rho A L \;,\quad I_p = \frac{\pi\rho L}{8}(D_e^4-D_i^4)",
                r"[M]\{\ddot{q}\} + ([C]+\Omega[G])\{\dot{q}\} + [K]\{q\} = \{F\}",
            ],
            "next_steps": [
                "Tutoriel T2 : Analyse modale (fréquences propres, modes)",
                "Explorer l'influence de la rigidité des paliers sur les modes",
                "Essayer l'exemple `rs.rotor_example()` dans ROSS",
            ]
        },
    ]


# =============================================================================
# ── T2 : ANALYSE MODALE ──────────────────────────────────────────────────────
# =============================================================================
def _tutorial_t2():
    def _fig_modes():
        x = np.linspace(0, 1, 100)
        fig = go.Figure()
        modes = [
            (np.sin(np.pi * x),        "#1F5C8B", "Mode 1 — 1 nœud"),
            (np.sin(2 * np.pi * x),    "#C55A11", "Mode 2 — 2 nœuds"),
            (np.sin(3 * np.pi * x),    "#22863A", "Mode 3 — 3 nœuds"),
        ]
        for shape, color, name in modes:
            fig.add_trace(go.Scatter(x=x, y=shape, name=name,
                                     line=dict(color=color, width=2.5)))
        fig.update_layout(height=260, title="Formes modales typiques d'un rotor encastré-libre",
                          plot_bgcolor="white", xaxis_title="Position axiale normalisée",
                          yaxis_title="Amplitude normalisée",
                          legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True, key="t2_modes_fig")

    def _widget_modal():
        st.markdown("**Influence des paliers sur les fréquences propres :**")
        k = st.select_slider(
            "Raideur des paliers kxx = kyy (N/m)",
            options=[1e5, 5e5, 1e6, 5e6, 1e7, 5e7, 1e8],
            value=1e6, key="t2_k",
            format_func=lambda v: "{:.0e}".format(v))
        c = st.slider("Amortissement cxx = cyy (N·s/m)", 0, 5000, 500, 100, key="t2_c")

        # Calcul simplifié (système masse-ressort-amortisseur approché)
        m_total = 17.6
        omega_n = np.sqrt(k / m_total)
        fn = omega_n / (2 * np.pi)
        zeta = c / (2 * np.sqrt(k * m_total))
        log_dec = 2 * np.pi * zeta / np.sqrt(1 - zeta**2) if zeta < 1 else float('inf')

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("fn (Hz)", "{:.2f}".format(fn))
        col2.metric("fn (RPM)", "{:.0f}".format(fn * 60))
        col3.metric("ζ (amortissement)", "{:.4f}".format(zeta))
        col4.metric("Log Dec δ", "{:.4f}".format(log_dec) if log_dec != float('inf') else "∞")

        if zeta < 0:
            st.error("Système instable ! (ζ < 0)")
        elif zeta == 0:
            st.warning("Système non amorti — résonance infinie théorique")
        elif log_dec >= 0.3:
            st.success("Bonne stabilité (δ ≥ 0.3)")
        else:
            st.info("Stabilité marginale (δ < 0.3 — surveiller)")

        freqs = np.linspace(fn * 0.1, fn * 3, 400)
        omega = 2 * np.pi * freqs
        H = 1 / np.sqrt((1 - (omega/omega_n)**2)**2 + (2*zeta*omega/omega_n)**2)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=freqs, y=H,
                                 line=dict(color="#1F5C8B", width=2), fill="tozeroy",
                                 fillcolor="rgba(31,92,139,0.08)"))
        fig.add_vline(x=fn, line_dash="dash", line_color="#C55A11",
                      annotation_text="fn={:.1f}Hz".format(fn))
        fig.update_layout(height=260, title="FRF — Amplitude normalisée",
                          plot_bgcolor="white",
                          xaxis_title="Fréquence (Hz)", yaxis_title="|H(f)|")
        st.plotly_chart(fig, use_container_width=True, key="t2_frf_fig")

    return [
        {
            "title": "Problème aux valeurs propres",
            "kind":  "theory",
            "content": """
L'analyse modale d'un rotor consiste à résoudre le **problème aux valeurs propres généralisé**.
À vitesse Ω donnée, on cherche les fréquences propres $f_n$ et les formes modales $\\{\\phi\\}$.

Le système peut être **stable** (décroissance après perturbation) ou **instable** (amplification).
La stabilité est quantifiée par le **décrément logarithmique** δ :

- δ > 0.3 : Stable (API 684 exige δ ≥ 0.15 en pratique industrielle)
- 0 < δ < 0.3 : Marginalement stable — surveiller  
- δ ≤ 0 : Instable — **danger opérationnel**

Les **modes** décrivent la déformée du rotor à chaque résonance : mode de translative, 
de pivotement (rocking), de flexion…
            """,
            "figure": _fig_modes,
            "tip": "ROSS : `rotor.run_modal(speed=Ω)` retourne wn (rad/s) et log_dec. Vitesse en rad/s !",
        },
        {
            "title": "Équations",
            "kind":  "formula",
            "intro": "Le problème aux valeurs propres du rotor s'écrit :",
            "equations": [
                {
                    "name": "Problème aux valeurs propres (formulation d'état)",
                    "latex": r"\left([A] - \lambda[B]\right)\{v\} = \{0\}",
                    "desc": "Avec A et B les matrices de l'espace d'état du second ordre"
                },
                {
                    "name": "Valeurs propres complexes",
                    "latex": r"\lambda_k = \sigma_k \pm j\omega_{d,k} \quad \Rightarrow \quad f_{n,k} = \frac{\omega_{d,k}}{2\pi}",
                    "desc": "σ_k : taux d'amortissement modal | ω_d : pulsation amortie"
                },
                {
                    "name": "Décrément logarithmique",
                    "latex": r"\delta_k = \frac{-2\pi\sigma_k}{\omega_{d,k}} = 2\pi\zeta_k / \sqrt{1-\zeta_k^2}",
                    "desc": "Indicateur de stabilité : δ > 0 ⟺ système stable"
                },
                {
                    "name": "Fréquence propre vs vitesse (effet gyroscopique)",
                    "latex": r"f_n(\Omega) = f_{n,0} \pm \frac{\Omega}{2\pi} \cdot \frac{I_p}{I_d}",
                    "desc": "Division des modes en modes avancé (+) et rétrograde (−)"
                },
            ],
        },
        {
            "title": "Interactif",
            "kind":  "interactive",
            "title": "Influence des paliers",
            "desc":  "Modifiez la raideur et l'amortissement des paliers et observez l'effet sur fn et δ :",
            "widget": _widget_modal,
        },
        {
            "title": "Quiz",
            "kind":  "quiz",
            "title": "Stabilité et modes",
            "questions": [
                {
                    "q": "Quelle est la valeur minimale de décrément logarithmique requise par l'API 684 ?",
                    "choices": ["δ = 0.0", "δ ≥ 0.1", "δ ≥ 0.15", "δ ≥ 0.5"],
                    "answer":  "δ ≥ 0.15",
                    "explain": "L'API 684 Section 2.8 exige un décrément log ≥ 0.15 pour toutes les vitesses d'opération."
                },
                {
                    "q": "L'effet gyroscopique sur les fréquences propres d'un rotor en rotation :",
                    "choices": [
                        "N'a aucun effet",
                        "Les fait toutes diminuer",
                        "Les sépare en modes avancé et rétrograde",
                        "Les fait toutes augmenter"
                    ],
                    "answer":  "Les sépare en modes avancé et rétrograde",
                    "explain": "La matrice [G] couple les plans XZ et YZ, scindant chaque paire de modes en modes FW (+) et BW (-)."
                },
                {
                    "q": "Pour un rotor avec amortissement nul (c=0), le décrément logarithmique est :",
                    "choices": ["δ = ∞", "δ = 1", "δ = 0", "δ = π"],
                    "answer":  "δ = 0",
                    "explain": "Sans amortissement, σ_k = 0, donc δ = -2πσ/ω = 0. Le système oscille sans décroître."
                },
            ]
        },
        {
            "title": "Exercice",
            "kind":  "exercise",
            "title": "Analyser les modes du compresseur ROSS",
            "objective": "Calculer et interpréter les 6 premiers modes propres du compresseur centrifuge.",
            "steps": [
                "Charger l'exemple 'Compresseur centrifuge (ROSS)' via le bouton du panneau latéral",
                "Aller dans le module M2 (Statique & Modal)",
                "Lancer l'analyse modale à Ω = 0 RPM",
                "Relever les 6 premières fréquences propres et leurs décréments logarithmiques",
                "Identifier les modes instables (δ ≤ 0) et marginaux (0 < δ < 0.15)",
                "Augmenter l'amortissement des paliers (cxx = cyy = 2000 N·s/m) et relancer",
            ],
            "module_link": ("M2", "static_modal"),
            "expected": """
**Pour le compresseur ROSS (exemple) :**
- Avec cxx=cyy=0 : certains modes proches de δ=0 (paliers non amortis)
- Avec cxx=cyy=2000 : amélioration notable de la stabilité
- Les modes de translation apparaissent en premiers (fn plus basses)
- Les modes de flexion ont des fn plus élevées
            """
        },
        {
            "title": "Résumé",
            "kind":  "summary",
            "title": "T2 — Analyse Modale",
            "key_points": [
                "Problème aux valeurs propres → fn et formes modales",
                "Valeurs propres complexes λ = σ ± jω_d",
                "Décrément logarithmique δ = critère de stabilité",
                "API 684 : δ ≥ 0.15 obligatoire",
                "Effet gyroscopique : séparation FW/BW",
                "ROSS : `rotor.run_modal(speed=omega)`",
            ],
            "formulas": [
                r"\delta = \frac{-2\pi\sigma}{\omega_d} \geq 0.15 \; \text{(API 684)}",
                r"f_{FW/BW}(\Omega) = f_{n,0} \pm \frac{\Omega}{4\pi}\cdot\frac{I_p}{I_d}",
            ],
        },
    ]


# =============================================================================
# ── T3 : DIAGRAMME DE CAMPBELL ───────────────────────────────────────────────
# =============================================================================
def _tutorial_t3():
    def _fig_campbell():
        speeds = np.linspace(0, 5000, 200)  # RPM
        fn1 = 45 + speeds * 0.003
        fn2 = 85 + speeds * 0.005
        fn3 = 140 + speeds * 0.008
        exc1x = speeds / 60
        exc2x = speeds / 30

        fig = go.Figure()
        for fn, col, name in [(fn1,"#1F5C8B","Mode 1"),(fn2,"#22863A","Mode 2"),(fn3,"#7B1FA2","Mode 3")]:
            fig.add_trace(go.Scatter(x=speeds, y=fn, name=name,
                                     line=dict(color=col, width=2.5)))
        for exc, col, name in [(exc1x,"#C55A11","1X"),(exc2x,"#E64A19","2X")]:
            fig.add_trace(go.Scatter(x=speeds, y=exc, name=name,
                                     line=dict(color=col, width=1.8, dash="dash")))

        # Intersections (vitesses critiques approchées)
        for fn_arr, lbl in [(fn1,"Vc1"),(fn2,"Vc2")]:
            diff = fn_arr - exc1x
            idx = np.argmin(np.abs(diff))
            if idx > 0:
                fig.add_vline(x=speeds[idx], line_dash="dot",
                              line_color="#888", line_width=1,
                              annotation_text=lbl, annotation_font_size=9)

        fig.update_layout(
            height=350, title="Diagramme de Campbell (exemple)",
            plot_bgcolor="white", xaxis_title="Vitesse (RPM)",
            yaxis_title="Fréquence (Hz)", yaxis_range=[0, 200],
            legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True, key="t3_camp_fig")

    def _widget_campbell():
        st.markdown("**Calculez la marge API 684 :**")
        c1, c2, c3 = st.columns(3)
        with c1:
            op_rpm = st.number_input("Vitesse nominale (RPM)", 1000, 20000, 3000, 500, key="t3_op")
        with c2:
            fn_hz = st.number_input("Fréquence propre fn (Hz)", 10.0, 500.0, 60.0, 5.0, key="t3_fn")
        with c3:
            harmonic = st.selectbox("Harmonique excitateur", [1, 2, 3], key="t3_harm")

        exc_hz = op_rpm / 60 * harmonic
        fn_rpm = fn_hz * 60
        sep_margin = abs(fn_rpm - op_rpm) / op_rpm * 100
        api_ok = sep_margin >= 15.0

        col1, col2, col3 = st.columns(3)
        col1.metric("Excitation (Hz)", "{:.1f}".format(exc_hz))
        col2.metric("fn en RPM", "{:.0f}".format(fn_rpm))
        col3.metric("Marge de séparation", "{:.1f}%".format(sep_margin),
                    delta="OK" if api_ok else "NON CONFORME",
                    delta_color="normal" if api_ok else "inverse")

        if api_ok:
            st.success("✅ Conforme API 684 (marge ≥ 15%)")
        else:
            st.error("❌ Non conforme API 684 — la vitesse critique est trop proche de la vitesse nominale !")
            recomm_rpm = fn_rpm * (1 + 0.16) if fn_rpm < op_rpm else fn_rpm * (1 - 0.16)
            st.info("💡 Modifier la vitesse nominale à < {:.0f} RPM ou > {:.0f} RPM.".format(
                fn_rpm / 1.15, fn_rpm * 1.15))

    return [
        {
            "title": "Principe",
            "kind":  "theory",
            "content": """
Le **diagramme de Campbell** est l'outil principal pour identifier les **vitesses critiques** d'un rotor.

Il superpose dans un graphique (vitesse vs fréquence) :
- Les **courbes de fréquences propres** fn(Ω) — qui varient légèrement avec la vitesse (effet gyroscopique)
- Les **lignes d'excitation harmonique** : 1X = Ω/60, 2X = 2Ω/60, ...

Chaque **intersection** d'une courbe fn avec une ligne harmonique définit une **vitesse critique** à laquelle une résonance peut se produire.

La norme **API 684** impose que les vitesses critiques soient séparées d'au moins **15%** de la plage de fonctionnement continue.
            """,
            "figure": _fig_campbell,
            "tip": "Les courbes descendantes (modes rétrogrades BW) ne sont généralement pas excitées par un balourd synchrone 1X.",
        },
        {
            "title": "Normes API",
            "kind":  "formula",
            "intro": "La norme API 684 définit des critères stricts pour la séparation des vitesses critiques :",
            "equations": [
                {
                    "name": "Marge de séparation (Separation Margin)",
                    "latex": r"SM = \frac{|N_{crit} - N_{op}|}{N_{op}} \times 100\% \geq 15\%",
                    "desc": "N_crit = vitesse critique (RPM), N_op = vitesse nominale (RPM)"
                },
                {
                    "name": "Plage de fonctionnement (Operating Speed Range)",
                    "latex": r"N_{min} = 0.8 \cdot N_{op} \quad N_{max} = 1.2 \cdot N_{op}",
                    "desc": "Les vitesses critiques doivent être hors de [N_min, N_max]"
                },
                {
                    "name": "Fréquence d'excitation harmonique k",
                    "latex": r"f_{exc,k}(\Omega) = k \cdot \frac{\Omega}{60} \quad k = 1, 2, 3, ...",
                    "desc": "1X = déséquilibre, 2X = désalignement, N×=passage de pales/dents"
                },
            ],
            "table": pd.DataFrame({
                "Excitation": ["1X", "2X", "3X", "N×"],
                "Origine physique": [
                    "Balourd (déséquilibre résiduel)",
                    "Désalignement, accouplement",
                    "Ovalisation, frottement",
                    "Passage d'aubes (N pales)"
                ],
                "Fréquence (Hz)": ["Ω/60", "2Ω/60", "3Ω/60", "N·Ω/60"]
            })
        },
        {
            "title": "Calcul marge",
            "kind":  "interactive",
            "title": "Vérificateur API 684",
            "desc":  "Saisissez les paramètres de votre machine et vérifiez la conformité API :",
            "widget": _widget_campbell,
        },
        {
            "title": "Quiz",
            "kind":  "quiz",
            "title": "Campbell et API 684",
            "questions": [
                {
                    "q": "Quelle est la marge de séparation minimale exigée par l'API 684 ?",
                    "choices": ["5%", "10%", "15%", "20%"],
                    "answer":  "15%",
                    "explain": "API 684 Section 2.5 : SM ≥ 15% pour les vitesses critiques dans la plage opérationnelle."
                },
                {
                    "q": "Sur un diagramme de Campbell, une vitesse critique correspond à :",
                    "choices": [
                        "Un maximum de la courbe fn(Ω)",
                        "Une intersection entre une courbe modale et une ligne harmonique",
                        "La vitesse maximale de fonctionnement",
                        "Le point où fn = 0 Hz"
                    ],
                    "answer":  "Une intersection entre une courbe modale et une ligne harmonique",
                    "explain": "La résonance se produit quand la fréquence d'excitation coïncide avec la fréquence propre."
                },
                {
                    "q": "L'excitation 2X est principalement associée à :",
                    "choices": ["Balourd résiduel", "Désalignement de l'accouplement", "Fissure d'arbre", "Cavitation"],
                    "answer":  "Désalignement de l'accouplement",
                    "explain": "Le désalignement génère une force d'excitation à 2× la fréquence de rotation."
                },
            ]
        },
        {
            "title": "Exercice",
            "kind":  "exercise",
            "title": "Tracer le Campbell du compresseur",
            "objective": "Tracer le diagramme de Campbell et identifier toutes les vitesses critiques dans la plage 0-10000 RPM.",
            "steps": [
                "Aller dans M3 (Campbell + UCS)",
                "Fixer la vitesse maximale à 10 000 RPM avec 50 points",
                "Sélectionner les harmoniques 1X, 2X, 3X",
                "Identifier les intersections avec les lignes harmoniques",
                "Vérifier la marge API 684 pour une vitesse nominale de 3000 RPM",
                "Utiliser l'onglet 'API 684' pour le score de conformité",
            ],
            "module_link": ("M3", "campbell"),
            "expected": """
**Résultats attendus :**
- Plusieurs vitesses critiques visibles selon la raideur des paliers
- L'onglet API 684 doit calculer un score de conformité
- Un score ≥ 80% indique une bonne conception
            """
        },
        {
            "title": "Résumé",
            "kind":  "summary",
            "title": "T3 — Campbell & API 684",
            "key_points": [
                "Vitesse critique = intersection fn(Ω) avec harmonique kX",
                "API 684 : marge ≥ 15% obligatoire",
                "1X = balourd | 2X = désalignement | NX = passage d'aubes",
                "Modes BW (rétrogrades) non excités par le balourd 1X",
                "ROSS : `rotor.run_campbell(speeds, frequencies=n)`",
                "Plage opérationnelle : 0.8Nop < N < 1.2Nop",
            ],
            "formulas": [
                r"SM = \frac{|N_{crit}-N_{op}|}{N_{op}}\times 100 \geq 15\%",
                r"f_{exc,k} = k \cdot \frac{\Omega}{2\pi} \quad [Hz]",
            ],
        },
    ]


# =============================================================================
# ── T4 : RÉPONSE AU BALOURD ──────────────────────────────────────────────────
# =============================================================================
def _tutorial_t4():
    def _fig_balourd():
        freqs = np.linspace(1, 100, 500)
        fn, zeta, U, m_r = 40.0, 0.05, 0.001, 10.0
        omega_n = 2 * np.pi * fn
        omega   = 2 * np.pi * freqs
        amp     = U * omega**2 / np.sqrt((omega_n**2 - omega**2)**2 + (2*zeta*omega_n*omega)**2)
        phase   = np.degrees(np.arctan2(-2*zeta*omega_n*omega, omega_n**2 - omega**2))

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=freqs, y=amp*1e6, name="Amplitude (μm)",
                                  line=dict(color="#1F5C8B", width=2),
                                  fill="tozeroy", fillcolor="rgba(31,92,139,0.08)"),
                      secondary_y=False)
        fig.add_trace(go.Scatter(x=freqs, y=phase, name="Phase (°)",
                                  line=dict(color="#C55A11", width=1.5, dash="dot")),
                      secondary_y=True)
        fig.add_vline(x=fn, line_dash="dash", line_color="#22863A", line_width=2,
                      annotation_text="fn={}Hz".format(fn))
        fig.update_layout(height=280, title="Réponse au balourd — Bode",
                          plot_bgcolor="white", xaxis_title="Fréquence (Hz)",
                          legend=dict(orientation="h", y=1.12))
        fig.update_yaxes(title_text="Amplitude (μm)", secondary_y=False)
        fig.update_yaxes(title_text="Phase (°)", secondary_y=True, range=[-190, 10])
        st.plotly_chart(fig, use_container_width=True, key="t4_bode_fig")

    def _widget_iso():
        st.markdown("**Calculateur ISO 1940 — Grade de balourd résiduel permis :**")
        c1, c2, c3 = st.columns(3)
        with c1:
            G = st.selectbox("Classe ISO 1940", ["G0.4","G1","G2.5","G6.3","G16","G40"], index=2, key="t4_G")
        with c2:
            n_rpm = st.number_input("Vitesse nominale (RPM)", 500, 30000, 3000, 500, key="t4_n")
        with c3:
            mass = st.number_input("Masse du rotor (kg)", 1.0, 10000.0, 15.0, 1.0, key="t4_mass")

        G_val = float(G[1:].replace(",", "."))
        e_perm = G_val * 9.549 / (n_rpm)  # mm (e_max = G / ω_rad)
        U_perm = e_perm * mass  # kg·mm
        st.metric("Excentricité permise e", "{:.4f} mm".format(e_perm))
        st.metric("Balourd résiduel max U", "{:.4f} kg·mm".format(U_perm))
        st.caption("Formule : e = G × 9549 / N_RPM (mm)")

    return [
        {
            "title": "Physique du balourd",
            "kind":  "theory",
            "content": """
Un **balourd** (unbalance) est un défaut de centrage de la masse par rapport à l'axe de rotation.
Il génère une **force centrifuge tournante synchrone (1X)** qui excite le rotor à chaque révolution.

La force de balourd vaut :
$$F_{balourd} = m \\cdot e \\cdot \\Omega^2$$

où $m$ est la masse du rotor, $e$ l'excentricité du centre de masse, et $\\Omega$ la vitesse angulaire.

Cette force **croît avec le carré de la vitesse**, d'où l'importance critique du passage par les vitesses critiques lors de la montée en régime.

La **réponse en fréquence** montre :
- Un pic d'amplitude à chaque fréquence propre
- Un déphasage de 90° à la résonance, et 180° au-delà
            """,
            "figure": _fig_balourd,
            "tip": "La représentation en diagramme de Bode (amplitude + phase vs fréquence) permet de localiser précisément les résonances.",
        },
        {
            "title": "Équations",
            "kind":  "formula",
            "intro": "La réponse au balourd d'un système à 1 DDL s'écrit analytiquement :",
            "equations": [
                {
                    "name": "Force centrifuge de balourd",
                    "latex": r"F(t) = m_u \cdot e \cdot \Omega^2 \cdot e^{j\Omega t}",
                    "desc": "m_u = masse de balourd (kg), e = excentricité (m), Ω = vitesse angulaire (rad/s)"
                },
                {
                    "name": "Amplitude de la réponse (rapport de fréquence r = Ω/ωn)",
                    "latex": r"|X| = \frac{U \cdot r^2}{\sqrt{(1-r^2)^2 + (2\zeta r)^2}}",
                    "desc": "U = me/M (excentricité équivalente), ζ = taux d'amortissement"
                },
                {
                    "name": "Déphasage",
                    "latex": r"\phi = \arctan\!\left(\frac{2\zeta r}{1 - r^2}\right)",
                    "desc": "φ = 90° à la résonance (r=1), quelque soit ζ"
                },
                {
                    "name": "Norme ISO 1940 — Balourd résiduel permis",
                    "latex": r"U_{perm} = m_{rotor} \cdot e_{max} \quad \text{avec} \quad e_{max} = \frac{G \cdot 9549}{N_{RPM}} \; \text{(mm)}",
                    "desc": "G = grade ISO (G2.5 machines standard, G0.4 turbines haute précision)"
                },
            ],
        },
        {
            "title": "ISO 1940",
            "kind":  "interactive",
            "title": "Calculateur ISO 1940",
            "desc":  "Déterminez le balourd résiduel maximal admissible selon votre application :",
            "widget": _widget_iso,
        },
        {
            "title": "Quiz",
            "kind":  "quiz",
            "title": "Balourd et réponse forcée",
            "questions": [
                {
                    "q": "À la résonance (Ω = ωn), le déphasage entre la force de balourd et la réponse est :",
                    "choices": ["0°", "45°", "90°", "180°"],
                    "answer":  "90°",
                    "explain": "À la résonance, φ = 90° quelle que soit la valeur de l'amortissement ζ."
                },
                {
                    "q": "La force de balourd F = m·e·Ω² double si la vitesse de rotation Ω :",
                    "choices": ["Double", "Multiplie par √2", "Multiplie par 4", "Reste constante"],
                    "answer":  "Multiplie par 4",
                    "explain": "F ∝ Ω² : doubler Ω multiplie la force par 2² = 4."
                },
                {
                    "q": "Quelle classe ISO 1940 est requise pour une turbine haute précision ?",
                    "choices": ["G16", "G6.3", "G2.5", "G0.4"],
                    "answer":  "G0.4",
                    "explain": "G0.4 est la classe la plus sévère, réservée aux turbines haute précision et aux gyroscopes."
                },
            ]
        },
        {
            "title": "Exercice",
            "kind":  "exercise",
            "title": "Analyser la réponse au balourd",
            "objective": "Tracer la réponse au balourd et identifier les vitesses de résonance.",
            "steps": [
                "Aller dans M4 (Balourd & H(jω))",
                "Appliquer un balourd de 0.001 kg·m au nœud central",
                "Balayer la plage 0 – 300 Hz avec 300 points",
                "Identifier les pics d'amplitude sur le diagramme de Bode",
                "Vérifier que les pics correspondent aux fn calculés en M2",
                "Tracer le diagramme polaire (orbite) à la vitesse critique",
            ],
            "module_link": ("M4", "unbalance"),
        },
        {
            "title": "Résumé",
            "kind":  "summary",
            "title": "T4 — Réponse au Balourd",
            "key_points": [
                "Balourd → force synchrone 1X = m·e·Ω²",
                "Réponse en fréquence : pic à chaque fn",
                "Déphasage 90° à la résonance",
                "ISO 1940 : grade G (G0.4 à G40)",
                "ROSS : `rotor.run_unbalance_response(node, mag, phase, frequency)`",
                "Orbites elliptiques autour des vitesses critiques",
            ],
            "formulas": [
                r"F_{unbr} = m_u \cdot e \cdot \Omega^2",
                r"|X(\Omega)| = \frac{U r^2}{\sqrt{(1-r^2)^2+(2\zeta r)^2}}",
            ],
        },
    ]


# =============================================================================
# ── T5 : PALIERS HYDRODYNAMIQUES ─────────────────────────────────────────────
# =============================================================================
def _tutorial_t5():
    def _fig_bearing():
        theta = np.linspace(0, 2*np.pi, 200)
        R = 1.0
        C = 0.002
        eps = 0.5

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=R*np.cos(theta), y=R*np.sin(theta),
                                  mode="lines", line=dict(color="#1F5C8B", width=3), name="Coussinet"))
        x_j = [C * eps + (R - C) * np.cos(t) for t in theta]
        y_j = [(R - C) * np.sin(t) for t in theta]
        fig.add_trace(go.Scatter(x=x_j, y=y_j, mode="lines",
                                  line=dict(color="#C55A11", width=2), name="Arbre (excentrique)",
                                  fill="toself", fillcolor="rgba(197,90,17,0.15)"))
        fig.add_annotation(x=0, y=0, text="O<br>(coussinet)", showarrow=False,
                            font=dict(size=9, color="#1F5C8B"))
        fig.add_annotation(x=C*eps, y=0, text="  e (excentricité)", showarrow=False,
                            font=dict(size=9, color="#C55A11"))
        fig.update_layout(height=250, title="Palier HD — Excentricité et film fluide",
                          xaxis_scaleanchor="y", showlegend=True,
                          margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True, key="t5_bearing_fig")

    def _widget_sommerfeld():
        st.markdown("**Nombre de Sommerfeld et régime de fonctionnement :**")
        c1, c2, c3 = st.columns(3)
        with c1:
            mu = st.number_input("Viscosité μ (Pa·s)", 0.001, 0.5, 0.02, 0.005,
                                  format="%.3f", key="t5_mu")
        with c2:
            N_rpm = st.number_input("Vitesse N (RPM)", 500, 20000, 3000, 500, key="t5_N")
        with c3:
            W = st.number_input("Charge W (N)", 100, 100000, 5000, 500, key="t5_W")

        R_m = st.slider("Rayon R (mm)", 20, 200, 50, key="t5_R") * 1e-3
        C_m = st.slider("Jeu radial C (mm)", 0.05, 2.0, 0.2, 0.05, key="t5_C") * 1e-3
        L_m = st.slider("Longueur L (mm)", 20, 200, 50, key="t5_L") * 1e-3

        Ns = N_rpm / 60
        S = (mu * Ns / (W / (R_m * L_m))) * (R_m / C_m)**2
        eps_approx = 1 / (1 + 4 * S)

        col1, col2, col3 = st.columns(3)
        col1.metric("Sommerfeld S", "{:.4f}".format(S))
        col2.metric("Excentricité ε ≈", "{:.3f}".format(min(eps_approx, 0.99)))
        if S < 0.1:
            col3.metric("Régime", "Fortement chargé", delta="Usure risquée", delta_color="inverse")
        elif S < 1.0:
            col3.metric("Régime", "Optimal", delta="Film complet", delta_color="normal")
        else:
            col3.metric("Régime", "Faiblement chargé", delta="Risque d'instabilité", delta_color="inverse")

    return [
        {
            "title": "Film fluide",
            "kind":  "theory",
            "content": """
Les **paliers hydrodynamiques** (HD) soutiennent l'arbre par un film de lubrifiant sous pression,
généré par l'effet de coin (wedge effect) entre l'arbre en rotation et le coussinet.

Caractéristiques principales :
- **Pas de contact métal-métal** en régime de fonctionnement nominal
- **Coefficients de raideur et d'amortissement non-isotropes** : kxx ≠ kyy, kxy ≠ 0
- Les coefficients varient avec la **vitesse**, la **charge** et la **viscosité**
- Peuvent induire l'**instabilité par précession huile** (oil whirl/whip) à ~0.46×Ω

Le **nombre de Sommerfeld S** caractérise le régime de lubrification :
$S = \\frac{\\mu N}{P}\\left(\\frac{R}{C}\\right)^2$
            """,
            "figure": _fig_bearing,
            "warning": "L'instabilité par précession huile (oil whip) survient quand fn_rotor ≈ 0.46Ω. Elle peut être catastrophique.",
        },
        {
            "title": "Équations",
            "kind":  "formula",
            "intro": "Les coefficients dynamiques d'un palier HD (formulation linéarisée) :",
            "equations": [
                {
                    "name": "Nombre de Sommerfeld",
                    "latex": r"S = \frac{\mu N_s}{P}\left(\frac{R}{C}\right)^2 \quad P = \frac{W}{LD}",
                    "desc": "μ = viscosité dynamique (Pa·s), Ns = tr/s, P = pression moyenne, R/C = rapport géométrique"
                },
                {
                    "name": "Matrice de raideur du palier HD",
                    "latex": r"[K_{bearing}] = \begin{bmatrix} k_{xx} & k_{xy} \\ k_{yx} & k_{yy} \end{bmatrix}",
                    "desc": "Termes croisés kxy = kyx ≠ 0 → couplage des plans de vibration"
                },
                {
                    "name": "Condition d'instabilité (Oil Whirl)",
                    "latex": r"f_{whirl} \approx 0.46 \cdot \frac{\Omega}{2\pi} < f_{n,rotor}",
                    "desc": "Si la fréquence de précession huile croise fn → instabilité explosive"
                },
            ],
            "table": pd.DataFrame({
                "Paramètre": ["Raideur directe kxx, kyy", "Raideur croisée kxy", "Amortissement cxx, cyy"],
                "Dépendance": ["Charge W, vitesse Ω", "Vitesse Ω (antisymétrique)", "Viscosité μ, vitesse Ω"],
                "Effet sur stabilité": ["Stabilisant", "Déstabilisant (kxy < 0)", "Stabilisant"]
            })
        },
        {
            "title": "Sommerfeld",
            "kind":  "interactive",
            "title": "Calcul du régime de lubrification",
            "desc":  "Évaluez le nombre de Sommerfeld et le régime de fonctionnement :",
            "widget": _widget_sommerfeld,
        },
        {
            "title": "Quiz",
            "kind":  "quiz",
            "title": "Paliers hydrodynamiques",
            "questions": [
                {
                    "q": "L'instabilité par précession huile (oil whirl) survient généralement à une fréquence ≈ :",
                    "choices": ["0.1×Ω", "0.46×Ω", "1.0×Ω", "2.0×Ω"],
                    "answer":  "0.46×Ω",
                    "explain": "L'huile dans le film tourne en moyenne à ≈0.46Ω, créant une excitation sous-synchrone."
                },
                {
                    "q": "Dans la matrice de raideur d'un palier HD, les termes croisés kxy ont pour effet :",
                    "choices": [
                        "Stabiliser le rotor",
                        "Coupler les plans de vibration, potentiellement déstabilisant",
                        "Augmenter la fréquence propre",
                        "Réduire l'amortissement"
                    ],
                    "answer":  "Coupler les plans de vibration, potentiellement déstabilisant",
                    "explain": "Les termes croisés kxy = -kyx génèrent une force de portance asynchrone qui peut déstabiliser."
                },
            ]
        },
        {
            "title": "Exercice",
            "kind":  "exercise",
            "title": "Modéliser un palier hydrodynamique",
            "objective": "Comparer les réponses d'un rotor avec paliers rigides vs paliers HD.",
            "steps": [
                "Aller dans M5 (Paliers HD)",
                "Définir un palier cylindrique : R=50mm, C=0.2mm, L=50mm, μ=0.02 Pa·s",
                "Calculer les coefficients pour N=3000 RPM et W=5000 N",
                "Comparer fn et δ avec/sans termes croisés kxy",
                "Observer l'effet de la variation de viscosité (μ de 0.01 à 0.05 Pa·s)",
            ],
            "module_link": ("M5", "hd_bearings"),
        },
        {
            "title": "Résumé",
            "kind":  "summary",
            "title": "T5 — Paliers HD",
            "key_points": [
                "Film fluide : pas de contact métal-métal",
                "Coefficients kxx, kyy, kxy, cxx, cyy (fonction de Ω, W, μ)",
                "Termes croisés kxy → déstabilisants",
                "Oil whirl ≈ 0.46Ω → oil whip si fn = 0.46Ω",
                "Nombre de Sommerfeld S caractérise le régime",
                "ROSS : `BearingFluidFilm` / `BearingElement` avec kxy",
            ],
            "formulas": [
                r"S = \frac{\mu N_s}{P}\left(\frac{R}{C}\right)^2",
                r"f_{whirl} \approx 0.46\,\frac{\Omega}{2\pi}",
            ],
        },
    ]


# =============================================================================
# ── T6 : SYSTÈMES MULTIROTORS ────────────────────────────────────────────────
# =============================================================================
def _tutorial_t6():
    def _fig_multirotor():
        fig = go.Figure()
        # Rotor 1 (moteur / pignon z1=37)
        r1_x = np.array([0, 0.3, 0.392, 0.592, 0.792, 0.884, 1.184])
        r1_y = np.array([0.0615, 0.0615, 0.075, 0.075, 0.075, 0.075, 0.0615])
        fig.add_trace(go.Scatter(x=r1_x, y=r1_y, mode="lines+markers",
                                  line=dict(color="#1F5C8B", width=3), name="R1 (moteur)",
                                  fill="tozeroy", fillcolor="rgba(31,92,139,0.12)"))
        # Rotor 2 (turbine / roue z2=159) — en dessous
        r2_x = np.array([0, 0.08, 0.28, 0.48, 1.12])
        r2_y = np.array([-0.1605, -0.1605, -0.1305, -0.1305, -0.1305])
        fig.add_trace(go.Scatter(x=r2_x, y=r2_y, mode="lines+markers",
                                  line=dict(color="#C55A11", width=3), name="R2 (turbine)",
                                  fill="tozeroy", fillcolor="rgba(197,90,17,0.12)"))
        # Engrenages
        fig.add_shape(type="circle", x0=0.55, x1=0.64, y0=0.05, y1=0.10,
                      fillcolor="rgba(31,92,139,0.5)", line=dict(color="#1F5C8B"))
        fig.add_shape(type="circle", x0=0.35, x1=0.76, y0=-0.22, y1=0.08,
                      fillcolor="rgba(197,90,17,0.25)", line=dict(color="#C55A11", dash="dash"))
        fig.add_annotation(x=0.595, y=0.075, text="z₁=37", showarrow=False,
                            font=dict(size=9, color="#1F5C8B"))
        fig.add_annotation(x=0.56, y=-0.07, text="z₂=159", showarrow=False,
                            font=dict(size=9, color="#C55A11"))
        fig.update_layout(height=280, title="Système MultiRotor couplé (ROSS Tutorial Part 4)",
                          xaxis_title="Position axiale (m)", yaxis_title="Rayon (m)",
                          plot_bgcolor="white", showlegend=True,
                          legend=dict(orientation="h", y=1.1),
                          margin=dict(l=10, r=10, t=50, b=30))
        st.plotly_chart(fig, use_container_width=True, key="t6_multi_fig")

    def _widget_gear():
        st.markdown("**Calculateur de paramètres d'engrenage :**")
        c1, c2 = st.columns(2)
        with c1:
            z1 = st.number_input("z₁ (dents pignon)", 10, 200, 37, key="t6_z1")
            n1 = st.number_input("N₁ (RPM)", 100, 30000, 1200, 100, key="t6_n1")
            m_mod = st.number_input("Module (mm)", 0.5, 20.0, 5.0, 0.5, key="t6_mod")
        with c2:
            z2 = st.number_input("z₂ (dents roue)", 10, 500, 159, key="t6_z2")
            pa = st.slider("Angle de pression α (°)", 14.5, 30.0, 22.5, 0.5, key="t6_pa")

        ratio = z1 / z2
        n2 = n1 * ratio
        fe = n1 / 60 * z1
        d1 = m_mod * z1 / 1000
        d2 = m_mod * z2 / 1000
        db1 = d1 * np.cos(np.radians(pa))
        db2 = d2 * np.cos(np.radians(pa))
        aw = (d1 + d2) / 2 * 1000

        df = pd.DataFrame({
            "Paramètre": ["Rapport i = z1/z2", "N₂ (RPM)", "fe (Hz)",
                          "d₁ (mm)", "d₂ (mm)", "d_base1 (mm)", "d_base2 (mm)", "Entraxe aw (mm)"],
            "Valeur":    ["{:.4f}".format(ratio), "{:.1f}".format(n2), "{:.2f}".format(fe),
                          "{:.1f}".format(d1*1000), "{:.1f}".format(d2*1000),
                          "{:.1f}".format(db1*1000), "{:.1f}".format(db2*1000),
                          "{:.1f}".format(aw)]
        })
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.info("💡 La fréquence d'engrènement **fe = {:.1f} Hz** doit être hors des fréquences propres du système couplé.".format(fe))

    return [
        {
            "title": "Systèmes couplés",
            "kind":  "theory",
            "content": """
Un **système MultiRotor** comprend deux arbres ou plus reliés par un engrenage.
La complexité principale vient du **couplage latéral-torsionnel** introduit par l'engrenage :

1. **Le rapport de transmission** lie les vitesses : $N_2 = N_1 \\cdot z_1/z_2$
2. **La raideur de maille** $k_{mesh}$ couple les déplacements latéraux des deux arbres
3. **La fréquence d'engrènement** $f_e = N_1 \\cdot z_1 / 60$ est une source d'excitation majeure
4. Les **harmoniques de fe** (2fe, 3fe) apparaissent en cas de défaut de profil de dent

Le diagramme de Campbell du système couplé doit donc inclure les lignes d'excitation à **fe, 2fe, 3fe** en plus des harmoniques de rotation.
            """,
            "figure": _fig_multirotor,
            "tip": "Dans ROSS, GearElement hérite de DiskElement mais ajoute les paramètres de denture (n_teeth, base_diameter, pressure_angle).",
        },
        {
            "title": "Équations",
            "kind":  "formula",
            "intro": "Le système MultiRotor est régi par les équations couplées :",
            "equations": [
                {
                    "name": "Rapport de transmission",
                    "latex": r"i = \frac{z_1}{z_2} = \frac{N_1}{N_2} = \frac{\omega_1}{\omega_2}",
                    "desc": "z1, z2 = nombres de dents, N1, N2 = vitesses en RPM"
                },
                {
                    "name": "Fréquence d'engrènement",
                    "latex": r"f_e = N_1 \cdot \frac{z_1}{60} = N_2 \cdot \frac{z_2}{60} \quad [\text{Hz}]",
                    "desc": "Identique quelle que soit l'entrée — fréquence de contact répété des dents"
                },
                {
                    "name": "Équation du mouvement couplé",
                    "latex": r"\begin{bmatrix}M_1 & 0 \\ 0 & M_2\end{bmatrix}\ddot{q} + \left(\begin{bmatrix}C_1 & 0 \\ 0 & C_2\end{bmatrix}+\Omega[G]\right)\dot{q} + \begin{bmatrix}K_1+K_c & K_{12} \\ K_{21} & K_2+K_c\end{bmatrix}q = F",
                    "desc": "K_c = matrice de couplage par engrenage (fonction de k_mesh et de l'angle de pression)"
                },
                {
                    "name": "Diamètre de base (denture droite)",
                    "latex": r"d_b = m_z \cdot z \cdot \cos(\alpha) \quad \text{avec} \; m_z = \frac{d}{z}",
                    "desc": "α = angle de pression, m_z = module, d = diamètre primitif"
                },
            ],
        },
        {
            "title": "Paramètres engrenage",
            "kind":  "interactive",
            "title": "Calculateur d'engrenage",
            "desc":  "Calculez tous les paramètres géométriques et cinématiques de votre engrenage :",
            "widget": _widget_gear,
        },
        {
            "title": "Quiz",
            "kind":  "quiz",
            "title": "MultiRotor et engrenages",
            "questions": [
                {
                    "q": "Pour un engrenage avec z1=37 dents et N1=1200 RPM, la fréquence d'engrènement fe est :",
                    "choices": ["20 Hz", "740 Hz", "1200 Hz", "37 Hz"],
                    "answer":  "740 Hz",
                    "explain": "fe = N1 × z1 / 60 = 1200 × 37 / 60 = 740 Hz."
                },
                {
                    "q": "Le terme de couplage Kc dans la matrice de raideur globale dépend principalement de :",
                    "choices": [
                        "La masse des engrenages uniquement",
                        "La raideur de maille k_mesh et l'angle de pression α",
                        "La vitesse de rotation uniquement",
                        "L'amortissement des paliers"
                    ],
                    "answer":  "La raideur de maille k_mesh et l'angle de pression α",
                    "explain": "La matrice de couplage Kc = k_mesh × T(α) où T dépend de l'angle de pression et de la géométrie."
                },
                {
                    "q": "Dans ROSS, la classe qui modélise une roue dentée sur un arbre est :",
                    "choices": ["DiskElement", "GearElement", "BearingElement", "ShaftElement"],
                    "answer":  "GearElement",
                    "explain": "GearElement hérite de DiskElement et ajoute les paramètres n_teeth, base_diameter, pressure_angle, helix_angle."
                },
            ]
        },
        {
            "title": "Exercice",
            "kind":  "exercise",
            "title": "Analyser le benchmark ROSS Part 4",
            "objective": "Charger le modèle de référence MultiRotor et valider les fréquences propres.",
            "steps": [
                "Aller dans M8 (MultiRotor & GearElement)",
                "Charger le 'Modèle de référence ROSS Tutorial Part 4'",
                "Cliquer sur 'Assembler et lancer tous les calculs'",
                "Observer le diagramme de Campbell couplé avec fe=740 Hz",
                "Comparer les fn calculés avec les valeurs de référence dans l'onglet Benchmark",
                "Vérifier l'écart moyen (objectif : < 5%)",
            ],
            "module_link": ("M8", "multirotor"),
            "expected": """
**Valeurs de référence ROSS Part 4 :**
- Mode 1 : 109 Hz | Mode 2 : 116 Hz | Mode 3 : 146 Hz | Mode 4 : 148 Hz
- Mode 5 : 276 Hz | Mode 6 : 288 Hz | Mode 7 : 447 Hz | Mode 8 : 519 Hz
- fe = 740 Hz (doit apparaître comme ligne horizontale dans Campbell)
            """
        },
        {
            "title": "Résumé",
            "kind":  "summary",
            "title": "T6 — Systèmes MultiRotors",
            "key_points": [
                "Rapport i = z1/z2 = N1/N2",
                "Fréquence d'engrènement fe = N1·z1/60",
                "Couplage latéral-torsionnel via k_mesh",
                "Campbell : lignes fe, 2fe, 3fe à surveiller",
                "GearElement = DiskElement + paramètres denture",
                "MultiRotor : assemblage des deux rotors couplés",
            ],
            "formulas": [
                r"f_e = N_1 \cdot \frac{z_1}{60} \; \text{Hz}",
                r"i = \frac{z_1}{z_2} = \frac{N_1}{N_2}",
            ],
            "next_steps": [
                "Explorer l'influence de k_mesh sur les fréquences propres couplées",
                "Comparer engrenage droit (α=20°) vs hélicoïdal (β=15°)",
                "Tutoriel avancé : diagnostic de défauts d'engrenage par analyse spectrale",
            ]
        },
    ]


# =============================================================================
# CSS
# =============================================================================
def _inject_tutorial_css():
    st.markdown("""
<style>
/* ── Hero ─────────────────────────────────────── */
.tut-hero {
  display:flex; justify-content:space-between; align-items:center;
  background:linear-gradient(135deg,#1F5C8B 0%,#153F62 100%);
  color:white; padding:28px 32px; border-radius:12px; margin-bottom:16px;
}
.tut-hero h1 { margin:0; font-size:1.8em; font-weight:800; }
.tut-hero p  { margin:4px 0 0; opacity:.8; font-size:0.95em; }
.tut-hero-stats { display:flex; gap:24px; }
.tut-stat {
  text-align:center; font-size:2em; font-weight:800; line-height:1;
}
.tut-stat span { display:block; font-size:0.35em; font-weight:400; opacity:.75; margin-top:3px; }

/* ── Progress bar ─────────────────────────────── */
.tut-progress-bar-wrap {
  background:#E0E7EF; border-radius:99px; height:8px; width:100%; overflow:hidden;
}
.tut-progress-bar-fill {
  background:linear-gradient(90deg,#1F5C8B,#22863A);
  height:100%; border-radius:99px;
  transition:width .6s ease;
}

/* ── Cards ────────────────────────────────────── */
.tut-card {
  background:white; border-radius:10px; padding:16px 18px 12px;
  box-shadow:0 2px 8px rgba(0,0,0,.08); margin-bottom:12px;
  transition:transform .15s,box-shadow .15s;
}
.tut-card:hover { transform:translateY(-2px); box-shadow:0 5px 18px rgba(0,0,0,.13); }
.tut-card-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }
.tut-icon { font-size:1.8em; }
.tut-badge {
  font-size:0.72em; padding:3px 10px; border-radius:99px;
  font-weight:600; letter-spacing:.02em;
}
.tut-card-title { font-size:1.0em; font-weight:700; color:#1A1A2E; margin-bottom:4px; }
.tut-card-sub   { font-size:0.82em; color:#6B7280; margin-bottom:8px; }
.tut-card-meta  { display:flex; gap:14px; font-size:0.78em; color:#9CA3AF; }

/* ── Badges earned ────────────────────────────── */
.tut-badge-row  { display:flex; flex-wrap:wrap; gap:8px; margin-top:8px; }
.tut-earned-badge {
  color:white; padding:5px 14px; border-radius:99px;
  font-size:0.85em; font-weight:700;
}

/* ── Exercise box ─────────────────────────────── */
.tut-exercise-box {
  background:#FFF8E1; border-left:4px solid #C55A11;
  padding:12px 16px; border-radius:0 8px 8px 0; margin:12px 0;
  font-size:0.95em;
}
</style>
""", unsafe_allow_html=True)
