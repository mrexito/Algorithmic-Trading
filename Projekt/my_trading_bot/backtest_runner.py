"""Utility entry point for executing all strategies and storing their returns."""

import os
import pickle
import pandas as pd
import backtrader as bt
from data.data_handler import download_and_save_data
from strategies.macd_strategy import MACDStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.sma_strategy import SMAStrategy
from strategies.dummy_strategy import DummyStrategy
from strategies.ai_strategy import AIStrategy
from strategies.dtw_strategy import DTWStrategy
from strategies.horizontal_pattern_strategy import HorizontalPatternStrategy
from strategies.bollinger_strategy import BollingerStrategy
from strategies.zigzag_strategy import ZigZagStrategy
from config.settings import PREDEFINED_SYMBOLS, CAPITAL, COMMISSION

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_DIR = os.path.join(BASE_DIR, "results")
DATA_DIR = os.path.join(BASE_DIR, "data", "historical_prices")


def run_backtests():
    """Run every registered strategy over each symbol and persist cumulative returns."""
    strategies = {
        "MACD": MACDStrategy,
        "RSI": RSIStrategy,
        "SMA": SMAStrategy,
        "DUMMY": DummyStrategy,
        "AI": AIStrategy,
        "DTW": DTWStrategy,
        "HORIZONTAL": HorizontalPatternStrategy,
        "BOLLINGER": BollingerStrategy,
        "ZIGZAG": ZigZagStrategy
    }

    os.makedirs(RESULT_DIR, exist_ok=True)
    download_and_save_data()

    for symbol in PREDEFINED_SYMBOLS:
        df = pd.read_csv(os.path.join(DATA_DIR, f"{symbol}.csv"), index_col="datetime", parse_dates=True)

        for strat_name, strat_class in strategies.items():
            cerebro = bt.Cerebro()
            data = bt.feeds.PandasData(dataname=df)
            cerebro.adddata(data)
            cerebro.addstrategy(strat_class)
            # Batch Size anpassen bei Bedarf aktuell 10% -> 10% des Kapitals pro Trade
            cerebro.addsizer(bt.sizers.PercentSizer, percents=5)
            cerebro.broker.set_cash(CAPITAL)
            cerebro.broker.setcommission(commission=COMMISSION)
            cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn')
            results = cerebro.run()

            returns = results[0].analyzers.timereturn.get_analysis()
            returns_series = pd.Series(returns)

            filename = f"{strat_name}_{symbol}_returns.pkl"
            with open(os.path.join(RESULT_DIR, filename), "wb") as f:
                pickle.dump(returns_series, f)


if __name__ == "__main__":
    run_backtests()
