# modules/m9_report.py — Rapport PDF & Export
# RotorLab Suite 2.0 — Pr. Najeh Ben Guedria
# Couvre : PDF ReportLab, Excel, HTML, Script Python reproductible
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

    # ── Informations du rapport ───────────────────────────────────────────
    st.markdown(
        '<div class="rl-section-header">Informations du rapport</div>',
        unsafe_allow_html=True)

    st.text_input("Titre du rapport",
                  value="Rapport de Simulation Rotordynamique",
                  key="m9_title")
    st.text_input("Auteur",
                  value=st.session_state.get("user_name", "Pr. Najeh Ben Guedria"),
                  key="m9_author")
    st.text_input("Etablissement",
                  value="ISTLS — Universite de Sousse",
                  key="m9_inst")
    st.text_input("Reference projet",
                  value="RotorLab Suite 2.0",
                  key="m9_ref")

    # ── Contenu a inclure ─────────────────────────────────────────────────
    st.markdown(
        '<div class="rl-section-header">Contenu du rapport</div>',
        unsafe_allow_html=True)

    # Detection automatique des modules calcules
    has_modal    = st.session_state.get("res_modal")    is not None
    has_campbell = st.session_state.get("res_campbell") is not None
    has_api      = st.session_state.get("df_api")       is not None
    has_unbal    = st.session_state.get("res_unbalance") is not None
    has_temporal = st.session_state.get("res_temporal") is not None

    st.checkbox("Caracteristiques du rotor",
                value=True, disabled=True,
                key="m9_inc_rotor")
    st.checkbox("Analyse modale (M2)",
                value=has_modal, disabled=not has_modal,
                key="m9_inc_modal")
    st.checkbox("Campbell + Vitesses critiques (M3)",
                value=has_campbell, disabled=not has_campbell,
                key="m9_inc_campbell")
    st.checkbox("Conformite API 684 (M3)",
                value=has_api, disabled=not has_api,
                key="m9_inc_api")
    st.checkbox("Reponse au balourd (M4)",
                value=has_unbal, disabled=not has_unbal,
                key="m9_inc_unbal")
    st.checkbox("Reponse temporelle (M6)",
                value=has_temporal, disabled=not has_temporal,
                key="m9_inc_temporal")

    st.info(
        "Les modules grises necessitent d'avoir "
        "lance les calculs correspondants."
    )

    st.markdown(
        '<div class="rl-section-header">Options d export</div>',
        unsafe_allow_html=True)

    st.checkbox("Inclure les figures (Campbell, rotor 3D)",
                value=True, key="m9_inc_figs")
    st.checkbox("Inclure le code Python reproductible",
                value=True, key="m9_inc_code")
    st.selectbox("Langue du rapport",
                 ["Francais", "English"],
                 key="m9_lang")


# =============================================================================
# PANNEAU GRAPHICS
# =============================================================================
def _render_graphics(rotor):
    st.markdown(
        '<div class="rl-graphics-title">Report & Export — RotorLab Suite 2.0</div>',
        unsafe_allow_html=True)

    if rotor is None:
        st.info("Construisez un rotor dans M1 pour generer des rapports.")
        return

    tab_pdf, tab_excel, tab_html, tab_code, tab_preview = st.tabs([
        "Rapport PDF",
        "Export Excel",
        "Rapport HTML",
        "Script Python",
        "Apercu"
    ])

    with tab_pdf:
        _render_pdf_tab(rotor)

    with tab_excel:
        _render_excel_tab()

    with tab_html:
        _render_html_tab(rotor)

    with tab_code:
        _render_code_tab(rotor)

    with tab_preview:
        _render_preview_tab(rotor)


