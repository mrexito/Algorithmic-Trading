# ==================== dashboard/callbacks/tab2_details_callbacks.py ====================

import base64
import io
import os
import tempfile

import dash
from dash import html
from dash.dependencies import Input, Output
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import quantstats.reports as qsr

from dashboard import data_loader


# beim Start die Versionen ausgeben (nur zur Kontrolle)
import pandas as _pd, quantstats as _qs, numpy as _np

print(f"[QS-Env] pandas={_pd.__version__} quantstats={_qs.__version__} numpy={_np.__version__}")

BENCHMARK_TICKER = "^SSMI"
BENCHMARK_LABEL = "^SSMI"


def _normalize_returns(x: pd.Series | pd.DataFrame) -> pd.Series:
    """Bringt Equity- oder Return-Daten in taegliche einfache Renditen-Form fuer QuantStats."""
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


def _load_benchmark_returns(index: pd.DatetimeIndex) -> tuple[pd.Series, pd.Series, bool]:
    """Liefert Benchmark-Renditen und -Preise (Startwert 1.0)."""
    benchmark_available = False
    bm_returns = pd.Series(dtype=float)
    bm_price = pd.Series(dtype=float)

    getter = getattr(data_loader, "get_benchmark_returns", None)
    if getter is None:
        return bm_returns, bm_price, benchmark_available

    try:
        raw_bm = getter(BENCHMARK_TICKER, index)
    except Exception as err:  # pragma: no cover - defensive logging
        print(f"[Tab2] Benchmark-Laden fehlgeschlagen: {err}")
        return bm_returns, bm_price, benchmark_available

    if raw_bm is None or getattr(raw_bm, "empty", False):
        return bm_returns, bm_price, benchmark_available

    bm_returns = raw_bm.copy()
    if not isinstance(bm_returns.index, pd.DatetimeIndex):
        bm_returns.index = pd.to_datetime(bm_returns.index, errors="coerce")
    bm_returns = bm_returns.sort_index()

    bm_returns = bm_returns.groupby(bm_returns.index.normalize()).apply(lambda v: (1 + v).prod() - 1)
    bm_returns = bm_returns.astype(float).replace([np.inf, -np.inf], np.nan).dropna()
    bm_returns = bm_returns.asfreq("D").fillna(0.0)
    try:
        bm_returns.index.freq = pd.tseries.offsets.Day()
    except Exception:
        pass

    bm_price = (1.0 + bm_returns).cumprod()
    if bm_price.empty:
        return bm_returns, bm_price, benchmark_available

    bm_price = bm_price.asfreq("D")
    bm_price.iloc[0] = 1.0
    bm_price = bm_price.ffill().fillna(1.0)
    bm_price.name = BENCHMARK_LABEL
    benchmark_available = True

    return bm_returns, bm_price, benchmark_available


def _build_equity_plot(returns: pd.Series, bm_returns: pd.Series, benchmark_available: bool) -> html.Img | None:
    try:
        strat_eq = (1.0 + returns).cumprod()
        data = pd.DataFrame({"Strategie": strat_eq})

        if benchmark_available and not bm_returns.empty:
            bm_eq = (1.0 + bm_returns).cumprod()
            bm_eq = bm_eq.reindex(strat_eq.index, method="ffill").fillna(1.0)
            data[BENCHMARK_LABEL] = bm_eq

        fig, ax = plt.subplots(figsize=(10, 4))
        data.plot(ax=ax)
        ax.set_title(f"Equity Vergleich: Strategie vs. {BENCHMARK_LABEL}")
        ax.set_ylabel("Equity Index")
        ax.set_xlabel("Datum")
        ax.legend()
        ax.grid(True, which="both", linestyle=":", linewidth=0.5)

        buffer = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buffer, format="png", dpi=150)
        plt.close(fig)
        buffer.seek(0)
        encoded = base64.b64encode(buffer.read()).decode("ascii")
        return html.Img(
            src=f"data:image/png;base64,{encoded}",
            style={"width": "100%", "maxWidth": "900px", "display": "block", "margin": "20px auto"},
            alt="Equity Vergleich: Strategie vs. ^SSMI",
        )
    except Exception as err:  # pragma: no cover - defensive logging
        print(f"[Tab2] Equity-Plot fehlgeschlagen: {err}")
        return None


@dash.callback(
    [Output("quantstats-metrics", "children"),
     Output("quantstats-report", "children")],
    [Input("details-strategy-dropdown", "value"),
     Input("details-symbol-dropdown", "value")]
)
def update_details(strategy, symbol):
    if not strategy or not symbol:
        return dash.no_update, dash.no_update

    raw = data_loader.load_returns(symbol, strategy)
    if raw is None or (hasattr(raw, "empty") and raw.empty):
        return html.Div("Keine Daten verfügbar."), html.Div()

    returns = _normalize_returns(raw)
    if returns.empty:
        return html.Div("Keine Daten verfügbar."), html.Div()

    # 1️⃣ QuantStats-Metriken (Tabelle)
    stats_df = qsr.metrics(returns, display=False, mode="full")
    metrics_html = stats_df.to_html()
    metrics_content = html.Div([
        html.Iframe(
            srcDoc=metrics_html,
            style={"width": "100%", "height": "420px", "border": "none"},
        )
    ])

    # 2️⃣ Vollstaendiger QuantStats-HTML-Report
    tmp_path = None
    bm_returns, bm_price, benchmark_available = _load_benchmark_returns(returns.index)

    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".html")
        os.close(fd)

        qsr_kwargs = dict(
            output=tmp_path,
            title=f"Strategie Tearsheet: {strategy} - {symbol}",
            download_filename="quantstats_report.html",
        )
        if benchmark_available:
            qsr_kwargs["benchmark"] = bm_price

        qsr.html(returns, **qsr_kwargs)

        with open(tmp_path, "r", encoding="utf-8") as f:
            report_html = f.read()

        equity_plot = _build_equity_plot(returns, bm_returns, benchmark_available)

        children = [
            html.Iframe(
                srcDoc=report_html,
                style={"width": "100%", "height": "1800px", "border": "none"},
            )
        ]
        if equity_plot is not None:
            children.append(html.Div(equity_plot))

        report_content = html.Div(children)

    except Exception as err:
        import pandas as pd, quantstats as qs, numpy as np
        dbg = [
            f"pandas={pd.__version__}",
            f"quantstats={qs.__version__}",
            f"numpy={np.__version__}",
            f"returns_len={len(returns)}",
            f"freq={getattr(returns.index, 'freq', None)}",
            f"head=\n{returns.head().to_string()}",
        ]
        report_content = html.Div([
            html.P("Fehler beim Laden des QuantStats-Reports."),
            html.Pre(str(err)),
            html.Pre("\n".join(dbg)),
        ])
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return metrics_content, report_content
