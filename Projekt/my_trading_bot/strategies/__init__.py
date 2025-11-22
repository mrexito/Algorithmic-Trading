"""Convenience exports for all strategies available to the trading bot."""

from .rsi_strategy import RSIStrategy
from .macd_strategy import MACDStrategy
from .sma_strategy import SMAStrategy
from .ai_strategy import AIStrategy
try:  # Optional dependency: dtaidistance
    from .dtw_strategy import DTWStrategy
except Exception:  # pragma: no cover - dependency not available
    DTWStrategy = None
from .horizontal_pattern_strategy import HorizontalPatternStrategy
from .bollinger_strategy import BollingerStrategy
from .zigzag_strategy import ZigZagStrategy

__all__ = [
    "RSIStrategy",
    "MACDStrategy",
    "SMAStrategy",
    "AIStrategy",
    "HorizontalPatternStrategy",
    "BollingerStrategy",
    "ZigZagStrategy",
]

if DTWStrategy is not None:
    __all__.append("DTWStrategy")
