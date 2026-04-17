# =============================================================================
# SNIPPET À INTÉGRER DANS app.py — Remplace render_dashboard()
# =============================================================================

def render_dashboard():
    # ── CSS du tableau de bord ─────────────────────────────────────────────
    st.markdown("""
    <style>
    /* ── Hero Dashboard ───────────────────────────────────────────────── */
    .dash-hero {
        background: linear-gradient(135deg, #0F1923 0%, #153F62 50%, #1F5C8B 100%);
        border-radius: 14px;
        padding: 36px 40px 30px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
        border: 1.5px solid rgba(31,92,139,0.4);
    }
    .dash-hero::before {
        content: "";
        position: absolute;
        right: -60px; top: -60px;
        width: 280px; height: 280px;
        border-radius: 50%;
        background: rgba(31,92,139,0.18);
        pointer-events: none;
    }
    .dash-hero::after {
        content: "";
        position: absolute;
        right: 60px; bottom: -80px;
        width: 200px; height: 200px;
        border-radius: 50%;
        background: rgba(34,134,58,0.12);
        pointer-events: none;
    }
    .dash-hero-title {
        font-size: 2.2em;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.5px;
        margin: 0 0 4px;
        line-height: 1.1;
    }
    .dash-hero-sub {
        color: rgba(255,255,255,0.70);
        font-size: 1.05em;
        margin: 0 0 20px;
    }
    .dash-hero-author {
        color: rgba(255,255,255,0.45);
        font-size: 0.82em;
        letter-spacing: 0.04em;
    }
    .dash-hero-badges {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 16px;
    }
    .dash-hero-badge {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.2);
        color: rgba(255,255,255,0.85);
        padding: 4px 12px;
        border-radius: 99px;
        font-size: 0.76em;
        font-weight: 600;
        letter-spacing: 0.04em;
    }
    .dash-hero-badge.ok  { background: rgba(34,134,58,0.25); border-color: rgba(34,134,58,0.5); color: #7FE5A0; }
    .dash-hero-badge.err { background: rgba(192,0,0,0.25);   border-color: rgba(192,0,0,0.5);   color: #FF8F8F; }

    /* ── Grille des métriques ──────────────────────────────────────────── */
    .dash-metrics-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 26px;
    }
    .dash-metric {
        background: #FFFFFF;
        border: 1.5px solid #D0D8E4;
        border-radius: 10px;
        padding: 16px 18px;
        position: relative;
        overflow: hidden;
        transition: box-shadow 0.2s;
    }
    .dash-metric::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
    }
    .dash-metric.blue::before  { background: #1F5C8B; }
    .dash-metric.green::before { background: #22863A; }
    .dash-metric.orange::before{ background: #C55A11; }
    .dash-metric.purple::before{ background: #7B1FA2; }
    .dash-metric-icon  { font-size: 1.6em; margin-bottom: 8px; }
    .dash-metric-label { font-size: 0.74em; font-weight: 600; color: #6B7280; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 2px; }
    .dash-metric-value { font-size: 1.6em; font-weight: 800; color: #1A1A2E; line-height: 1; }
    .dash-metric-sub   { font-size: 0.76em; color: #9CA3AF; margin-top: 3px; }
    .dash-metric-ok    { color: #22863A !important; }
    .dash-metric-err   { color: #C00000 !important; }
    .dash-metric-warn  { color: #C55A11 !important; }

    /* ── Section header ────────────────────────────────────────────────── */
    .dash-section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 0 0 16px;
        padding-bottom: 10px;
        border-bottom: 2px solid #EBF4FB;
    }
    .dash-section-title {
        font-size: 1.05em;
        font-weight: 700;
        color: #1F5C8B;
        letter-spacing: -0.2px;
    }
    .dash-section-badge {
        background: #EBF4FB;
        color: #1F5C8B;
        border: 1px solid #B5D4F4;
        border-radius: 99px;
        padding: 2px 10px;
        font-size: 0.72em;
        font-weight: 700;
        letter-spacing: 0.04em;
    }

    /* ── Cartes de modules ─────────────────────────────────────────────── */
    .dash-module-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 14px;
        margin-bottom: 28px;
    }
    .dash-module-card {
        background: #FFFFFF;
        border: 1.5px solid #D0D8E4;
        border-radius: 12px;
        padding: 0;
        overflow: hidden;
        transition: transform 0.15s, box-shadow 0.15s;
    }
    .dash-module-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(31,92,139,0.12);
    }
    .dash-module-card-header {
        height: 5px;
        width: 100%;
    }
    .dash-module-card-body {
        padding: 14px 16px 10px;
    }
    .dash-module-card-top {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 6px;
    }
    .dash-module-icon {
        font-size: 1.3em;
        width: 36px; height: 36px;
        display: flex; align-items: center; justify-content: center;
        border-radius: 8px;
        flex-shrink: 0;
    }
    .dash-module-id-badge {
        font-size: 0.68em;
        font-weight: 800;
        letter-spacing: 0.08em;
        padding: 2px 8px;
        border-radius: 99px;
        text-transform: uppercase;
    }
    .dash-module-new {
        font-size: 0.64em;
        font-weight: 700;
        background: #F3E5F5;
        color: #4A148C;
        border: 1px solid #CE93D8;
        border-radius: 99px;
        padding: 2px 7px;
        margin-left: 4px;
    }
    .dash-module-title {
        font-size: 0.92em;
        font-weight: 700;
        color: #1A1A2E;
        margin-bottom: 3px;
    }
    .dash-module-desc {
        font-size: 0.78em;
        color: #6B7280;
        line-height: 1.4;
        margin-bottom: 8px;
    }
    .dash-module-status {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.70em;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 99px;
        margin-bottom: 4px;
    }
    .dash-module-status.done { background: #E8F5E9; color: #1B5E20; border: 1px solid #A5D6A7; }
    .dash-module-status.none { background: #F3F4F6; color: #9CA3AF; border: 1px solid #E5E7EB; }

    /* ── Zone de progression globale ───────────────────────────────────── */
    .dash-progress-wrap {
        background: #FFFFFF;
        border: 1.5px solid #D0D8E4;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
    }
    .dash-progress-header {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 10px;
    }
    .dash-progress-label { font-size: 0.85em; font-weight: 700; color: #1A1A2E; }
    .dash-progress-pct   { font-size: 1.4em; font-weight: 800; color: #1F5C8B; }
    .dash-progress-bar   { height: 8px; background: #EBF4FB; border-radius: 99px; overflow: hidden; }
    .dash-progress-fill  { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #1F5C8B, #22863A); transition: width 0.6s ease; }

    /* ── Activité récente ──────────────────────────────────────────────── */
    .dash-log-wrap {
        background: #1E1E2E;
        border: 1.5px solid #2D3748;
        border-radius: 10px;
        padding: 14px 16px;
    }
    .dash-log-title {
        font-size: 0.72em;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #4A6584;
        margin-bottom: 8px;
    }
    .dash-log-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 3px 0;
        font-family: monospace;
        font-size: 0.76em;
        color: #8A9BB0;
    }
    .dash-log-item.ok   { color: #4CAF50; }
    .dash-log-item.warn { color: #FF9800; }
    .dash-log-item.err  { color: #F44336; }
    .dash-log-ts { color: #4A6584; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

    rotor   = st.session_state.get("rotor")
    n_done  = len(st.session_state.get("tut_done", set()))
    n_res   = sum(1 for k in ["res_modal","res_campbell","res_unbalance","res_temporal"]
                  if st.session_state.get(k) is not None)
    logs    = st.session_state.get("log_messages", [])

    # ── HERO ──────────────────────────────────────────────────────────────
    ross_badge_cls = "ok" if ROSS_AVAILABLE else "err"
    ross_badge_lbl = "ROSS {} actif".format(ROSS_VERSION) if ROSS_AVAILABLE else "ROSS absent"
    rotor_badge_lbl= "{} nœuds · {:.1f} kg".format(len(rotor.nodes), rotor.m) if rotor else "Aucun rotor"
    rotor_badge_cls= "ok" if rotor else "err"

    st.markdown("""
    <div class="dash-hero">
      <div class="dash-hero-title">⚙ RotorLab Suite 2.0</div>
      <div class="dash-hero-sub">Plateforme Avancée de Simulation en Dynamique des Rotors</div>
      <div class="dash-hero-author">{author} — {inst}</div>
      <div class="dash-hero-badges">
        <span class="dash-hero-badge {rc}">{rl}</span>
        <span class="dash-hero-badge {roc}">{rol}</span>
        <span class="dash-hero-badge">v{ver}</span>
        <span class="dash-hero-badge">{nd} / 6 tutoriels</span>
        <span class="dash-hero-badge">{nr} / 9 analyses</span>
      </div>
    </div>
    """.format(
        author=APP_AUTHOR, inst=APP_INST, ver=APP_VERSION,
        rc=ross_badge_cls,  rl=ross_badge_lbl,
        roc=rotor_badge_cls, rol=rotor_badge_lbl,
        nd=n_done, nr=n_res,
    ), unsafe_allow_html=True)

    # ── MÉTRIQUES ─────────────────────────────────────────────────────────
    rotor_val   = "{} nœuds".format(len(rotor.nodes)) if rotor else "Aucun"
    rotor_sub   = "{:.2f} kg · {} DDL".format(rotor.m, rotor.ndof) if rotor else "Construisez M1"
    rotor_cls   = "dash-metric-ok" if rotor else "dash-metric-err"
    ross_val    = ROSS_VERSION if ROSS_AVAILABLE else "Absent"
    ross_cls    = "dash-metric-ok" if ROSS_AVAILABLE else "dash-metric-err"
    analyses_pct= int(n_res / 9 * 100)
    tut_pct     = int(n_done / 6 * 100)

    st.markdown("""
    <div class="dash-metrics-row">
      <div class="dash-metric blue">
        <div class="dash-metric-icon">⚙</div>
        <div class="dash-metric-label">Moteur ROSS</div>
        <div class="dash-metric-value {rc}">{rv}</div>
        <div class="dash-metric-sub">ross-rotordynamics</div>
      </div>
      <div class="dash-metric green">
        <div class="dash-metric-icon">🔩</div>
        <div class="dash-metric-label">Rotor actif</div>
        <div class="dash-metric-value {rotc}">{rotv}</div>
        <div class="dash-metric-sub">{rots}</div>
      </div>
      <div class="dash-metric orange">
        <div class="dash-metric-icon">📊</div>
        <div class="dash-metric-label">Analyses calculées</div>
        <div class="dash-metric-value">{nr} <span style="font-size:0.5em;color:#9CA3AF;">/ 9</span></div>
        <div class="dash-metric-sub">Progression {ap}%</div>
      </div>
      <div class="dash-metric purple">
        <div class="dash-metric-icon">🎓</div>
        <div class="dash-metric-label">Tutoriels</div>
        <div class="dash-metric-value">{nd} <span style="font-size:0.5em;color:#9CA3AF;">/ 6</span></div>
        <div class="dash-metric-sub">Progression {tp}%</div>
      </div>
    </div>
    """.format(
        rc=ross_cls, rv=ross_val,
        rotc=rotor_cls, rotv=rotor_val, rots=rotor_sub,
        nr=n_res, ap=analyses_pct,
        nd=n_done, tp=tut_pct,
    ), unsafe_allow_html=True)

    # ── BARRE DE PROGRESSION GLOBALE ──────────────────────────────────────
    global_pct = min(100, int((n_res / 9 * 50) + (n_done / 6 * 30) + (20 if rotor else 0)))
    st.markdown("""
    <div class="dash-progress-wrap">
      <div class="dash-progress-header">
        <span class="dash-progress-label">Progression globale du projet</span>
        <span class="dash-progress-pct">{pct}%</span>
      </div>
      <div class="dash-progress-bar">
        <div class="dash-progress-fill" style="width:{pct}%"></div>
      </div>
    </div>
    """.format(pct=global_pct), unsafe_allow_html=True)

    # ── MODULES ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="dash-section-header">
      <span class="dash-section-title">Accès rapide aux modules</span>
      <span class="dash-section-badge">9 modules</span>
    </div>
    """, unsafe_allow_html=True)

    modules_info = [
        ("M1", "🏗️", "Constructeur",      "Géométrie, matériaux, paliers",       "shaft",        "#1F5C8B", "#EBF4FB", False, "res_modal"),
        ("M2", "📊", "Statique & Modal",  "Déflexion, fréquences propres",       "static_modal", "#22863A", "#E8F5E9", False, "res_modal"),
        ("M3", "📈", "Campbell + UCS",    "Stabilité, vitesses critiques",        "campbell",     "#C55A11", "#FFF3E0", False, "res_campbell"),
        ("M4", "🌀", "Balourd & H(jω)",   "Bode, polaire, ISO 1940",             "unbalance",    "#7B1FA2", "#F3E5F5", False, "res_unbalance"),
        ("M5", "💧", "Paliers HD",        "Film fluide, coefficients",            "hd_bearings",  "#00796B", "#E0F2F1", True,  None),
        ("M6", "⏱️", "Temporel",          "Newmark, orbites, waterfall 3D",      "temporal",     "#F57C00", "#FFF3E0", False, "res_temporal"),
        ("M7", "🔧", "Défauts",           "Fissure, désalignement, frottement",  "faults",       "#C62828", "#FFEBEE", False, None),
        ("M8", "⚙️", "MultiRotor",        "GearElement, engrenages couplés",     "multirotor",   "#4527A0", "#EDE7F6", True,  None),
        ("M9", "📄", "Rapport PDF",       "Export complet multi-sections",       "report",       "#37474F", "#ECEFF1", False, None),
    ]

    # Affichage en HTML + boutons Streamlit en dessous
    html_cards = '<div class="dash-module-grid">'
    for mid, icon, title, desc, node, color, bg, is_new, res_key in modules_info:
        has_result = st.session_state.get(res_key) is not None if res_key else False
        status_cls = "done" if has_result else "none"
        status_lbl = "Calculé" if has_result else "Non calculé"
        new_tag    = '<span class="dash-module-new">NEW</span>' if is_new else ""
        html_cards += """
        <div class="dash-module-card">
          <div class="dash-module-card-header" style="background:{color};"></div>
          <div class="dash-module-card-body">
            <div class="dash-module-card-top">
              <div class="dash-module-icon" style="background:{bg};">{icon}</div>
              <div>
                <span class="dash-module-id-badge" style="background:{bg};color:{color};">{mid}</span>
                {new_tag}
              </div>
            </div>
            <div class="dash-module-title">{title}</div>
            <div class="dash-module-desc">{desc}</div>
            <span class="dash-module-status {sc}">{sl}</span>
          </div>
        </div>
        """.format(
            color=color, bg=bg, icon=icon, mid=mid,
            new_tag=new_tag, title=title, desc=desc,
            sc=status_cls, sl=status_lbl
        )
    html_cards += "</div>"
    st.markdown(html_cards, unsafe_allow_html=True)

    # Boutons Streamlit (fonctionnels) — alignés sous la grille
    cols = st.columns(3)
    for i, (mid, icon, title, desc, node, color, bg, is_new, _) in enumerate(modules_info):
        with cols[i % 3]:
            _node, _module = node, mid
            def _make_cb(n, m):
                def _cb():
                    st.session_state["active_node"]   = n
                    st.session_state["active_module"] = m
                    st.session_state["nav_mode"]      = "simulation"
                return _cb
            st.button(
                "Ouvrir {}".format(mid),
                key="dash2_{}".format(mid),
                use_container_width=True,
                type="primary",
                on_click=_make_cb(_node, _module)
            )

    # ── JOURNAL D'ACTIVITÉ ────────────────────────────────────────────────
    if logs:
        st.markdown("""
        <div class="dash-section-header" style="margin-top:24px;">
          <span class="dash-section-title">Journal d'activité</span>
          <span class="dash-section-badge">{n} entrées</span>
        </div>
        """.format(n=len(logs)), unsafe_allow_html=True)

        log_items = ""
        for log in reversed(logs[-6:]):
            cls = {"ok": "ok", "warn": "warn", "err": "err"}.get(log["level"], "")
            log_items += '<div class="dash-log-item {cls}"><span class="dash-log-ts">[{ts}]</span> {icon} {msg}</div>'.format(
                cls=cls, ts=log["ts"], icon=log["icon"], msg=log["msg"])

        st.markdown("""
        <div class="dash-log-wrap">
          <div class="dash-log-title">Activité récente</div>
          {items}
        </div>
        """.format(items=log_items), unsafe_allow_html=True)
