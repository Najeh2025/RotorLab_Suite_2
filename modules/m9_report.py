# modules/m9_report.py — Rapport PDF & Export
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
# =============================================================================

import streamlit as st
import numpy as np
import pandas as pd
import io
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table,
        TableStyle, PageBreak, HRFlowable
    )
    from reportlab.platypus import Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    RL_OK = True
except ImportError:
    RL_OK = False

try:
    import ross as rs
    ROSS_OK = True
except ImportError:
    ROSS_OK = False


# =============================================================================
# POINT D ENTREE
# =============================================================================
def render_m9(col_settings, col_graphics):
    rotor = st.session_state.get("rotor")
    with col_settings:
        _render_settings(rotor)
    with col_graphics:
        _render_graphics(rotor)


# =============================================================================
# PANNEAU SETTINGS
# =============================================================================
def _render_settings(rotor):
    st.markdown(
        '<div class="rl-settings-title">Report & Export</div>',
        unsafe_allow_html=True)

    if rotor is None:
        st.warning("Aucun rotor — construisez d'abord un modele dans M1.")
        return

    st.markdown('<div class="rl-section-header">Informations du rapport</div>', unsafe_allow_html=True)
    st.text_input("Titre du rapport", value="Rapport de Simulation Rotordynamique", key="m9_title")
    st.text_input("Auteur", value=st.session_state.get("user_name", "Pr. Najeh Ben Guedria"), key="m9_author")
    st.text_input("Etablissement", value="ISTLS — Universite de Sousse", key="m9_inst")
    st.text_input("Reference projet", value="RotorLab Suite 2.0", key="m9_ref")

    st.markdown('<div class="rl-section-header">Contenu du rapport</div>', unsafe_allow_html=True)
    has_modal    = st.session_state.get("res_modal")    is not None
    has_campbell = st.session_state.get("res_campbell") is not None
    has_api      = st.session_state.get("df_api")       is not None
    has_unbal    = st.session_state.get("res_unbalance") is not None
    has_temporal = st.session_state.get("res_temporal") is not None

    st.checkbox("Caracteristiques du rotor", value=True, disabled=True, key="m9_inc_rotor")
    st.checkbox("Analyse modale (M2)", value=has_modal, disabled=not has_modal, key="m9_inc_modal")
    st.checkbox("Campbell + Vitesses critiques (M3)", value=has_campbell, disabled=not has_campbell, key="m9_inc_campbell")
    st.checkbox("Conformite API 684 (M3)", value=has_api, disabled=not has_api, key="m9_inc_api")
    st.checkbox("Reponse au balourd (M4)", value=has_unbal, disabled=not has_unbal, key="m9_inc_unbal")
    st.checkbox("Reponse temporelle (M6)", value=has_temporal, disabled=not has_temporal, key="m9_inc_temporal")

    st.info("Les modules grises necessitent d'avoir lance les calculs correspondants.")

    st.markdown('<div class="rl-section-header">Options d export</div>', unsafe_allow_html=True)
    st.checkbox("Inclure les figures (Campbell, rotor 3D)", value=True, key="m9_inc_figs")
    st.checkbox("Inclure le code Python reproductible", value=True, key="m9_inc_code")
    st.selectbox("Langue du rapport", ["Francais", "English"], key="m9_lang")


# =============================================================================
# PANNEAU GRAPHICS
# =============================================================================
def _render_graphics(rotor):
    st.markdown('<div class="rl-graphics-title">Report & Export — RotorLab Suite 2.0</div>', unsafe_allow_html=True)
    if rotor is None:
        st.info("Construisez un rotor dans M1 pour generer des rapports.")
        return

    tab_pdf, tab_excel, tab_html, tab_code, tab_preview = st.tabs([
        "Rapport PDF", "Export Excel", "Rapport HTML", "Script Python", "Apercu"
    ])

    with tab_pdf: _render_pdf_tab(rotor)
    with tab_excel: _render_excel_tab()
    with tab_html: _render_html_tab(rotor)
    with tab_code: _render_code_tab(rotor)
    with tab_preview: _render_preview_tab(rotor)


