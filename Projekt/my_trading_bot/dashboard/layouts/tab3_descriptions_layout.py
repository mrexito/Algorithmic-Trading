# ==================== dashboard/layouts/tab3_descriptions_layout.py ====================

import os
from dash import html, dcc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC_DIR = os.path.join(BASE_DIR, "docs", "strategy_descriptions")


def get_available_strategies():
    if not os.path.exists(DOC_DIR):
        return []
    files = [f for f in os.listdir(DOC_DIR) if f.endswith("_description.md")]
    return [f.replace("_description.md", "") for f in files]


strategy_options = get_available_strategies()

layout = html.Div([
    html.H2("Strategiebeschreibungen"),
    html.Div([
        html.Label("Wähle eine Strategie:"),
        dcc.Dropdown(
            id="description-strategy-dropdown",
            options=[{"label": s, "value": s} for s in strategy_options],
            placeholder="Strategie auswählen"
        )
    ]),
    html.Div(id="strategy-description-content", style={"marginTop": "20px"})
])