# =============================================================================
# ONGLET PDF
# =============================================================================
def _render_pdf_tab(rotor):
    st.markdown("### Generation du rapport PDF")

    if not RL_OK:
        st.error(
            "ReportLab non disponible. "
            "Ajoutez `reportlab>=4.0.0` dans requirements.txt."
        )
        return

    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        if st.button("Generer le rapport PDF",
                     type="primary",
                     key="m9_gen_pdf",
                     use_container_width=True):
            with st.spinner("Generation du PDF en cours..."):
                try:
                    pdf_bytes = _generate_pdf(rotor)
                    st.session_state["m9_pdf_bytes"] = pdf_bytes
                    _log("Rapport PDF genere ({:.0f} Ko)".format(
                        len(pdf_bytes)/1024), "ok")
                except Exception as e:
                    st.error("Erreur PDF : {}".format(e))
                    import traceback
                    st.code(traceback.format_exc())

    with col_info:
        st.markdown("""
        <div class="rl-card-info">
          <small>Le rapport PDF inclut :<br>
          Page de couverture, caracteristiques du rotor,
          tableaux de resultats codes par couleur,
          figures Plotly (si Kaleido disponible),
          et verification normative API 684 / ISO 1940.</small>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.get("m9_pdf_bytes"):
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        st.download_button(
            "Telecharger le rapport PDF",
            data=st.session_state["m9_pdf_bytes"],
            file_name="RotorLab_Rapport_{}.pdf".format(ts),
            mime="application/pdf",
            key="m9_dl_pdf"
        )
        st.success("PDF pret — {:.0f} Ko".format(
            len(st.session_state["m9_pdf_bytes"]) / 1024))


# =============================================================================
# ONGLET EXCEL
# =============================================================================
def _render_excel_tab():
    st.markdown("### Export des donnees en Excel")

    has_shaft = "df_shaft" in st.session_state
    has_disk  = "df_disk"  in st.session_state
    has_bear  = "df_bear"  in st.session_state

    if not (has_shaft and has_disk and has_bear):
        st.warning("Tableaux du modele non disponibles. "
                   "Ouvrez M1 pour les initialiser.")
        return

    col1, col2 = st.columns(2)
    with col1:
        inc_model = st.checkbox("Parametres du modele (Arbre/Disques/Paliers)",
                                value=True, key="m9_xl_model")
        inc_modal = st.checkbox("Resultats modaux",
                                value=st.session_state.get("df_modal") is not None,
                                key="m9_xl_modal")
    with col2:
        inc_camp  = st.checkbox("Vitesses critiques (Campbell)",
                                value=st.session_state.get("df_campbell") is not None,
                                key="m9_xl_camp")
        inc_api   = st.checkbox("Conformite API 684",
                                value=st.session_state.get("df_api") is not None,
                                key="m9_xl_api")

    if st.button("Generer le fichier Excel",
                 type="primary", key="m9_gen_xl",
                 use_container_width=True):
        try:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
                wb = writer.book

                # Formats
                fmt_header = wb.add_format({
                    "bold": True, "font_color": "white",
                    "bg_color": "#1F5C8B", "border": 1,
                    "align": "center"
                })
                fmt_green_header = wb.add_format({
                    "bold": True, "font_color": "white",
                    "bg_color": "#22863A", "border": 1,
                    "align": "center"
                })
                fmt_red_header = wb.add_format({
                    "bold": True, "font_color": "white",
                    "bg_color": "#8B1F1F", "border": 1,
                    "align": "center"
                })
                fmt_alt = wb.add_format({
                    "bg_color": "#F2F5F9", "border": 1})
                fmt_normal = wb.add_format({"border": 1})

                def _write_df(df, sheet_name, header_fmt):
                    df.to_excel(writer, sheet_name=sheet_name,
                                index=False, startrow=1)
                    ws = writer.sheets[sheet_name]
                    for col_num, val in enumerate(df.columns):
                        ws.write(0, col_num, val, header_fmt)
                    for row_num in range(len(df)):
                        fmt = fmt_alt if row_num % 2 == 0 else fmt_normal
                        for col_num in range(len(df.columns)):
                            ws.write(row_num + 1, col_num,
                                     str(df.iloc[row_num, col_num]), fmt)
                    ws.set_column(0, len(df.columns)-1, 16)

                if inc_model:
                    _write_df(st.session_state["df_shaft"],
                              "Arbre", fmt_header)
                    _write_df(st.session_state["df_disk"],
                              "Disques", fmt_header)
                    _write_df(st.session_state["df_bear"],
                              "Paliers", fmt_header)

                if inc_modal and st.session_state.get("df_modal") is not None:
                    _write_df(st.session_state["df_modal"],
                              "Modal", fmt_header)

                if inc_camp and st.session_state.get("df_campbell") is not None:
                    _write_df(st.session_state["df_campbell"],
                              "Campbell", fmt_green_header)

                if inc_api and st.session_state.get("df_api") is not None:
                    _write_df(st.session_state["df_api"],
                              "API_684", fmt_red_header)

            ts = datetime.now().strftime("%Y%m%d_%H%M")
            st.download_button(
                "Telecharger le fichier Excel",
                data=buf.getvalue(),
                file_name="RotorLab_Data_{}.xlsx".format(ts),
                mime="application/vnd.openxmlformats-officedocument"
                     ".spreadsheetml.sheet",
                key="m9_dl_xl"
            )
            st.success("Excel genere avec succes !")
        except ModuleNotFoundError:
            st.error("xlsxwriter manquant. "
                     "Ajoutez `xlsxwriter>=3.0.0` dans requirements.txt.")
        except Exception as e:
            st.error("Erreur Excel : {}".format(e))


# =============================================================================
# ONGLET HTML
# =============================================================================
def _render_html_tab(rotor):
    st.markdown("### Export du rapport HTML")

    if st.button("Generer le rapport HTML",
                 type="primary", key="m9_gen_html",
                 use_container_width=True):
        try:
            html = _generate_html(rotor)
            ts   = datetime.now().strftime("%Y%m%d_%H%M")
            st.download_button(
                "Telecharger le rapport HTML",
                data=html.encode("utf-8"),
                file_name="RotorLab_Rapport_{}.html".format(ts),
                mime="text/html",
                key="m9_dl_html"
            )
            st.success("Rapport HTML genere !")
        except Exception as e:
            st.error("Erreur HTML : {}".format(e))

    st.markdown("""
    <div class="rl-card-info">
      <small>Le rapport HTML est autonome (pas de dependances externes),
      lisible dans tout navigateur web, et imprimable en PDF depuis
      le navigateur (Ctrl+P).</small>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# ONGLET CODE PYTHON
# =============================================================================
def _render_code_tab(rotor):
    st.markdown("### Script Python reproductible")
    st.markdown("""
    <div class="rl-card-info">
      <small>Ce script Python reconstruit exactement votre modele ROSS
      et relance toutes les analyses calculees durant la session.
      Il est independant de RotorLab Suite et s'execute directement
      avec Python + ROSS.</small>
    </div>
    """, unsafe_allow_html=True)

    script = _generate_python_script(rotor)
    st.code(script, language="python")

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    st.download_button(
        "Telecharger le script Python",
        data=script.encode("utf-8"),
        file_name="rotor_simulation_{}.py".format(ts),
        mime="text/x-python",
        key="m9_dl_py"
    )


# =============================================================================
# ONGLET APERCU
# =============================================================================
def _render_preview_tab(rotor):
    st.markdown("### Apercu du contenu du rapport")
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")

    st.markdown("""
    <div style="border:1px solid #D0D8E4; border-radius:8px;
    padding:20px; background:white; font-family:Arial, sans-serif;">

    <div style="background:#1F5C8B; color:white; padding:16px;
    border-radius:6px; margin-bottom:16px;">
      <h2 style="margin:0; font-size:1.4em;">RotorLab Suite 2.0</h2>
      <p style="margin:4px 0 0; opacity:0.85; font-size:0.9em;">
        Rapport de Simulation Rotordynamique
      </p>
    </div>

    <table style="width:100%; font-size:0.85em; margin-bottom:14px;">
      <tr>
        <td style="color:#888; width:140px;">Auteur</td>
        <td><strong>{author}</strong></td>
      </tr>
      <tr>
        <td style="color:#888;">Etablissement</td>
        <td>{inst}</td>
      </tr>
      <tr>
        <td style="color:#888;">Date</td>
        <td>{ts}</td>
      </tr>
      <tr>
        <td style="color:#888;">Rotor</td>
        <td>{nodes} noeuds | {mass:.2f} kg | {ndof} DDL</td>
      </tr>
    </table>

    <hr style="border:1px solid #EEE; margin:12px 0;">
    <p style="font-size:0.8em; color:#666;"><strong>Sections incluses :</strong></p>
    <ul style="font-size:0.82em; color:#444;">
      {sections}
    </ul>
    </div>
    """.format(
        author=st.session_state.get("m9_author",
                                     "Pr. Najeh Ben Guedria"),
        inst=st.session_state.get("m9_inst", "ISTLS — Universite de Sousse"),
        ts=ts,
        nodes=len(rotor.nodes),
        mass=rotor.m,
        ndof=len(rotor.nodes) * 4,
        sections=_get_sections_html()
    ), unsafe_allow_html=True)


def _get_sections_html():
    items = ["<li>Caracteristiques geometriques du rotor</li>"]
    if st.session_state.get("res_modal"):
        items.append("<li>Analyse modale — frequences propres et stabilite</li>")
    if st.session_state.get("res_campbell"):
        items.append("<li>Diagramme de Campbell — vitesses critiques</li>")
    if st.session_state.get("df_api"):
        items.append("<li>Conformite normative API 684</li>")
    if st.session_state.get("res_unbalance"):
        items.append("<li>Reponse au balourd — ISO 1940</li>")
    if st.session_state.get("res_temporal"):
        items.append("<li>Reponse temporelle — orbites et spectre</li>")
    if st.session_state.get("m9_inc_code"):
        items.append("<li>Script Python reproductible</li>")
    return "".join(items)


# =============================================================================
# GENERATION PDF (ReportLab)
# =============================================================================
def _generate_pdf(rotor):
    buf    = io.BytesIO()
    doc    = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=2*cm, bottomMargin=2*cm,
        leftMargin=2.5*cm, rightMargin=2.5*cm
    )
    styles = getSampleStyleSheet()

    # Styles personnalises
    style_title = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=22, textColor=colors.HexColor("#1F5C8B"),
        spaceAfter=6, alignment=TA_CENTER
    )
    style_h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"],
        fontSize=14, textColor=colors.HexColor("#1F5C8B"),
        spaceBefore=14, spaceAfter=6,
        borderPad=4, borderColor=colors.HexColor("#1F5C8B"),
        borderWidth=0, borderRadius=0,
        leftIndent=0
    )
    style_h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=12, textColor=colors.HexColor("#C55A11"),
        spaceBefore=10, spaceAfter=4
    )
    style_body = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, leading=14,
        alignment=TA_JUSTIFY, spaceAfter=4
    )
    style_caption = ParagraphStyle(
        "Caption", parent=styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#888888"),
        alignment=TA_CENTER, spaceAfter=6
    )

    elements = []
    ts_str   = datetime.now().strftime("%d/%m/%Y %H:%M")
    author   = st.session_state.get("m9_author", "Pr. Najeh Ben Guedria")
    inst     = st.session_state.get("m9_inst", "ISTLS — Universite de Sousse")
    title    = st.session_state.get("m9_title",
                                     "Rapport de Simulation Rotordynamique")

    # ── PAGE DE COUVERTURE ────────────────────────────────────────────────
    elements.append(Spacer(1, 2*cm))
    elements.append(Paragraph("RotorLab Suite 2.0", style_title))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(title, style_h1))
    elements.append(Spacer(1, 1*cm))
    elements.append(HRFlowable(
        width="100%", thickness=2,
        color=colors.HexColor("#1F5C8B")))
    elements.append(Spacer(1, 0.5*cm))

    # Tableau infos
    cover_data = [
        ["Auteur",       author],
        ["Etablissement",inst],
        ["Date",         ts_str],
        ["Rotor",        "{} noeuds | {:.2f} kg | {} DDL".format(
            len(rotor.nodes), rotor.m, len(rotor.nodes)*4)],
        ["Logiciel",     "RotorLab Suite 2.0 — base sur ROSS"],
    ]
    cover_table = Table(cover_data, colWidths=[4*cm, 12*cm])
    cover_table.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1F5C8B")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.HexColor("#F2F5F9"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D8E4")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    elements.append(cover_table)
    elements.append(Spacer(1, 1*cm))
    elements.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor("#D0D8E4")))
    elements.append(PageBreak())

    # ── SECTION 1 : CARACTERISTIQUES DU ROTOR ────────────────────────────
    elements.append(Paragraph("1. Caracteristiques du modele", style_h1))

    rotor_info = [
        ["Parametre", "Valeur"],
        ["Masse totale", "{:.3f} kg".format(rotor.m)],
        ["Nombre de noeuds", str(len(rotor.nodes))],
        ["DDL total (4 DDL/noeud)", str(len(rotor.nodes)*4)],
    ]
    # Longueur totale
    try:
        df_shaft = st.session_state.get("df_shaft")
        if df_shaft is not None:
            L_tot = sum(float(r.get("L (m)", 0))
                        for r in df_shaft.to_dict("records"))
            rotor_info.append(["Longueur totale",
                                "{:.4f} m".format(L_tot)])
    except Exception:
        pass

    rotor_info.append(["Materiau",
                        st.session_state.get("mat_name", "—")])

    t_rotor = _make_table_blue(rotor_info)
    elements.append(t_rotor)
    elements.append(Spacer(1, 0.5*cm))

    # Image rotor 3D
    if st.session_state.get("m9_inc_figs") and \
            st.session_state.get("img_rotor"):
        try:
            img_io = io.BytesIO(st.session_state["img_rotor"])
            img    = RLImage(img_io, width=14*cm, height=7*cm)
            elements.append(img)
            elements.append(Paragraph(
                "Figure 1 — Geometrie 3D du rotor", style_caption))
            elements.append(Spacer(1, 0.3*cm))
        except Exception:
            pass

    # Tableau arbre
    df_shaft = st.session_state.get("df_shaft")
    if df_shaft is not None and not df_shaft.empty:
        elements.append(Paragraph("Elements d'arbre :", style_h2))
        shaft_data = [list(df_shaft.columns)]
        for _, row in df_shaft.iterrows():
            shaft_data.append([str(round(v, 6)) if isinstance(v, float)
                                else str(v) for v in row])
        elements.append(_make_table_blue(shaft_data))
        elements.append(Spacer(1, 0.3*cm))

    # ── SECTION 2 : ANALYSE MODALE ────────────────────────────────────────
    df_modal = st.session_state.get("df_modal")
    if st.session_state.get("m9_inc_modal") and df_modal is not None \
            and not df_modal.empty:
        elements.append(PageBreak())
        elements.append(Paragraph("2. Analyse modale", style_h1))
        elements.append(Paragraph(
            "Frequences propres et stabilite du rotor.", style_body))
        elements.append(Spacer(1, 0.3*cm))

        modal_data = [list(df_modal.columns)]
        for _, row in df_modal.iterrows():
            modal_data.append([str(v) for v in row])
        elements.append(_make_table_blue(modal_data))
        elements.append(Spacer(1, 0.3*cm))

    # ── SECTION 3 : CAMPBELL ─────────────────────────────────────────────
    df_camp = st.session_state.get("df_campbell")
    if st.session_state.get("m9_inc_campbell") and \
            df_camp is not None and not df_camp.empty:
        elements.append(Paragraph("3. Vitesses critiques (Campbell)", style_h1))

        camp_data = [list(df_camp.columns)]
        for _, row in df_camp.iterrows():
            camp_data.append([str(v) for v in row])
        elements.append(_make_table_green(camp_data))
        elements.append(Spacer(1, 0.3*cm))

        # Image Campbell
        if st.session_state.get("m9_inc_figs") and \
                st.session_state.get("img_campbell"):
            try:
                img_io = io.BytesIO(st.session_state["img_campbell"])
                img    = RLImage(img_io, width=14*cm, height=8*cm)
                elements.append(img)
                elements.append(Paragraph(
                    "Figure 2 — Diagramme de Campbell", style_caption))
            except Exception:
                pass
        elements.append(Spacer(1, 0.3*cm))

    # ── SECTION 4 : API 684 ───────────────────────────────────────────────
    df_api    = st.session_state.get("df_api")
    api_params = st.session_state.get("api_params")
    if st.session_state.get("m9_inc_api") and \
            df_api is not None and not df_api.empty:
        elements.append(Paragraph("4. Conformite normative API 684", style_h1))

        if api_params:
            score  = float(api_params.get("score", 0))
            op_rpm = float(api_params.get("op_rpm", 0))
            zl     = float(api_params.get("zl", 0))
            zh     = float(api_params.get("zh", 0))
            elements.append(Paragraph(
                "Vitesse operationnelle : {:.0f} RPM | "
                "Zone interdite : [{:.0f} - {:.0f}] RPM | "
                "Score : {:.0f}%".format(op_rpm, zl, zh, score),
                style_body))
            elements.append(Spacer(1, 0.2*cm))

        api_data = [list(df_api.columns)]
        for _, row in df_api.iterrows():
            api_data.append([str(v) for v in row])
        elements.append(_make_table_red(api_data))
        elements.append(Spacer(1, 0.3*cm))

    # ── SECTION 5 : CODE PYTHON ───────────────────────────────────────────
    if st.session_state.get("m9_inc_code"):
        elements.append(PageBreak())
        elements.append(Paragraph("5. Script Python reproductible", style_h1))
        script_lines = _generate_python_script(rotor).split("\n")
        code_data = [[line] for line in script_lines[:40]]
        code_table = Table(code_data, colWidths=[16*cm])
        code_table.setStyle(TableStyle([
            ("FONTNAME",  (0,0), (-1,-1), "Courier"),
            ("FONTSIZE",  (0,0), (-1,-1), 7.5),
            ("BACKGROUND",(0,0), (-1,-1), colors.HexColor("#1E1E2E")),
            ("TEXTCOLOR", (0,0), (-1,-1), colors.HexColor("#D4D4D4")),
            ("LEFTPADDING",(0,0),(-1,-1), 8),
            ("TOPPADDING", (0,0),(-1,-1), 2),
            ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ]))
        elements.append(code_table)

    # ── PIED DE PAGE ──────────────────────────────────────────────────────
    elements.append(Spacer(1, 1*cm))
    elements.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor("#D0D8E4")))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "RotorLab Suite 2.0 — {} — {} — {}".format(
            author, inst, ts_str),
        style_caption))

    doc.build(elements)
    return buf.getvalue()