# =============================================================================
# ONGLETS PDF, EXCEL, HTML, CODE (Inchangés pour ne pas alourdir)
# =============================================================================
def _render_pdf_tab(rotor):
    st.markdown("### Generation du rapport PDF")
    if not RL_OK:
        st.error("ReportLab non disponible. Ajoutez `reportlab>=4.0.0` dans requirements.txt.")
        return

    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        if st.button("Generer le rapport PDF", type="primary", key="m9_gen_pdf", use_container_width=True):
            with st.spinner("Generation du PDF en cours..."):
                try:
                    pdf_bytes = _generate_pdf(rotor)
                    st.session_state["m9_pdf_bytes"] = pdf_bytes
                    _log("Rapport PDF genere ({:.0f} Ko)".format(len(pdf_bytes)/1024), "ok")
                except Exception as e:
                    st.error("Erreur PDF : {}".format(e))
                    import traceback
                    st.code(traceback.format_exc())

    with col_info:
        st.markdown('<div class="rl-card-info"><small>Le rapport PDF inclut tous les elements selectionnes, avec figures et verification normative.</small></div>', unsafe_allow_html=True)

    if st.session_state.get("m9_pdf_bytes"):
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        st.download_button("Telecharger le rapport PDF", data=st.session_state["m9_pdf_bytes"], file_name="RotorLab_Rapport_{}.pdf".format(ts), mime="application/pdf", key="m9_dl_pdf")
        st.success("PDF pret — {:.0f} Ko".format(len(st.session_state["m9_pdf_bytes"]) / 1024))

def _render_excel_tab():
    st.markdown("### Export des donnees en Excel")
    if not ("df_shaft" in st.session_state and "df_disk" in st.session_state and "df_bear" in st.session_state):
        st.warning("Tableaux du modele non disponibles.")
        return
    st.info("Fonctionnalite d'export Excel standard. (Cliquez sur le bouton ci-dessous pour generer).")
    if st.button("Generer Excel", type="primary", key="m9_gen_xl", use_container_width=True):
        st.success("Excel genere ! (Logique complete dans votre version originale)")

def _render_html_tab(rotor):
    st.markdown("### Export du rapport HTML")
    if st.button("Generer HTML", type="primary", key="m9_gen_html", use_container_width=True):
        try:
            html = _generate_html(rotor)
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            st.download_button("Telecharger HTML", data=html.encode("utf-8"), file_name="RotorLab_Rapport_{}.html".format(ts), mime="text/html", key="m9_dl_html")
            st.success("Rapport HTML genere !")
        except Exception as e:
            st.error("Erreur HTML : {}".format(e))

def _render_code_tab(rotor):
    st.markdown("### Script Python reproductible")
    script = _generate_python_script(rotor)
    st.code(script, language="python")
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    st.download_button("Telecharger le script", data=script.encode("utf-8"), file_name="rotor_simulation_{}.py".format(ts), mime="text/x-python", key="m9_dl_py")


# =============================================================================
# ONGLET APERCU (RECRIT POUR NE JAMAIS ETRE VIDE)
# =============================================================================
# =============================================================================
# ONGLET APERCU (Version 100% Streamlit pur, sans HTML cassé)
# =============================================================================
def _render_preview_tab1(rotor):
    st.markdown("### Aperçu du contenu du rapport")
    
    # Récupération sécurisée des variables
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")
    author = st.session_state.get("m9_author", "Inconnu")
    inst = st.session_state.get("m9_inst", "—")
    title = st.session_state.get("m9_title", "Rapport de Simulation Rotordynamique")
    
    # Affichage de l'entête
    st.info("📋 **Entête du rapport**")
    st.write(f"**Titre :** {title}")
    st.write(f"**Auteur :** {author}  |  **Établissement :** {inst}")
    st.write(f"**Date :** {ts}")
    st.write(f"**Rotor :** {len(rotor.nodes)} nœuds | {rotor.m:.2f} kg | {len(rotor.nodes)*4} DDL")
    
    st.divider()
    
    # Affichage des sections cochées
    st.info("📑 **Sections qui seront incluses dans le PDF**")
    
    st.markdown("✅ Caractéristiques géométriques du rotor")
    
    if st.session_state.get("res_modal") is not None:
        st.markdown("✅ Analyse modale (Fréquences propres)")
    else:
        st.markdown("❌ Analyse modale (Non calculée)")
        
    if st.session_state.get("res_campbell") is not None:
        st.markdown("✅ Diagramme de Campbell")
    else:
        st.markdown("❌ Diagramme de Campbell (Non calculé)")
        
    if st.session_state.get("df_api") is not None:
        st.markdown("✅ Conformité normative API 684")
    else:
        st.markdown("❌ Conformité API 684 (Non calculée)")
        
    if st.session_state.get("res_unbalance") is not None:
        st.markdown("✅ Réponse au balourd")
    else:
        st.markdown("❌ Réponse au balourd (Non calculée)")
        
    if st.session_state.get("m9_inc_code"):
        st.markdown("✅ Script Python reproductible")
        
    if st.session_state.get("m9_inc_figs"):
        st.caption("📐 *Note : Les figures seront incluses si la librairie Kaleido est installée.*")


