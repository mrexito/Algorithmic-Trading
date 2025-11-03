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

## Usage
1. Install dependencies:
   ```bash
   pip install -r Projekt/requirements.txt
   ```
2. Run the backtests to generate result files:
   ```bash
   python Projekt/my_trading_bot/backtest_runner.py
   ```
3. (Optional) Configure the live market data backend by exporting:
   ```bash
   export TIMESCALE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/market"
   export TS_TABLE="ohlcv"  # optional; defaults to ohlcv
   export MARKET_BOOTSTRAP_SYMBOLS="AAPL,GOOGL"  # optional; defaults shown
   export MARKET_BOOTSTRAP_DURATION="5 D"        # optional
   export MARKET_BOOTSTRAP_BAR_SIZE="5 min"      # optional
   ```
   These variables tell the dashboard where to upsert live prices and which symbols to fetch automatically.
4. Start the dashboard:
   ```bash
   python Projekt/my_trading_bot/dashboard/app.py
   ```
   Open the displayed address in your browser to interact with the three tabs:
   - **Übersicht & Vergleich** – compare strategies across symbols
   - **Strategiedetails** – deep dive into a single strategy/symbol
   - **Strategiebeschreibungen** – read the markdown descriptions

This prototype uses local CSV files for historical price data and stores backtest results in `results/` as pickled Pandas Series.


## 🔗 Data Source & Database Integration

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

#### 🐳 Docker setup
Make sure your Timescale container is running:
```bash
docker ps
```
If not, start it:
```bash
docker run -d --name timescale -e POSTGRES_PASSWORD=postgres -p 5432:5432 timescale/timescaledb:latest-pg15
```

#### 🔧 Environment Configuration
Set up the database connection for the dashboard and data loader:

```bash
export TIMESCALE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/market"
export TS_TABLE="ohlcv"
```

> 💡 You can define these in a `.env` file for convenience.

---

### 3. Dashboard Data Flow
- On startup the Dash app calls `bootstrap_live_data()` from `dashboard/data_loader.py`, which:
  1. Downloads the latest OHLCV data for the configured symbols via `market_data_api.fetch_yahoo`.
  2. Saves a CSV snapshot in `Projekt/my_trading_bot/data/live_data/`.
  3. Upserts the rows into the Timescale table (`TS_TABLE`).
- At runtime dashboard callbacks read OHLCV data from TimescaleDB. If the DB is unreachable the app gracefully falls back to the static CSVs under `data/historical_prices/`.

You can rerun the bootstrap manually at any time by executing:
```bash
python -c "from dashboard.data_loader import bootstrap_live_data; bootstrap_live_data(['AAPL','GOOGL'])"
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


