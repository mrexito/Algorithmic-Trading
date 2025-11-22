"""Range-trading strategy that looks for horizontal support/resistance bounces."""

import backtrader as bt


class HorizontalPatternStrategy(bt.Strategy):
    """Buy near recent lows with supporting momentum and exit on TP/SL touches."""

    params = dict(
        lookback=20, stop_loss=0.03, take_profit=0.05  # 3% Stop-Loss  # 5% Take-Profit
    )

    def __init__(self):
        """Precompute indicators used for detecting range conditions."""
        self.order = None
        self.buy_price = None

        # Indikatoren
        self.highest = bt.ind.Highest(self.data.high, period=self.p.lookback)
        self.lowest = bt.ind.Lowest(self.data.low, period=self.p.lookback)
        self.rsi = bt.ind.RSI_SMA(self.data.close, period=14)
        self.ma_short = bt.ind.SMA(self.data.close, period=10)
        self.ma_long = bt.ind.SMA(self.data.close, period=50)

    def next(self):
        """Issue buy/sell orders when the horizontal pattern criteria are met."""
        if self.order:
            return  # wait for the pending order to settle

        # Entry condition: RSI below 35, price slightly above the recent low, positive momentum
        if not self.position:
            if (
                self.rsi[0] < 35
                and self.data.close[0] > self.lowest[0] * 1.02
                and self.ma_short[0] > self.ma_long[0]
            ):
                self.order = self.buy()
                self.buy_price = self.data.close[0]

        # Exit condition: take-profit or stop-loss hit
        elif self.position:
            tp = self.buy_price * (1 + self.p.take_profit)
            sl = self.buy_price * (1 - self.p.stop_loss)

            if self.data.close[0] >= tp or self.data.close[0] <= sl:
                self.order = self.close()
