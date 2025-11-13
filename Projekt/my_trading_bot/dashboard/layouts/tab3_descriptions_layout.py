import os

from dash import dcc, html

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC_DIR = os.path.join(BASE_DIR, "docs", "strategy_descriptions")


def get_available_strategies():
    """Return strategy identifiers for which a markdown description exists."""
    if not os.path.exists(DOC_DIR):
        return []
    files = [f for f in os.listdir(DOC_DIR) if f.endswith("_description.md")]
    return [f.replace("_description.md", "") for f in files]


def _dropdown_options():
    return [{"label": strategy, "value": strategy} for strategy in get_available_strategies()]


layout = html.Div(
    className="tab-container",
    children=[
        html.H2("Strategiebeschreibungen", className="tab-heading"),
        html.Div(
            className="control-group",
            children=[
                html.Label("Wähle eine Strategie", className="control-label"),
                dcc.Dropdown(
                    id="description-strategy-dropdown",
                    options=_dropdown_options(),
                    placeholder="Strategie auswählen",
                ),
            ],
        ),
        html.Div(
            id="strategy-description-content",
            className="card",
        ),
    ],
)
