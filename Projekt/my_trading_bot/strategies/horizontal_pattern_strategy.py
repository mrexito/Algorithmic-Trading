import backtrader as bt


class HorizontalPatternStrategy(bt.Strategy):
    params = dict(
        lookback=20,
        stop_loss=0.03,        # 3% Stop-Loss
        take_profit=0.05       # 5% Take-Profit
    )

    def __init__(self):
        self.order = None
        self.buy_price = None

        # Indikatoren
        self.highest = bt.ind.Highest(self.data.high, period=self.p.lookback)
        self.lowest = bt.ind.Lowest(self.data.low, period=self.p.lookback)
        self.rsi = bt.ind.RSI_SMA(self.data.close, period=14)
        self.ma_short = bt.ind.SMA(self.data.close, period=10)
        self.ma_long = bt.ind.SMA(self.data.close, period=50)

    def next(self):
        if self.order:
            return  # warte, bis die Order ausgeführt wurde

        # Kaufbedingung: RSI unter 35, Kurs leicht über jüngstem Tief, positive Dynamik
        if not self.position:
            if self.rsi[0] < 35 and self.data.close[0] > self.lowest[0] * 1.02 and self.ma_short[0] > self.ma_long[0]:
                self.order = self.buy()
                self.buy_price = self.data.close[0]

        # Verkaufsbedingung: Take-Profit oder Stop-Loss erreicht
        elif self.position:
            tp = self.buy_price * (1 + self.p.take_profit)
            sl = self.buy_price * (1 - self.p.stop_loss)

            if self.data.close[0] >= tp or self.data.close[0] <= sl:
                self.order = self.close()