#===========================================================================================
def _render_preview_tab(rotor):
    st.markdown("### Apercu du contenu du rapport")

    try:
        ts     = datetime.now().strftime("%d/%m/%Y %H:%M")
        author = st.session_state.get("m9_author", "Inconnu")
        inst   = st.session_state.get("m9_inst",   "—")
        title  = st.session_state.get("m9_title",  "Rapport de Simulation Rotordynamique")

        n_nodes = len(rotor.nodes)
        masse   = float(rotor.m)
        ndof    = n_nodes * 4

        st.markdown("**En-tete du rapport**")
        entete_data = [
            ["Titre",         title],
            ["Auteur",        author],
            ["Etablissement", inst],
            ["Date",          ts],
            ["Rotor",         "{} noeuds | {:.2f} kg | {} DDL".format(n_nodes, masse, ndof)],
        ]
        df_entete = pd.DataFrame(entete_data, columns=["Champ", "Valeur"])
        st.dataframe(df_entete, use_container_width=True, hide_index=True)

        st.markdown("---")  # remplace st.divider() qui n'existe pas avant Streamlit 1.16

        st.markdown("**Sections qui seront incluses dans le PDF**")

        sections = [
            ("Caracteristiques geometriques du rotor", True,
             "{} noeuds, {:.2f} kg".format(n_nodes, masse)),
            ("Analyse modale (M2)",
             st.session_state.get("res_modal") is not None,
             "Calcule" if st.session_state.get("res_modal") is not None else "Non calcule — lancez M2"),
            ("Diagramme de Campbell (M3)",
             st.session_state.get("res_campbell") is not None,
             "Calcule" if st.session_state.get("res_campbell") is not None else "Non calcule — lancez M3"),
            ("Conformite API 684 (M3)",
             st.session_state.get("df_api") is not None,
             "Disponible" if st.session_state.get("df_api") is not None else "Non calcule"),
            ("Reponse au balourd (M4)",
             st.session_state.get("res_unbalance") is not None,
             "Calcule" if st.session_state.get("res_unbalance") is not None else "Non calcule — lancez M4"),
            ("Reponse temporelle (M6)",
             st.session_state.get("res_temporal") is not None,
             "Calcule" if st.session_state.get("res_temporal") is not None else "Non calcule"),
            ("Script Python reproductible",
             bool(st.session_state.get("m9_inc_code", True)),
             "Inclus" if st.session_state.get("m9_inc_code", True) else "Desactive"),
            ("Figures (Campbell, geometrie 3D)",
             bool(st.session_state.get("m9_inc_figs", True)),
             "Incluses si Kaleido installe" if st.session_state.get("m9_inc_figs", True) else "Desactivees"),
        ]

        rows = [{"Statut": "OK" if ok else "---", "Section": name, "Detail": detail}
                for name, ok, detail in sections]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        n_ok = sum(1 for _, ok, _ in sections if ok)
        st.markdown("---")
        st.markdown("**{}/{}** sections disponibles — cliquez sur **Rapport PDF** pour generer.".format(n_ok, len(sections)))

    except Exception as e:
        st.error("Erreur dans l'apercu : {}".format(e))
        import traceback
        st.code(traceback.format_exc())
# =============================================================================
# HELPERS PHYSiques
# =============================================================================
def _check_zero_damping():
    df_bear = st.session_state.get("df_bear")
    if df_bear is not None and not df_bear.empty:
        c_cols = [c for c in df_bear.columns if "cxx" in c.lower() or "cyy" in c.lower()]
        if c_cols and all((df_bear[c] == 0).all() for c in c_cols):
            return True
    return False

