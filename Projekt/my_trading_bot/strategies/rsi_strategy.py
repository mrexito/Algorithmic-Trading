"""Relative Strength Index mean-reversion strategy."""

import backtrader as bt


class RSIStrategy(bt.Strategy):
    """Buy oversold markets and exit once RSI signals overbought conditions."""

    def __init__(self):
        """Create the RSI indicator used for thresholds."""
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=14)

    def next(self):
        """Enter and exit based on RSI crossing fixed oversold/overbought levels."""
        if not self.position and self.rsi < 30:
            self.buy()
        elif self.position and self.rsi > 70:
            self.close()
