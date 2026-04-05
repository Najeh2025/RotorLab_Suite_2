# config.py — Constantes globales de RotorLab Suite 2.0

APP_NAME    = "RotorLab Suite 2.0"
APP_VERSION = "2.0.0"
APP_AUTHOR  = "Pr. Najeh Ben Guedria"
APP_INST    = "ISTLS — Université de Sousse"

# ── Palette de couleurs (cohérente avec le CSS) ─────────────────────────
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

# ── Structure de l'arbre de navigation (Model Tree) ─────────────────────
MODEL_TREE = [
    {
        "id": "global_defs",
        "label": "Global Definitions",
        "icon": "⚙️",
        "children": [
            {"id": "material",   "label": "Material",    "icon": "🧱", "module": "M1"},
            {"id": "parameters", "label": "Parameters",  "icon": "📋", "module": "M1"},
        ]
    },
    {
        "id": "rotor_model",
        "label": "Rotor Model",
        "icon": "🔩",
        "children": [
            {"id": "shaft",    "label": "Shaft Elements",  "icon": "📏", "module": "M1"},
            {"id": "disks",    "label": "Disk Elements",   "icon": "💿", "module": "M1"},
            {"id": "bearings", "label": "Bearings / Seals","icon": "⚙️", "module": "M1"},
        ]
    },
    {
        "id": "study",
        "label": "Study",
        "icon": "🔬",
        "children": [
            {"id": "static_modal", "label": "Static & Modal",        "icon": "📊", "module": "M2"},
            {"id": "campbell",     "label": "Campbell + UCS Map",     "icon": "📈", "module": "M3"},
            {"id": "api_level1",   "label": "API 684 Level 1",        "icon": "📜", "module": "M3"},
            {"id": "unbalance",    "label": "Unbalance Response",     "icon": "🌀", "module": "M4"},
            {"id": "freq_resp",    "label": "Freq. Response H(jω)",   "icon": "📡", "module": "M4"},
            {"id": "hd_bearings",  "label": "Fluid Film Bearings",    "icon": "💧", "module": "M5"},
            {"id": "temporal",     "label": "Time Response",          "icon": "⏱️", "module": "M6"},
            {"id": "faults",       "label": "Fault Analysis",         "icon": "🔧", "module": "M7"},
            {"id": "multirotor",   "label": "MultiRotor & Gear",      "icon": "⚙️", "module": "M8"},
        ]
    },
    {
        "id": "results",
        "label": "Results",
        "icon": "📊",
        "children": [
            {"id": "report", "label": "Report & Export", "icon": "📄", "module": "M9"},
            {"id": "copilot","label": "SmartRotor Copilot","icon":"✨","module": "AI"},
        ]
    },
]
