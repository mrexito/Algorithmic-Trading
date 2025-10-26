"""Moving Average Convergence Divergence trend-following strategy."""

import backtrader as bt


class MACDStrategy(bt.Strategy):
    """Trade the sign of the MACD histogram to follow momentum shifts."""

    def __init__(self):
        """Derive a simple histogram signal from the MACD indicator."""
        macd = bt.indicators.MACD()
        self.signal = macd.macd - macd.signal

    def next(self):
        """Enter long on positive momentum and exit when it turns negative."""
        if not self.position and self.signal[0] > 0:
            self.buy()
        elif self.position and self.signal[0] < 0:
            self.close()