def _make_table_blue(data):
    return _make_colored_table(data, "#1F5C8B")

def _make_table_green(data):
    return _make_colored_table(data, "#22863A")

def _make_table_red(data):
    return _make_colored_table(data, "#8B1F1F")

def _make_colored_table(data, header_color):
    n_cols = len(data[0])
    col_w  = 15.5 * cm / n_cols
    t = Table(data, colWidths=[col_w] * n_cols)
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),
         colors.HexColor(header_color)),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8.5),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#F2F5F9"), colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.5,
         colors.HexColor("#D0D8E4")),
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
    title  = st.session_state.get("m9_title",
                                   "Rapport de Simulation Rotordynamique")

    def df_to_html(df, header_color="#1F5C8B"):
        rows = ""
        for _, row in df.iterrows():
            rows += "<tr>"
            for v in row:
                rows += "<td>{}</td>".format(str(v).replace(
                    "✅","OK").replace("❌","NON").replace("⚠️","WARN"))
            rows += "</tr>"
        headers = "".join("<th>{}</th>".format(c) for c in df.columns)
        return (
            "<table><thead style='background:{};color:white;'>"
            "<tr>{}</tr></thead><tbody>{}</tbody></table>".format(
                header_color, headers, rows)
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
    """.format(rotor.m, len(rotor.nodes), len(rotor.nodes)*4,
               st.session_state.get("mat_name","—"))

    df_modal = st.session_state.get("df_modal")
    if df_modal is not None and not df_modal.empty:
        sections += "<h2>2. Analyse modale</h2>"
        sections += df_to_html(df_modal, "#1F5C8B")

    df_camp = st.session_state.get("df_campbell")
    if df_camp is not None and not df_camp.empty:
        sections += "<h2>3. Vitesses critiques (Campbell)</h2>"
        sections += df_to_html(df_camp, "#22863A")

    df_api    = st.session_state.get("df_api")
    api_params = st.session_state.get("api_params")
    if df_api is not None and not df_api.empty:
        sections += "<h2>4. Conformite API 684</h2>"
        if api_params:
            sections += "<p>Vitesse operationnelle : {:.0f} RPM | " \
                        "Score : {:.0f}%</p>".format(
                            float(api_params.get("op_rpm",0)),
                            float(api_params.get("score",0)))
        sections += df_to_html(df_api, "#8B1F1F")

    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>RotorLab Suite 2.0 — {title}</title>
<style>
  body {{ font-family:Arial,sans-serif; max-width:960px;
          margin:30px auto; color:#333; line-height:1.5; }}
  h1   {{ color:#1F5C8B; border-bottom:3px solid #1F5C8B;
          padding-bottom:8px; }}
  h2   {{ color:#C55A11; margin-top:28px; }}
  table {{ width:100%; border-collapse:collapse; margin:12px 0; }}
  th   {{ padding:8px 10px; text-align:left; }}
  td   {{ padding:6px 10px; border:1px solid #ddd; font-size:0.9em; }}
  tr:nth-child(even) td {{ background:#F8F8F8; }}
  .header {{ background:#1F5C8B; color:white;
             padding:20px; border-radius:6px; margin-bottom:20px; }}
  .footer {{ margin-top:40px; color:#999;
             font-size:0.8em; border-top:1px solid #eee;
             padding-top:10px; }}
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
  — ross.readthedocs.io
</div>
</body></html>""".format(
        title=title, author=author, inst=inst,
        ts=ts, sections=sections)


# =============================================================================
# GENERATION SCRIPT PYTHON
# =============================================================================
def _generate_python_script(rotor):
    ts     = datetime.now().strftime("%Y-%m-%d %H:%M")
    author = st.session_state.get("m9_author", "Pr. Najeh Ben Guedria")

    # Reconstruction de l'arbre
    shaft_lines = "shaft = [\n"
    df_shaft = st.session_state.get("df_shaft")
    if df_shaft is not None:
        for _, row in df_shaft.iterrows():
            L   = float(row.get("L (m)",   0.2))
            idl = float(row.get("id_L (m)", 0.0))
            odl = float(row.get("od_L (m)", 0.05))
            idr = float(row.get("id_R (m)", idl))
            odr = float(row.get("od_R (m)", odl))
            shaft_lines += (
                "    rs.ShaftElement(L={}, idl={}, odl={}, "
                "idr={}, odr={}, material=mat),\n".format(
                    L, idl, odl, idr, odr))
    shaft_lines += "]"

    # Reconstruction des disques
    disk_lines = "disks = [\n"
    df_disk = st.session_state.get("df_disk")
    if df_disk is not None:
        for _, row in df_disk.iterrows():
            disk_lines += (
                "    rs.DiskElement(n={}, m={:.4f}, "
                "Id={:.6f}, Ip={:.6f}),\n".format(
                    int(row.get("noeud", row.get("nœud", 0))),
                    float(row.get("Masse (kg)", 0)),
                    float(row.get("Id (kg.m²)", 0)),
                    float(row.get("Ip (kg.m²)", 0))))
    disk_lines += "]"

    # Reconstruction des paliers
    bear_lines = "bearings = [\n"
    df_bear = st.session_state.get("df_bear")
    if df_bear is not None:
        for _, row in df_bear.fillna(0).iterrows():
            n   = int(row.get("noeud", row.get("nœud", 0)))
            kxx = float(row.get("kxx", 1e6))
            kyy = float(row.get("kyy", 1e6))
            kxy = float(row.get("kxy", 0.0))
            cxx = float(row.get("cxx", 0.0))
            cyy = float(row.get("cyy", 0.0))
            bear_lines += (
                "    rs.BearingElement(n={}, kxx={:.2e}, kyy={:.2e}, "
                "kxy={:.2e}, kyx={:.2e}, cxx={:.1f}, cyy={:.1f}),\n".format(
                    n, kxx, kyy, kxy, -kxy, cxx, cyy))
    bear_lines += "]"

    # Sections d'analyse
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
