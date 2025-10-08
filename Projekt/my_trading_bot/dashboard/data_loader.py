import os
import pickle
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULT_DIR = os.path.join(BASE_DIR, "results")

def get_available_results():
    files = [f for f in os.listdir(RESULT_DIR) if f.endswith("_returns.pkl")]
    combos = []
    for f in files:
        name = f.replace("_returns.pkl", "")
        strat, symbol = name.split("_")
        combos.append((symbol, strat))
    return combos

def load_returns(symbol, strategy):
    file_path = os.path.join(RESULT_DIR, f"{strategy}_{symbol}_returns.pkl")
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return pickle.load(f)
    return pd.Series()
