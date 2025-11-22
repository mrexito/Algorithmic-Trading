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
   - Optional: virtuelles Environment anlegen, z. B. mit `python -m venv .venv` und anschliessend `source .venv/bin/activate` (Linux/macOS) bzw. `.venv\\Scripts\\activate` (Windows).
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
   - Starte die Dash-App und öffne anschliessend http://127.0.0.1:8050 im Browser:
     ```bash
     python Projekt/my_trading_bot/dashboard/app.py
     ```
4. **Nutzung**
   - **Tab 1 – Übersicht & Vergleich:** mehrere Strategien und Symbole vergleichen, Kennzahlen prüfen und Equity-Kurven abgleichen.
   - **Tab 2 – Strategiedetails:** mit abhängigen Dropdowns eine Kombination auswählen und den QuantStats-Tearsheet laden.
   - **Tab 3 – Strategiebeschreibungen:** Markdown-Dokumentation zu den Strategien lesen.

Das Projekt verwendet lokale CSV-Dateien für historische Kurse und legt Backtest-Ergebnisse als Pickle-Serien im Ordner `results/` ab.


## Data Source & Database Integration

This project now supports **live market data fetching via Yahoo Finance** and **automatic storage in TimescaleDB** (running inside Docker).

### 1. Yahoo Finance Integration
The module `Projekt/my_trading_bot/data/market_data_api.py` handles market data loading using the [yfinance](https://pypi.org/project/yfinance/) library.

You can fetch and store data manually via:
```bash
python -m Projekt.my_trading_bot.data.market_data_api AAPL --provider yf --duration "5 D" --bar-size "5 min"
```

**Parameters:**
- `symbol`: Stock ticker (e.g., `AAPL`, `MSFT`)
- `--provider`: Currently only `yf` (Yahoo Finance)
- `--duration`: Time range (e.g., `"1 D"`, `"5 D"`, `"1 Mo"`, `"1 Y"`)
- `--bar-size`: Granularity (e.g., `"1 min"`, `"5 min"`, `"1 day"`)

This will:
1. Fetch recent price data from Yahoo Finance.
2. Save a CSV copy under `data/live_data/`.
3. Upsert all data directly into the **TimescaleDB** table `ohlcv`.

> When the dashboard boots, it calls the same API automatically for the symbols defined in `MARKET_BOOTSTRAP_SYMBOLS` (defaults: `AAPL, GOOGL`). If the API call fails, the app continues to run using the most recent CSV/DB data without crashing.

---

### 2. TimescaleDB Integration
The project uses a **TimescaleDB container** to store OHLCV (Open, High, Low, Close, Volume) data.

#### Docker & TimescaleDB setup
Follow these one-time steps to bootstrap a TimescaleDB instance inside Docker:

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine on Linux) and make sure the daemon is running.
2. Pull the TimescaleDB image and create a persistent volume so your database survives container restarts:
   ```bash
   docker pull timescale/timescaledb:latest-pg15
   docker volume create timescale_data
   ```
3. Launch the container (adjust the password or port if needed):
   ```bash
   docker run -d \
     --name timescale \
     -e POSTGRES_PASSWORD=postgres \
     -p 5432:5432 \
     -v timescale_data:/var/lib/postgresql/data \
     timescale/timescaledb:latest-pg15
   ```
4. Create the `market` database, enable the Timescale extension and provision the `ohlcv` table:
   ```bash
   docker exec -it timescale psql -U postgres -c "CREATE DATABASE market;"
   docker exec -it timescale psql -U postgres -d market -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
   docker exec -it timescale psql -U postgres -d market -c "
     CREATE TABLE IF NOT EXISTS ohlcv (
       datetime TIMESTAMPTZ NOT NULL,
       symbol TEXT NOT NULL,
       open DOUBLE PRECISION,
       high DOUBLE PRECISION,
       low DOUBLE PRECISION,
       close DOUBLE PRECISION,
       volume DOUBLE PRECISION,
       PRIMARY KEY (datetime, symbol)
     );
     SELECT create_hypertable('ohlcv', 'datetime', if_not_exists => TRUE);
   "
   ```
5. Verify the container is healthy:
   ```bash
   docker ps --filter name=timescale
   ```

#### Environment Configuration
Set up the database connection for the dashboard and data loader:

```bash
export TIMESCALE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/market"
export TS_TABLE="ohlcv"
```

---

### 3. Dashboard Data Flow
- On startup the Dash app calls `bootstrap_live_data()` from `dashboard/data_loader.py`, which:
  1. Downloads the latest OHLCV data for the configured symbols via `market_data_api.fetch_yahoo`.
  2. Saves a CSV snapshot in `Projekt/my_trading_bot/data/live_data/`.
  3. Upserts the rows into the Timescale table (`TS_TABLE`).
- Defaults now request one year of daily bars (`duration="1 Y"`, `bar-size="1 day"`); adjust the env vars above if you need a different horizon or granularity.
- At runtime dashboard callbacks read OHLCV data from TimescaleDB. If the DB is unreachable the app gracefully falls back to the static CSVs under `data/historical_prices/`.
- The Yahoo fetch logic now lives solely in `data/market_data_api.py`; `data_handler.py` acts as a thin CLI wrapper so strategy code and the dashboard share identical normalization rules.
- `market_data_api.fetch_yahoo` includes retry/backoff handling to mitigate transient yfinance hiccups before giving up.
- Bootstrapping now runs in a background thread so the Dash UI comes up immediately. The header status shows `Bootstrapping …` until the fetch finishes (or reports cached data).
- Tab 1 now offers an input field to queue additional symbols (comma- or space-separated). Triggering the button runs the same bootstrap routine in the background, stores new data in TimescaleDB, and refreshes the dropdowns once rows are available.
- Successful runs persist a small cache marker (`data/live_data/.bootstrap_state.json`). If Dash reloads within `MARKET_BOOTSTRAP_CACHE_TTL` seconds with the same symbols & settings, the bootstrap is skipped and the status reports the last success timestamp.

