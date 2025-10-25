import os
import yfinance as yf
# import pandas as pd
from config.settings import PREDEFINED_SYMBOLS


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "historical_prices")


def download_and_save_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    for symbol in PREDEFINED_SYMBOLS:
        df = yf.download(symbol, start="2015-01-01", end="2025-06-30")
        df.dropna(inplace=True)
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        df.index.name = 'datetime'
        df.to_csv(os.path.join(DATA_DIR, f"{symbol}.csv"), index=True)
