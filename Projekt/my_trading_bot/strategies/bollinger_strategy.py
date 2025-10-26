"""Bollinger Band mean-reversion strategy."""

import backtrader as bt


class BollingerStrategy(bt.Strategy):
    """Fade moves beyond the bands and exit when price reverts to the mean."""

    params = dict(period=20, devfactor=2.0)

    def __init__(self):
        """Set up the Bollinger Band indicator and internal order tracking."""
        self.bbands = bt.indicators.BollingerBands(
            self.datas[0].close, period=self.p.period, devfactor=self.p.devfactor
        )
        self.order = None

    def next(self):
        """Enter long when price pierces the lower band and exit near the middle."""
        if self.order:
            return  # Warte, bis bestehender Auftrag ausgeführt ist

        # Kaufsignal: Schlusskurs unter dem unteren Band
        if not self.position and self.datas[0].close[0] < self.bbands.bot[0]:
            self.order = self.buy()

        # Verkaufssignal: Schlusskurs über mittlerem Band (SMA)
        elif self.position and self.datas[0].close[0] > self.bbands.mid[0]:
            self.order = self.close()

    def notify_order(self, order):
        """Reset pending order state once Backtrader reports final status."""
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None
