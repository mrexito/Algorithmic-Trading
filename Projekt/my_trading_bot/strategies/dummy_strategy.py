"""Placeholder strategy that alternates positions on a fixed cadence."""

import backtrader as bt


class DummyStrategy(bt.Strategy):
    """Flip between long and flat every few bars to act as a test harness."""

    def __init__(self):
        """Set up a simple counter for spacing trades."""
        self.counter = 0

    def next(self):
        """Toggle positions every tenth bar to simulate trade flow."""
        self.counter += 1
        if self.counter % 10 == 0:
            if not self.position:
                self.buy()
            else:
                self.close()
