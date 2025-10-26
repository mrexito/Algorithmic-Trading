"""Simple moving average crossover strategy implementation."""

import backtrader as bt


class SMAStrategy(bt.Strategy):
    """Enter long when price crosses above a short SMA and exit on crosses below."""

    def __init__(self):
        """Initialize the moving average indicator used for signals."""
        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=10)

    def next(self):
        """Generate buy/sell orders based on the relationship to the SMA."""
        if not self.position and self.data.close[0] > self.sma[0]:
            self.buy()
        elif self.position and self.data.close[0] < self.sma[0]:
            self.close()
