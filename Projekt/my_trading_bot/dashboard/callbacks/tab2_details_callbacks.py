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

from dashboard.data_loader import get_benchmark_returns, load_returns


# beim Start die Versionen ausgeben (nur zur Kontrolle)
import pandas as _pd, quantstats as _qs, numpy as _np
print(f"[QS-Env] pandas={_pd.__version__} quantstats={_qs.__version__} numpy={_np.__version__}")


def _normalize_returns(x: pd.Series | pd.DataFrame) -> pd.Series:
    """Bringt Equity- oder Return-Daten in taegliche einfache Renditen-Form fuer QuantStats."""

    series = x
    if isinstance(series, pd.DataFrame):
        for column in ["returns", "ret", "r", "daily_return", "strategy_return"]:
            if column in series.columns:
                series = series[column]
                break
        else:
            series = series.iloc[:, 0]

    series = pd.Series(series).copy()
    if not isinstance(series.index, pd.DatetimeIndex):
        series.index = pd.to_datetime(series.index, errors="coerce")
    series = series.dropna().sort_index()

    values = pd.to_numeric(series, errors="coerce")
    values = values.dropna()

    if values.empty:
        return pd.Series(dtype=float, name="returns")

    # Equity-Kurve zu Renditen umwandeln
    if values.min() >= 0 and values.max() > 2:
        values = values.pct_change().fillna(0.0)

    returns = values.groupby(values.index.normalize()).apply(lambda v: (1.0 + v).prod() - 1.0)
    returns = returns.astype(float).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    returns = returns.asfreq("D", fill_value=0.0)
    try:
        returns.index.freq = pd.tseries.frequencies.to_offset("D")
    except Exception:
        pass
    returns.name = "returns"
    return returns


@dash.callback(
    [Output("quantstats-metrics", "children"),
     Output("quantstats-report", "children")],
    [Input("details-strategy-dropdown", "value"),
     Input("details-symbol-dropdown", "value")]
)
def update_details(strategy, symbol):
    if not strategy or not symbol:
        return dash.no_update, dash.no_update

    raw = load_returns(symbol, strategy)
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

    benchmark_returns = get_benchmark_returns("^SSMI", returns.index)

    # 2️⃣ Vollstaendiger QuantStats-HTML-Report mit Benchmark-Fallback
    tmp_path = None
    report_children: list = []
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".html")
        os.close(fd)

        try:
            if benchmark_returns is not None and not benchmark_returns.empty:
                qsr.html(
                    returns,
                    benchmark=benchmark_returns,
                    output=tmp_path,
                    title=f"Strategie Tearsheet: {strategy} - {symbol}",
                    download_filename="quantstats_report.html",
                )
            else:
                qsr.html(
                    returns,
                    output=tmp_path,
                    title=f"Strategie Tearsheet: {strategy} - {symbol}",
                    download_filename="quantstats_report.html",
                )
        except Exception:
            qsr.html(
                returns,
                output=tmp_path,
                title=f"Strategie Tearsheet: {strategy} - {symbol}",
                download_filename="quantstats_report.html",
            )

        with open(tmp_path, "r", encoding="utf-8") as f:
            report_html = f.read()

        report_children.append(
            html.Iframe(
                srcDoc=report_html,
                style={"width": "100%", "height": "1800px", "border": "none"},
            )
        )

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
        report_children = [
            html.P("Fehler beim Laden des QuantStats-Reports."),
            html.Pre(str(err)),
            html.Pre("\n".join(dbg)),
        ]
    finally:
        if tmp_path and tmp_path.startswith(tempfile.gettempdir()) and os.path.exists(tmp_path):
            os.remove(tmp_path)

    # 3️⃣ Equity-Vergleich als eingebettetes Bild
    if benchmark_returns is not None and not benchmark_returns.empty:
        try:
            aligned_returns = benchmark_returns.reindex(returns.index, fill_value=0.0)
            strategy_equity = (1.0 + returns).cumprod()
            benchmark_equity = (1.0 + aligned_returns).cumprod()

            fig, ax = plt.subplots(figsize=(10, 4.5))
            ax.plot(strategy_equity.index, strategy_equity.values, label=f"Strategie {strategy}")
            ax.plot(benchmark_equity.index, benchmark_equity.values, label="Benchmark ^SSMI")
            ax.set_title("Equity-Vergleich Strategie vs. ^SSMI")
            ax.set_xlabel("Datum")
            ax.set_ylabel("Equity (Startwert = 1.0)")
            ax.grid(True, which="major", linestyle=":", linewidth=0.7)
            ax.legend()
            fig.tight_layout()

            buffer = io.BytesIO()
            fig.savefig(buffer, format="png", dpi=150)
            plt.close(fig)
            buffer.seek(0)
            encoded = base64.b64encode(buffer.read()).decode("ascii")
            image_uri = f"data:image/png;base64,{encoded}"

            report_children.append(
                html.Div(
                    [
                        html.H4("Equity-Vergleich"),
                        html.Img(src=image_uri, style={"width": "100%", "maxWidth": "960px"}),
                    ],
                    style={"marginTop": "24px", "textAlign": "center"},
                )
            )
        except Exception:
            # Plot optional, Fehler werden bewusst verschluckt
            pass

    report_content = html.Div(report_children)

    return metrics_content, report_content
