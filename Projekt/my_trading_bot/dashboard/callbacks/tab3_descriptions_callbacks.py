# ==================== dashboard/callbacks/tab3_descriptions_callbacks.py ====================
"""Callbacks that load markdown descriptions for the selected strategy."""

import os
from dash import Output, Input
from dash import callback
from dash import dcc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC_DIR = os.path.join(BASE_DIR, "docs", "strategy_descriptions")


@callback(
    Output("strategy-description-content", "children"),
    Input("description-strategy-dropdown", "value"),
)
def update_strategy_description(strategy_name):
    """Load and render the markdown description for the requested strategy."""
    if not strategy_name:
        return "Bitte wähle eine Strategie aus dem Dropdown-Menü aus."

    file_path = os.path.join(DOC_DIR, f"{strategy_name}_description.md")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return dcc.Markdown(content)

    return "Keine Beschreibung für die ausgewählte Strategie gefunden."
