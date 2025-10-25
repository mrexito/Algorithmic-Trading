import backtrader as bt


class DummyStrategy(bt.Strategy):
    def __init__(self):
        self.counter = 0

    def next(self):
        self.counter += 1
        if self.counter % 10 == 0:
            if not self.position:
                self.buy()
            else:
                self.close()
