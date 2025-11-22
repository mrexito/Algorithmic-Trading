"""Utility entry point for executing all strategies and storing their returns."""

import os
import pickle
from pathlib import Path

import pandas as pd
import backtrader as bt

from data.market_data_api import fetch_yahoo, save_csv
from strategies.macd_strategy import MACDStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.sma_strategy import SMAStrategy
from strategies.ai_strategy import AIStrategy
from strategies.horizontal_pattern_strategy import HorizontalPatternStrategy
from strategies.bollinger_strategy import BollingerStrategy
from strategies.zigzag_strategy import ZigZagStrategy
from config.settings import PREDEFINED_SYMBOLS, CAPITAL, COMMISSION

try:  # Optional dependency (dtaidistance)
    from strategies.dtw_strategy import DTWStrategy  # type: ignore
except Exception:
    DTWStrategy = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_DIR = os.path.join(BASE_DIR, "results")
DATA_DIR = os.path.join(BASE_DIR, "data", "historical_prices")
DEFAULT_DURATION = os.environ.get("BACKTEST_DURATION", "1 Y")
DEFAULT_BAR_SIZE = os.environ.get("BACKTEST_BAR_SIZE", "1 day")


def run_backtests():
    """Run every registered strategy over each symbol and persist cumulative returns."""
    strategies = {
        "MACD": MACDStrategy,
        "RSI": RSIStrategy,
        "SMA": SMAStrategy,
        "AI": AIStrategy,
        "HORIZONTAL": HorizontalPatternStrategy,
        "BOLLINGER": BollingerStrategy,
        "ZIGZAG": ZigZagStrategy,
    }
    if DTWStrategy is not None:
        strategies["DTW"] = DTWStrategy
    else:
        print("[Backtest] INFO: DTW strategy skipped (dtaidistance not installed).")

    os.makedirs(RESULT_DIR, exist_ok=True)
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

    for symbol in PREDEFINED_SYMBOLS:
        df = fetch_yahoo(symbol, DEFAULT_DURATION, DEFAULT_BAR_SIZE)
        if df.empty:
            print(f"[Backtest] WARNING: No market data for {symbol}; skipping.")
            continue

        save_csv(df, symbol)  # keep live snapshot consistent
        csv_path = Path(DATA_DIR) / f"{symbol}.csv"
        df.to_csv(csv_path, index=False)

        df = pd.read_csv(
            csv_path,
            index_col="datetime",
            parse_dates=True,
        )

        for strat_name, strat_class in strategies.items():
            cerebro = bt.Cerebro()
            data = bt.feeds.PandasData(dataname=df)
            cerebro.adddata(data)
            cerebro.addstrategy(strat_class)
            # Position sizing: default to 5% of capital per trade; adjust if needed
            cerebro.addsizer(bt.sizers.PercentSizer, percents=5)
            cerebro.broker.set_cash(CAPITAL)
            cerebro.broker.setcommission(commission=COMMISSION)
            cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="timereturn")
            results = cerebro.run()

            returns = results[0].analyzers.timereturn.get_analysis()
            returns_series = pd.Series(returns)

            filename = f"{strat_name}_{symbol}_returns.pkl"
            with open(os.path.join(RESULT_DIR, filename), "wb") as f:
                pickle.dump(returns_series, f)


if __name__ == "__main__":
    run_backtests()
