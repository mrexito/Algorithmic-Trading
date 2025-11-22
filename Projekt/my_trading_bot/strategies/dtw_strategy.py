"""Dynamic Time Warping strategy that matches price paths to reference patterns."""

import backtrader as bt
import numpy as np
from dtaidistance import dtw


class DTWStrategy(bt.Strategy):
    """Enter trades when recent windows resemble up or down reference paths."""

    params = dict(window=20, threshold=5.0)

    def __init__(self):
        """Store a reference to the close series for repeated window extraction."""
        self.dataclose = self.datas[0].close

    def next(self):
        """Compare the latest window with templates and trade when similarity is high."""
        if len(self.dataclose) <= self.p.window:
            return

        # Current price window
        recent = np.array([self.dataclose[-i] for i in reversed(range(self.p.window))])

        # Linear reference patterns (e.g., uptrend/downtrend paths)
        pattern_up = np.linspace(recent[0], recent[-1], num=self.p.window)
        pattern_down = np.linspace(recent[-1], recent[0], num=self.p.window)

        # Compute DTW distances to templates
        dist_up = dtw.distance(recent, pattern_up)
        dist_down = dtw.distance(recent, pattern_down)

        if not self.position:
            if dist_up < self.p.threshold:
                self.buy()
            elif dist_down < self.p.threshold:
                self.sell()
        else:
            # Close the position when the path diverges sharply from both templates
            if dist_up > self.p.threshold * 2 and dist_down > self.p.threshold * 2:
                self.close()
