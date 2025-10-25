import backtrader as bt


class MACDStrategy(bt.Strategy):
    def __init__(self):
        macd = bt.indicators.MACD()
        self.signal = macd.macd - macd.signal

    def next(self):
        if not self.position and self.signal[0] > 0:
            self.buy()
        elif self.position and self.signal[0] < 0:
            self.close()