You can rerun the bootstrap manually at any time by executing:
```bash
python -c "from my_trading_bot.dashboard.data_loader import bootstrap_live_data; bootstrap_live_data(['AAPL','GOOGL'])"
```

---

### 4. Verification
To confirm data is stored in the database, run:
```bash
docker exec -it timescale psql -U postgres -d market -c "SELECT COUNT(*) FROM ohlcv;"
```

Or preview the last few entries:
```bash
docker exec -it timescale psql -U postgres -d market -c "SELECT * FROM ohlcv ORDER BY datetime DESC LIMIT 5;"
```

### 5. Datenpersistenz & Interaktion
Die Datenpipeline besteht aus klar getrennten Schritten, die zusammen sicherstellen, dass neue Kurse zuverlässig in der TimescaleDB landen und anschliessend vom Dashboard genutzt werden können:

1. **Bootstrap-Trigger**  
   Beim Start der Dash-App oder durch manuelle CLI-Aufrufe ruft `dashboard/data_loader.py` die Funktion `bootstrap_live_data()` auf. Die Symbolmenge stammt aus `MARKET_BOOTSTRAP_SYMBOLS` (Umgebung oder `.env`), optional ergänzt durch Eingaben in Tab 1. Ein Cache (`data/live_data/.bootstrap_state.json`) verhindert Mehrfach-Downloads innerhalb des `MARKET_BOOTSTRAP_CACHE_TTL`.

2. **Datenabruf & Normalisierung**  
   Für jedes Symbol lädt `Projekt/my_trading_bot/data/market_data_api.fetch_yahoo()` OHLCV-Werte via yfinance. Die Funktion vereinheitlicht Spalten, erzwingt UTC-Zeitstempel und fügt das Symbol als Spalte hinzu, sodass jede Zeile eindeutig (`symbol`, `datetime`) identifizierbar ist.

3. **Lokaler Snapshot**  
   Anschliessend erstellt `market_data_api.save_csv()` unter `data/live_data/` einen CSV-Snapshot (z. B. `AAPL_live.csv`). Diese Kopie dient als sofortiger Fallback, falls die Datenbank nicht erreichbar ist oder Tests offline laufen müssen.

4. **Schreiben in TimescaleDB**  
   Ist `TIMESCALE_URL` gesetzt, baut `bootstrap_live_data()` per SQLAlchemy eine Verbindung auf und übergibt das DataFrame an `market_data_api.upsert_timescale()`. Diese Funktion legt bei Bedarf die Tabelle (`TS_TABLE`, Standard `ohlcv`) an, erzwingt den Primärschlüssel (`symbol`, `datetime`) und führt ein UPSERT aus, sodass doppelte Zeitstempel überschrieben statt dupliziert werden. In einer Timescale-Hypertable-Umgebung bleiben damit historische und neue Daten konsistent.

5. **Laufzeitinteraktion im Dashboard**  
   Dashboard-Callbacks lesen über `get_available_results()` und `load_returns()` (ebenfalls in `dashboard/data_loader.py`) direkt aus der TimescaleDB. Fällt die Verbindung aus, greifen beide Funktionen automatisch auf die lokalen CSVs zurück. Dadurch erhält jede UI-Komponente stets eine konsistente Sicht auf dieselbe Datenbasis, unabhängig davon, ob die Daten ursprünglich aus Live-Abfragen oder aus Backtests stammen.

6. **Nebenläufigkeit & Statusmeldungen**  
   Das Bootstrap läuft in einem Hintergrund-Thread und verwendet einen Reentrant-Lock sowie Statusvariablen, damit mehrere Auslöser (Button-Klick, App-Start, CLI) koexistieren können, ohne Daten zu überschreiben. Der Status erscheint im Dashboard-Header (z. B. „Bootstrapping…“ oder Zeitpunkt des letzten erfolgreichen Runs) und erlaubt eine transparente Beobachtung der Datenflüsse.

Durch diese Kette – Download, Normalisierung, Snapshot, Timescale-Upsert und UI-Abfrage – entsteht eine deterministische, reproduzierbare Interaktion mit der Datenbank, die sowohl wissenschaftlichen als auch betrieblichen Anforderungen genügt.

## Technische Projektdokumentation (Sphinx)
Die technische Referenz wird mit [Sphinx](https://www.sphinx-doc.org) erzeugt und liest automatisch alle Docstrings aus dem Paket `my_trading_bot` ein.

1. **Abhängigkeiten installieren**
   ```bash
   pip install -r Projekt/requirements.txt
   ```
2. **API-Stubs aktualisieren** – bei neuen/verschobenen Modulen:
   ```bash
   sphinx-apidoc -o docs/source/api Projekt/my_trading_bot
   ```
3. **HTML-Version bauen**
   ```bash
   make -C docs html
   open docs/build/html/index.html  # optional
   ```
4. **PDF erstellen (LaTeX-Build erfordert TeXLive/MacTeX)**
   ```bash
   make -C docs latexpdf
   open docs/build/latex/MyTradingBotDashboard.pdf  # Dateiname je nach Projektname
   ```

`docs/source/conf.py` ist bereits mit `autodoc`, `napoleon`, `autosummary` und `viewcode` konfiguriert und fügt dem Import-Pfad automatisch das Verzeichnis `Projekt/` hinzu. Damit lässt sich die vollständige API-Dokumentation reproduzierbar in HTML und PDF exportieren.
