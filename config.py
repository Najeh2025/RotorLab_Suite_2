# config.py — Constantes globales de RotorLab Suite 2.0

APP_NAME    = "RotorLab Suite 2.0"
APP_VERSION = "2.0.0"
APP_AUTHOR  = "Pr. Najeh Ben Guedria"
APP_INST    = "ISTLS — Université de Sousse"

# ── Palette de couleurs ──────────────────────────────────────────────────
COLORS = {
    "primary"   : "#1F5C8B",
    "secondary" : "#C55A11",
    "success"   : "#22863A",
    "danger"    : "#C00000",
    "warning"   : "#F9A825",
    "light_bg"  : "#F0F4FF",
    "panel_bg"  : "#FAFBFD",
}

# ── Base de données matériaux ────────────────────────────────────────────
MATERIALS_DB = {
    "Acier standard (AISI 1045)":    {"rho": 7810.0, "E": 211e9, "G_s": 81.2e9},
    "Acier inoxydable (316L)":       {"rho": 7990.0, "E": 193e9, "G_s": 74.0e9},
    "Aluminium (7075-T6)":           {"rho": 2810.0, "E":  72e9, "G_s": 27.0e9},
    "Titane (Ti-6Al-4V)":            {"rho": 4430.0, "E": 114e9, "G_s": 44.0e9},
    "Inconel 718":                   {"rho": 8220.0, "E": 200e9, "G_s": 77.0e9},
    "Acier à outils (H13)":          {"rho": 7760.0, "E": 215e9, "G_s": 83.0e9},
    "Cuivre (CuZn)":                 {"rho": 8500.0, "E": 110e9, "G_s": 41.0e9},
    "Fonte grise (GG25)":            {"rho": 7200.0, "E": 100e9, "G_s": 40.0e9},
    "PEEK (composite fibres)":       {"rho": 1400.0, "E":   4e9, "G_s":  1.4e9},
    "Personnalisé":                  {"rho": 7810.0, "E": 211e9, "G_s": 81.2e9},
}

# ── Presets de paliers ───────────────────────────────────────────────────
BEARING_PRESETS = {
    "Roulement à billes (rigide)":    {"kxx":1e8, "kyy":1e8, "kxy":0.0, "cxx":200.0,  "cyy":200.0},
    "Roulement à rouleaux":           {"kxx":5e8, "kyy":5e8, "kxy":0.0, "cxx":100.0,  "cyy":100.0},
    "Palier lisse hydrodynamique":    {"kxx":1e7, "kyy":5e6, "kxy":2e6, "cxx":2000.0, "cyy":2000.0},
    "Palier magnétique actif (AMB)":  {"kxx":5e6, "kyy":5e6, "kxy":0.0, "cxx":5000.0, "cyy":5000.0},
    "Support souple (amortisseur)":   {"kxx":1e6, "kyy":1e6, "kxy":0.0, "cxx":8000.0, "cyy":8000.0},
    "Palier rigide (encastrement)":   {"kxx":1e9, "kyy":1e9, "kxy":0.0, "cxx":100.0,  "cyy":100.0},
    "Personnalisé":                   {"kxx":1e7, "kyy":1e7, "kxy":0.0, "cxx":500.0,  "cyy":500.0},
}

# ── Arbre de navigation ──────────────────────────────────────────────────
# CORRECTIONS APPLIQUÉES :
#   1. Tous les libellés en français
#   2. Suppression "API 684 Level 1"      → intégré dans M3
#   3. Suppression "Freq. Response H(jω)" → intégré dans M4
#   4. Fusion "Material" + "Parameters"   → "Matériau & Paramètres"
#   5. Section "Actions rapides" supprimée du tree
#      → boutons Compresseur/Reset conservés dans render_model_tree()
MODEL_TREE = [
    {
        "id"      : "global_defs",
        "label"   : "Définitions globales",
        "icon"    : "⚙️",
        "children": [
            {
                "id"    : "material",
                "label" : "Matériau & Paramètres",
                "icon"  : "🧱",
                "module": "M1",
            },
        ]
    },
    {
        "id"      : "rotor_model",
        "label"   : "Modèle du rotor",
        "icon"    : "🔩",
        "children": [
            {"id": "shaft",    "label": "Éléments d'arbre", "icon": "📏", "module": "M1"},
            {"id": "disks",    "label": "Éléments disques", "icon": "💿", "module": "M1"},
            {"id": "bearings", "label": "Paliers & Joints", "icon": "⚙️", "module": "M1"},
        ]
    },
    {
        "id"      : "study",
        "label"   : "Études",
        "icon"    : "🔬",
        "children": [
            {"id": "static_modal", "label": "Statique & Modal",       "icon": "📊", "module": "M2"},
            {"id": "campbell",     "label": "Campbell + UCS Map",      "icon": "📈", "module": "M3"},
            {"id": "unbalance",    "label": "Réponse au balourd",      "icon": "🌀", "module": "M4"},
            {"id": "hd_bearings",  "label": "Paliers film fluide",     "icon": "💧", "module": "M5"},
            {"id": "temporal",     "label": "Réponse temporelle",      "icon": "⏱️", "module": "M6"},
            {"id": "faults",       "label": "Analyse des défauts",     "icon": "🔧", "module": "M7"},
            {"id": "multirotor",   "label": "MultiRotor & Engrenages", "icon": "⚙️", "module": "M8"},
        ]
    },
    {
        "id"      : "results",
        "label"   : "Résultats",
        "icon"    : "📊",
        "children": [
            {"id": "report",  "label": "Rapport & Export",   "icon": "📄", "module": "M9"},
            {"id": "copilot", "label": "SmartRotor Copilot", "icon": "✨", "module": "AI"},
        ]
    },
]
