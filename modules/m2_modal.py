/* ══════════════════════════════════════════════════════════════════════════
   M1 — 3 boutons action uniformes (Appliquer / Charger / Sauvegarder)
   Technique : reconstruction complète du bouton "Browse files" via CSS pur.
   Aucun JavaScript requis.
   ══════════════════════════════════════════════════════════════════════════ */

/* 1. Masquer les instructions drag-and-drop et "Limit 200 MB" */
[data-testid="stFileUploaderDropzoneInstructions"] {
    display: none !important;
}

/* 2. Supprimer le style propre du conteneur dropzone */
[data-testid="stFileUploaderDropzone"] {
    border     : none !important;
    padding    : 0 !important;
    background : transparent !important;
    box-shadow : none !important;
    min-height : 0 !important;
}

/* 3. Reconstruire le bouton "Browse files" comme un bouton secondary Streamlit */
[data-testid="stFileUploaderDropzone"] button {
    /* Réinitialisation complète pour partir d'une base propre */
    all              : unset !important;

    /* Dimensions identiques aux st.button / st.download_button */
    display          : flex !important;
    align-items      : center !important;
    justify-content  : center !important;
    width            : 100% !important;
    min-height       : 38px !important;
    box-sizing       : border-box !important;

    /* Style secondary Streamlit */
    padding          : 0.25rem 0.75rem !important;
    border           : 1px solid rgba(49, 51, 63, 0.2) !important;
    border-radius    : 0.5rem !important;
    background-color : #ffffff !important;
    color            : rgb(49, 51, 63) !important;

    /* Typographie Streamlit */
    font-family      : "Source Sans Pro", sans-serif !important;
    font-size        : 1rem !important;
    font-weight      : 400 !important;
    line-height      : 1.6 !important;

    cursor           : pointer !important;
    user-select      : none !important;
    white-space      : nowrap !important;
    transition       : color 100ms ease, background-color 100ms ease,
                       border-color 100ms ease !important;
}

[data-testid="stFileUploaderDropzone"] button:hover {
    border-color     : rgba(49, 51, 63, 0.4) !important;
    background-color : rgba(151, 166, 195, 0.15) !important;
    color            : rgb(49, 51, 63) !important;
}

/* 4. Remplacer le texte "Browse files" par le libellé souhaité
      Technique : font-size:0 masque le texte natif, ::before l'affiche */
[data-testid="stFileUploaderDropzone"] button p {
    font-size   : 0 !important;
    margin      : 0 !important;
    padding     : 0 !important;
    line-height : 0 !important;
}

[data-testid="stFileUploaderDropzone"] button p::before {
    content     : "📂  Charger un modèle (.json)";
    font-size   : 1rem !important;
    font-weight : 400 !important;
    line-height : 1.6 !important;
    color       : rgb(49, 51, 63) !important;
    font-family : "Source Sans Pro", "Segoe UI Emoji",
                  "Apple Color Emoji", sans-serif !important;
}