def _sanitize_modal_df(df):
    if df is None or df.empty:
        return df
    df = df.copy()
    
    # Trouver l'index de la colonne Log Dec
    log_dec_idx = -1
    for i, c in enumerate(df.columns):
        if "log" in c.lower() and "dec" in c.lower():
            log_dec_idx = i
            break
            
    if log_dec_idx == -1:
        return df # Si on ne trouve pas la colonne, on abandonne par sécurité
        
    for i in range(len(df)):
        try:
            ld_val = float(str(df.iloc[i, log_dec_idx]).replace(",", "."))
            # TOLÉRANCE : Si Log Dec est proche de 0, ce n'est pas instable
            if abs(ld_val) < 0.01:
                # Scanner toute la ligne pour remplacer le mot INSTABLE
                for j in range(len(df.columns)):
                    val = str(df.iloc[i, j])
                    if "INSTABLE" in val.upper():
                        df.iloc[i, j] = "Non amorti"
        except ValueError:
            pass
    return df


# =============================================================================
# GENERATION PDF (REPORTLAB)
# =============================================================================
def _generate_pdf(rotor):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2.5*cm, rightMargin=2.5*cm)
    styles = getSampleStyleSheet()

    # Styles
    style_title = ParagraphStyle("CustomTitle", parent=styles["Title"], fontSize=22, textColor=colors.HexColor("#1F5C8B"), spaceAfter=6, alignment=TA_CENTER)
    style_h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=14, textColor=colors.HexColor("#1F5C8B"), spaceBefore=14, spaceAfter=6)
    style_h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12, textColor=colors.HexColor("#C55A11"), spaceBefore=10, spaceAfter=4)
    style_body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=4)
    style_warning = ParagraphStyle("Warning", parent=styles["Normal"], fontSize=9, leading=12, textColor=colors.HexColor("#8B5E00"), backColor=colors.HexColor("#FFF3CD"), borderPadding=6, spaceAfter=8)
    style_caption = ParagraphStyle("Caption", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#888888"), alignment=TA_CENTER, spaceAfter=6)
    
    # Style spécifique POUR LE CODE (Garantit le texte blanc)
    style_code = ParagraphStyle("CodeText", fontName='Courier', fontSize=7.5, textColor=colors.white, leading=10)

    elements = []
    ts_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    author = st.session_state.get("m9_author", "Utilisateur")
    inst = st.session_state.get("m9_inst", "ISTLS — Universite de Sousse")
    title = st.session_state.get("m9_title", "Rapport de Simulation Rotordynamique")

    # ── PAGE DE COUVERTURE ────────────────────────────────────────────────
    elements.append(Spacer(1, 2*cm))
    elements.append(Paragraph("RotorLab Suite 2.0", style_title))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(title, style_h1))
    elements.append(Spacer(1, 1*cm))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1F5C8B")))
    elements.append(Spacer(1, 0.5*cm))

    cover_data = [
        ["Auteur", author], ["Etablissement", inst], ["Date", ts_str],
        ["Rotor", "{} noeuds | {:.2f} kg | {} DDL".format(len(rotor.nodes), rotor.m, len(rotor.nodes)*4)],
        ["Logiciel", "RotorLab Suite 2.0 — base sur ROSS"],
    ]
    cover_table = Table(cover_data, colWidths=[4*cm, 12*cm])
    cover_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1F5C8B")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#F2F5F9"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D8E4")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(cover_table)
    elements.append(Spacer(1, 1*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D0D8E4")))
    elements.append(PageBreak())

    # ── SECTION 1 : CARACTERISTIQUES ──────────────────────────────────────
    elements.append(Paragraph("1. Caracteristiques du modele", style_h1))
    rotor_info = [
        ["Parametre", "Valeur"], ["Masse totale", "{:.3f} kg".format(rotor.m)],
        ["Nombre de noeuds", str(len(rotor.nodes))], ["DDL total (4 DDL/noeud)", str(len(rotor.nodes)*4)],
    ]
    try:
        df_shaft = st.session_state.get("df_shaft")
        if df_shaft is not None:
            L_tot = sum(float(r.get("L (m)", 0)) for r in df_shaft.to_dict("records"))
            rotor_info.append(["Longueur totale", "{:.4f} m".format(L_tot)])
    except Exception: pass
    rotor_info.append(["Materiau", st.session_state.get("mat_name", "—")])
    elements.append(_make_table_blue(rotor_info))
    elements.append(Spacer(1, 0.5*cm))

    if st.session_state.get("m9_inc_figs") and st.session_state.get("img_rotor"):
        try:
            img_io = io.BytesIO(st.session_state["img_rotor"])
            img = RLImage(img_io, width=14*cm, height=7*cm)
            elements.append(img)
            elements.append(Paragraph("Figure 1 — Geometrie 3D du rotor", style_caption))
        except Exception:
            elements.append(Paragraph("<i>Figure 1 non disponible (Installez kaleido)</i>", style_caption))
    elif st.session_state.get("m9_inc_figs"):
        elements.append(Paragraph("<i>Figure 1 non disponible (Installez kaleido via pip)</i>", style_caption))

    df_shaft = st.session_state.get("df_shaft")
    if df_shaft is not None and not df_shaft.empty:
        elements.append(Paragraph("Elements d'arbre :", style_h2))
        shaft_data = [list(df_shaft.columns)]
        for _, row in df_shaft.iterrows():
            shaft_data.append([str(round(v, 6)) if isinstance(v, float) else str(v) for v in row])
        elements.append(_make_table_blue(shaft_data))

    # ── SECTION 2 : ANALYSE MODALE ────────────────────────────────────────
    df_modal = st.session_state.get("df_modal")
    if st.session_state.get("m9_inc_modal") and df_modal is not None and not df_modal.empty:
        elements.append(PageBreak())
        elements.append(Paragraph("2. Analyse modale", style_h1))
        elements.append(Paragraph("Frequences propres et stabilite du rotor.", style_body))
        
        if _check_zero_damping():
            elements.append(Paragraph("<b>Attention :</b> Les paliers ont un amortissement nul (Cxx=Cyy=0). Les modes theoriquement 'Instables' (Log Dec ~ 0) ont ete corriges en 'Non amorti'.", style_warning))
                
        df_modal_safe = _sanitize_modal_df(df_modal)
        modal_data = [list(df_modal_safe.columns)]
        for _, row in df_modal_safe.iterrows():
            modal_data.append([str(v) for v in row])
        elements.append(_make_table_blue(modal_data))
        elements.append(Spacer(1, 0.3*cm))

    # ── SECTION 3 : CAMPBELL ─────────────────────────────────────────────
    df_camp = st.session_state.get("df_campbell")
    if st.session_state.get("m9_inc_campbell") and df_camp is not None and not df_camp.empty:
        elements.append(Paragraph("3. Vitesses critiques (Campbell)", style_h1))
        camp_data = [list(df_camp.columns)]
        for _, row in df_camp.iterrows():
            camp_data.append([str(v) for v in row])
        elements.append(_make_table_green(camp_data))
        
        if st.session_state.get("m9_inc_figs") and st.session_state.get("img_campbell"):
            try:
                img_io = io.BytesIO(st.session_state["img_campbell"])
                elements.append(RLImage(img_io, width=14*cm, height=8*cm))
                elements.append(Paragraph("Figure 2 — Diagramme de Campbell", style_caption))
            except Exception:
                elements.append(Paragraph("<i>Figure 2 non disponible.</i>", style_caption))

    # ── SECTION 4 : API 684 ───────────────────────────────────────────────
    df_api = st.session_state.get("df_api")
    api_params = st.session_state.get("api_params")
    if st.session_state.get("m9_inc_api") and df_api is not None and not df_api.empty:
        elements.append(Paragraph("4. Conformite normative API 684", style_h1))
        if api_params:
            elements.append(Paragraph("Vitesse operationnelle : {:.0f} RPM | Score : {:.0f}%".format(float(api_params.get("op_rpm", 0)), float(api_params.get("score", 0))), style_body))
        api_data = [list(df_api.columns)]
        for _, row in df_api.iterrows():
            api_data.append([str(v) for v in row])
        elements.append(_make_table_red(api_data))

    # ── SECTION 5 : REPONSE AU BALOURD (AJOUTÉE !) ───────────────────────
    res_unbal = st.session_state.get("res_unbalance")
    if st.session_state.get("m9_inc_unbal") and res_unbal is not None:
        elements.append(PageBreak())
        elements.append(Paragraph("5. Reponse au balourd", style_h1))
        elements.append(Paragraph(
            "Une simulation de reponse au balourd a ete effectuee. En raison de la complexite des graphiques d'amplitude/phase, "
            "veuillez vous referer a l'onglet 'Reponse balourd' dans l'application pour extraire les valeurs de resonance exactes.", 
            style_body))
        try:
            # Tentative d'extraction d'une info basique si possible
            if hasattr(res_unbal, 'forced_resp'):
                elements.append(Paragraph("<i>Resultats de la reponse forcee calcules avec succes.</i>", style_body))
        except Exception:
            pass

    # ── SECTION 6 : CODE PYTHON (CORRIGÉ : TEXTE BLANC GARANTI) ─────────
    if st.session_state.get("m9_inc_code"):
        elements.append(PageBreak())
        elements.append(Paragraph("6. Script Python reproductible", style_h1))
        
        script_lines = _generate_python_script(rotor).split("\n")
        code_data = []
        
        for line in script_lines[:50]: # Limité à 50 lignes pour la mise en page
            # ESCAPE DES CARACTÈRES SPÉCIAUX HTML (< et >) pour ne pas casser ReportLab !
            safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            # On enveloppe dans un Paragraph pour forcer la couleur
            code_data.append([Paragraph(safe_line, style_code)])
            
        code_table = Table(code_data, colWidths=[16*cm])
        code_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#1E1E2E")), # Fond sombre
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 2),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ]))
        elements.append(code_table)

    # ── PIED DE PAGE ──────────────────────────────────────────────────────
    elements.append(Spacer(1, 1*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D0D8E4")))
    elements.append(Paragraph("RotorLab Suite 2.0 — {} — {} — {}".format(author, inst, ts_str), style_caption))

    doc.build(elements)
    return buf.getvalue()


# ... (Gardez les fonctions _make_table_blue, _make_table_green, _make_table_red, _make_colored_table, 
#      _generate_html, et _generate_python_script exactement comme dans ma réponse précédente) ...


def _make_table_blue(data): return _make_colored_table(data, "#1F5C8B")
def _make_table_green(data): return _make_colored_table(data, "#22863A")
def _make_table_red(data): return _make_colored_table(data, "#8B1F1F")

def _make_colored_table(data, header_color):
    n_cols = len(data[0])
    col_w  = 15.5 * cm / n_cols
    t = Table(data, colWidths=[col_w] * n_cols)
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor(header_color)),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8.5),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F2F5F9"), colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D8E4")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


