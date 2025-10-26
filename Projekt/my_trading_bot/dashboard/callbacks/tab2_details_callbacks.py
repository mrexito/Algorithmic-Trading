# ==================== dashboard/callbacks/tab2_details_callbacks.py ====================
"""Callbacks for the details tab that render QuantStats metrics and reports."""

import os
import tempfile
import dash
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import quantstats.reports as qsr
from dashboard.data_loader import load_returns
import quantstats as qs

# QuantStats internally invokes matplotlib; force a headless backend to avoid macOS GUI/thread issues.
import matplotlib

matplotlib.use("Agg")


def _normalize_returns(x: pd.Series | pd.DataFrame) -> pd.Series:
    """Convert equity or return inputs into daily simple returns for QuantStats."""
    s = x
    if isinstance(s, pd.DataFrame):
        for c in ["returns", "ret", "r", "daily_return", "strategy_return"]:
            if c in s.columns:
                s = s[c]
                break
        else:
            s = s.iloc[:, 0]

    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index, errors="coerce")
    s = s.sort_index()

    # Equity-Kurve -> Renditen
    if s.min() >= 0 and s.max() > 2:
        s = s.pct_change()

    # pro Kalendertag aggregieren
    s = s.groupby(s.index.normalize()).apply(lambda v: (1 + v).prod() - 1)

    # aufraeumen
    s = s.astype(float).replace([np.inf, -np.inf], np.nan).dropna()

    # Tagesfrequenz erzwingen
    s = s.asfreq("D").fillna(0.0)
    try:
        s.index.freq = pd.tseries.offsets.Day()
    except Exception:
        pass

    s.name = "returns"
    return s


@dash.callback(
    [Output("quantstats-metrics", "children"), Output("quantstats-report", "children")],
    [
        Input("details-strategy-dropdown", "value"),
        Input("details-symbol-dropdown", "value"),
    ],
)
def update_details(strategy, symbol):
    """Render QuantStats metrics table and report for the selected strategy/symbol."""
    if not strategy or not symbol:
        return dash.no_update, dash.no_update

    raw = load_returns(symbol, strategy)
    if raw is None or (hasattr(raw, "empty") and raw.empty):
        return html.Div("Keine Daten verfügbar."), html.Div()

    returns = _normalize_returns(raw)
    if returns.empty:
        return html.Div("Keine Daten verfügbar."), html.Div()

    # 1️⃣ QuantStats-Metriken (Tabelle)
    stats_df = qsr.metrics(
        returns,
        display=False,
        mode="full",
        benchmark=None,  # prevent QuantStats from fetching SPY over the network
    )
    metrics_html = stats_df.to_html()
    metrics_content = html.Div(
        [
            html.Iframe(
                srcDoc=metrics_html,
                style={"width": "100%", "height": "420px", "border": "none"},
            )
        ]
    )

    # 2️⃣ Vollstaendiger QuantStats-HTML-Report
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".html")
        os.close(fd)

        qsr.html(
            returns,
            benchmark=None,  # ensure no external benchmark download occurs
            output=tmp_path,
            title=f"Strategie Tearsheet: {strategy} - {symbol}",
            download_filename="quantstats_report.html",
        )

        with open(tmp_path, "r", encoding="utf-8") as f:
            report_html = f.read()

        report_content = html.Div(
            [
                html.Iframe(
                    srcDoc=report_html,
                    style={"width": "100%", "height": "1800px", "border": "none"},
                )
            ]
        )

    except Exception as err:
        dbg = [
            f"pandas={pd.__version__}",
            f"quantstats={qs.__version__}",
            f"numpy={np.__version__}",
            f"returns_len={len(returns)}",
            f"freq={getattr(returns.index, 'freq', None)}",
            f"head=\n{returns.head().to_string()}",
        ]
        report_content = html.Div(
            [
                html.P("Fehler beim Laden des QuantStats-Reports."),
                html.Pre(str(err)),
                html.Pre("\n".join(dbg)),
            ]
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return metrics_content, report_content
