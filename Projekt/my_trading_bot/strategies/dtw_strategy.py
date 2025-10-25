import backtrader as bt
import numpy as np
from dtaidistance import dtw


class DTWStrategy(bt.Strategy):
    params = dict(window=20, threshold=5.0)

    def __init__(self):
        self.dataclose = self.datas[0].close

    def next(self):
        if len(self.dataclose) <= self.p.window:
            return

        # Aktuelles Zeitfenster
        recent = np.array([self.dataclose[-i] for i in reversed(range(self.p.window))])

        # Lineares Referenzmuster (z. B. Aufwärts- oder Abwärtstrend)
        pattern_up = np.linspace(recent[0], recent[-1], num=self.p.window)
        pattern_down = np.linspace(recent[-1], recent[0], num=self.p.window)

        # Berechne DTW-Distanzen
        dist_up = dtw.distance(recent, pattern_up)
        dist_down = dtw.distance(recent, pattern_down)

        if not self.position:
            if dist_up < self.p.threshold:
                self.buy()
            elif dist_down < self.p.threshold:
                self.sell()
        else:
            # Schließe Position bei stark abweichendem Verlauf
            if dist_up > self.p.threshold * 2 and dist_down > self.p.threshold * 2:
                self.close()