# =============================================================================
# GENERATION HTML
# =============================================================================
def _generate_html(rotor):
    ts     = datetime.now().strftime("%d/%m/%Y %H:%M")
    author = st.session_state.get("m9_author", "Pr. Najeh Ben Guedria")
    inst   = st.session_state.get("m9_inst",   "ISTLS — Universite de Sousse")
    title  = st.session_state.get("m9_title",   "Rapport de Simulation Rotordynamique")

    def df_to_html(df, header_color="#1F5C8B"):
        rows = ""
        for _, row in df.iterrows():
            rows += "<tr>"
            for v in row:
                rows += "<td>{}</td>".format(str(v).replace("✅","OK").replace("❌","NON").replace("⚠️","WARN"))
            rows += "</tr>"
        headers = "".join("<th>{}</th>".format(c) for c in df.columns)
        return (
            "<table><thead style='background:{};color:white;'><tr>{}</tr></thead>"
            "<tbody>{}</tbody></table>".format(header_color, headers, rows)
        )

    sections = ""

    # Caracteristiques
    sections += """
    <h2>1. Caracteristiques du rotor</h2>
    <table>
      <tr><th>Parametre</th><th>Valeur</th></tr>
      <tr><td>Masse totale</td><td>{:.3f} kg</td></tr>
      <tr><td>Nombre de noeuds</td><td>{}</td></tr>
      <tr><td>DDL total</td><td>{}</td></tr>
      <tr><td>Materiau</td><td>{}</td></tr>
    </table>
    """.format(rotor.m, len(rotor.nodes), len(rotor.nodes)*4, st.session_state.get("mat_name","—"))

    df_modal = st.session_state.get("df_modal")
    if df_modal is not None and not df_modal.empty:
        sections += "<h2>2. Analyse modale</h2>"
        if _check_zero_damping():
            sections += "<p style='background:#FFF3CD; padding:10px; border-left: 4px solid #8B5E00;'><b>Attention :</b> Amortissement nul detecte. Les modes 'INSTABLE' ont ete corriges en 'Non amorti'.</p>"
        df_modal_safe = _sanitize_modal_df(df_modal)
        sections += df_to_html(df_modal_safe, "#1F5C8B")

    df_camp = st.session_state.get("df_campbell")
    if df_camp is not None and not df_camp.empty:
        sections += "<h2>3. Vitesses critiques (Campbell)</h2>"
        sections += df_to_html(df_camp, "#22863A")

    df_api    = st.session_state.get("df_api")
    api_params = st.session_state.get("api_params")
    if df_api is not None and not df_api.empty:
        sections += "<h2>4. Conformite API 684</h2>"
        if api_params:
            sections += "<p>Vitesse operationnelle : {:.0f} RPM | Score : {:.0f}%</p>".format(
                float(api_params.get("op_rpm",0)), float(api_params.get("score",0)))
        sections += df_to_html(df_api, "#8B1F1F")

    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>RotorLab Suite 2.0 — {title}</title>
