import backtrader as bt


class RSIStrategy(bt.Strategy):
    def __init__(self):
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=14)

    def next(self):
        if not self.position and self.rsi < 30:
            self.buy()
        elif self.position and self.rsi > 70:
            self.close()
