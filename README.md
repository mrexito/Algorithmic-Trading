# My Trading Bot Dashboard
This repository contains a small prototype for a trading strategy backtesting framework. It includes example strategies, historical data and a Plotly Dash web interface to analyze the backtest results. The dashboard consists of three tabs:
1. **Übersicht & Vergleich** – mehrere Strategien und Symbole gleichzeitig vergleichen
2. **Strategiedetails** – detaillierte Metriken für eine Strategie/Symbol-Kombination
3. **Strategiebeschreibungen** – Textbeschreibungen aus dem `docs/` Ordner


## Folder structure

```
Projekt/
  my_trading_bot/                # Python package with the trading logic
    backtest_runner.py          # Executes backtests for each strategy/symbol
    config/                     # Global settings
    data/                       # Data download helpers and CSV files
    dashboard/                  # Plotly Dash application
    docs/                       # Markdown descriptions for strategies
    results/                    # Pickled returns named <STRATEGY>_<SYMBOL>_returns.pkl
    strategies/                 # Example trading strategies
  requirements.txt

## How to run
1. **Umgebung vorbereiten**
   - Verwende Python 3.11 (siehe Hinweis in `Projekt/requirements.txt`).
   - Optional: virtuelles Environment anlegen, z. B. mit `python -m venv .venv` und anschließend `source .venv/bin/activate` (Linux/macOS) bzw. `.venv\\Scripts\\activate` (Windows).
   - Abhängigkeiten installieren:
     ```bash
     pip install -r Projekt/requirements.txt
     ```
2. **Backtests erzeugen**
   - Führe die Berechnungen mit allen gewünschten Strategien/Symbolen aus. Die Resultate werden als `results/<STRATEGIE>_<SYMBOL>_returns.pkl` abgelegt:
     ```bash
     python Projekt/my_trading_bot/backtest_runner.py
     ```
3. **Dashboard starten**
   - Starte die Dash-App und öffne anschließend http://127.0.0.1:8050 im Browser:
     ```bash
     python Projekt/my_trading_bot/dashboard/app.py
     ```
4. **Nutzung**
   - **Tab 1 – Übersicht & Vergleich:** mehrere Strategien und Symbole vergleichen, Kennzahlen prüfen und Equity-Kurven abgleichen.
   - **Tab 2 – Strategiedetails:** mit abhängigen Dropdowns eine Kombination auswählen und den QuantStats-Tearsheet laden.
   - **Tab 3 – Strategiebeschreibungen:** Markdown-Dokumentation zu den Strategien lesen.

Das Projekt verwendet lokale CSV-Dateien für historische Kurse und legt Backtest-Ergebnisse als Pickle-Serien im Ordner `results/` ab.