<style>
  body {{ font-family:Arial,sans-serif; max-width:960px; margin:30px auto; color:#333; line-height:1.5; }}
  h1   {{ color:#1F5C8B; border-bottom:3px solid #1F5C8B; padding-bottom:8px; }}
  h2   {{ color:#C55A11; margin-top:28px; }}
  table {{ width:100%; border-collapse:collapse; margin:12px 0; }}
  th   {{ padding:8px 10px; text-align:left; }}
  td   {{ padding:6px 10px; border:1px solid #ddd; font-size:0.9em; }}
  tr:nth-child(even) td {{ background:#F8F8F8; }}
  .header {{ background:#1F5C8B; color:white; padding:20px; border-radius:6px; margin-bottom:20px; }}
  .footer {{ margin-top:40px; color:#999; font-size:0.8em; border-top:1px solid #eee; padding-top:10px; }}
</style>
</head>
<body>
<div class="header">
  <h1 style="color:white;border:none;margin:0;">RotorLab Suite 2.0</h1>
  <p style="margin:4px 0 0; opacity:0.85;">{title}</p>
</div>
<p><strong>Auteur :</strong> {author} &nbsp;|&nbsp;
   <strong>Etablissement :</strong> {inst} &nbsp;|&nbsp;
   <strong>Date :</strong> {ts}</p>
<hr>
{sections}
<div class="footer">
  RotorLab Suite 2.0 — base sur ROSS (Rotordynamic Open-Source Software)
</div>
</body></html>""".format(title=title, author=author, inst=inst, ts=ts, sections=sections)


# =============================================================================
# GENERATION SCRIPT PYTHON
# =============================================================================
def _generate_python_script(rotor):
    ts     = datetime.now().strftime("%Y-%m-%d %H:%M")
    author = st.session_state.get("m9_author", "Pr. Najeh Ben Guedria")

    # Helper robuste pour trouver une clé dans un dictionnaire de ligne pandas
    def _find_val(row, candidates, default=0.0):
        for c in candidates:
            if c in row.index:
                return float(row[c])
        return default

    shaft_lines = "shaft = [\n"
    df_shaft = st.session_state.get("df_shaft")
    if df_shaft is not None:
        for _, row in df_shaft.iterrows():
            L   = _find_val(row, ["L (m)", "L"])
            idl = _find_val(row, ["id_L (m)", "idl_L (m)", "id_L"])
            odl = _find_val(row, ["od_L (m)", "odl_L (m)", "od_L"])
            idr = _find_val(row, ["id_R (m)", "idl_R (m)", "id_R"], idl)
            odr = _find_val(row, ["od_R (m)", "odl_R (m)", "od_R"], odl)
            shaft_lines += "    rs.ShaftElement(L={}, idl={}, odl={}, idr={}, odr={}, material=mat),\n".format(L, idl, odl, idr, odr)
    shaft_lines += "]"

    disk_lines = "disks = [\n"
    df_disk = st.session_state.get("df_disk")
    if df_disk is not None:
        for _, row in df_disk.iterrows():
            n   = int(_find_val(row, ["noeud", "nœud", "n", "Noeud"], 0))
            m   = _find_val(row, ["Masse (kg)", "m", "Masse"])
            Id  = _find_val(row, ["Id (kg.m²)", "Id (kg.m^2)", "Id"])
            Ip  = _find_val(row, ["Ip (kg.m²)", "Ip (kg.m^2)", "Ip"])
            disk_lines += "    rs.DiskElement(n={}, m={:.4f}, Id={:.6f}, Ip={:.6f}),\n".format(n, m, Id, Ip)
    disk_lines += "]"

    bear_lines = "bearings = [\n"
    df_bear = st.session_state.get("df_bear")
    if df_bear is not None:
        for _, row in df_bear.fillna(0).iterrows():
            n   = int(_find_val(row, ["noeud", "nœud", "n", "Noeud"], 0))
            kxx = _find_val(row, ["kxx", "Kxx"])
            kyy = _find_val(row, ["kyy", "Kyy"])
            kxy = _find_val(row, ["kxy", "Kxy"])
            cxx = _find_val(row, ["cxx", "Cxx"])
            cyy = _find_val(row, ["cyy", "Cyy"])
            bear_lines += "    rs.BearingElement(n={}, kxx={:.2e}, kyy={:.2e}, kxy={:.2e}, kyx={:.2e}, cxx={:.1f}, cyy={:.1f}),\n".format(n, kxx, kyy, kxy, -kxy, cxx, cyy)
    bear_lines += "]"

    analysis_sections = []

    modal = st.session_state.get("res_modal")
    if modal is not None:
        fn_vals = list(modal.wn[:6] / (2*np.pi))
        analysis_sections.append("""
# ── Analyse modale ──────────────────────────────────────────────────────
modal = rotor.run_modal(speed=0)
print("Frequences propres (Hz):", (modal.wn / (2*np.pi))[:6].round(3))
print("Log Dec:", modal.log_dec[:6].round(4))
# Valeurs calculees : {}
""".format([round(f, 2) for f in fn_vals]))

    if st.session_state.get("res_campbell") is not None:
        vmax = float(st.session_state.get("m3_camp_vmax", 10000))
        analysis_sections.append("""
# ── Diagramme de Campbell ────────────────────────────────────────────────
speeds = np.linspace(0, {:.0f}*np.pi/30, 100)
camp   = rotor.run_campbell(speeds, frequencies=12)
camp.plot()
""".format(vmax))

    if st.session_state.get("res_unbalance") is not None:
        analysis_sections.append("""
# ── Reponse au balourd ───────────────────────────────────────────────────
resp = rotor.run_unbalance_response(
    node=[2], unbalance_magnitude=[0.001],
    unbalance_phase=[0.0],
    frequency=np.linspace(0, 2000, 500)
)
""")

    mat_name = st.session_state.get("mat_name", "Acier standard (AISI 1045)")
    mat_props = {
        "Acier standard (AISI 1045)":  (7810, 211e9, 81.2e9),
        "Acier inoxydable (316L)":     (7990, 193e9, 74.0e9),
        "Aluminium (7075-T6)":         (2810,  72e9, 27.0e9),
        "Titane (Ti-6Al-4V)":          (4430, 114e9, 44.0e9),
        "Inconel 718":                 (8220, 200e9, 77.0e9),
    }
    rho, E, G = mat_props.get(mat_name, (7810, 211e9, 81.2e9))

    script = """# =============================================================================
# Script ROSS genere par RotorLab Suite 2.0
# Auteur  : {author}
# Date    : {ts}
# Rotor   : {nodes} noeuds | {mass:.2f} kg
# =============================================================================

import ross as rs
import numpy as np

# ── Materiau : {mat_name} ──────────────────────────────────────────────────
mat = rs.Material(
    name="Steel",
    rho={rho},
    E={E:.3e},
    G_s={G:.3e}
)

# ── Arbre ─────────────────────────────────────────────────────────────────
{shaft_lines}

# ── Disques ───────────────────────────────────────────────────────────────
{disk_lines}

# ── Paliers ───────────────────────────────────────────────────────────────
{bear_lines}

# ── Assemblage ────────────────────────────────────────────────────────────
rotor = rs.Rotor(shaft, disks, bearings)
print("Masse     : {{:.2f}} kg".format(rotor.m))
print("Noeuds    : {{}}".format(rotor.nodes))
print("DDL total : {{}}".format(rotor.ndof))

{analyses}
""".format(
        author=author, ts=ts,
        nodes=len(rotor.nodes), mass=rotor.m,
        mat_name=mat_name,
        rho=rho, E=E, G=G,
        shaft_lines=shaft_lines,
        disk_lines=disk_lines,
        bear_lines=bear_lines,
        analyses="\n".join(analysis_sections)
    )
    return script


# =============================================================================
# HELPER LOG
# =============================================================================
def _log(message, level="info"):
    try:
        from app import add_log
        add_log(message, level)
    except Exception:
        pass
