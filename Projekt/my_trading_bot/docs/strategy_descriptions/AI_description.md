# AI Strategie

Ein leichtgewichtiges ML-Modell (logistische Regression) trifft Entscheidungen auf Basis von RSI- und SMA-Features und wird bei jedem Schritt mit den letzten Kursbewegungen neu trainiert.

## Idee & Setup
- Features: RSI(14) und SMA(14) auf dem Close.
- Training: Rolling-Re-Train auf dem letzten Fenster (`train_period`, Standard 200 Bars).
- Zielvariable: Nächste Kerze höher als vorherige (1) oder nicht (0).
- Threshold: Long bei `P(up) > 0.55`, Flat bei `P(up) < 0.45`.

## Einstiegs-/Ausstiegslogik
- Einstieg: Wenn keine Position und Modellwahrscheinlichkeit > Schwellenwert.
- Ausstieg: Wenn in Position und Wahrscheinlichkeit unter die Gegen-Schwelle fällt.
- Keine Short-Komponente in der Standardkonfiguration.

## Stärken
- Adaptiv: Modell passt sich laufend an neue Marktphasen an.
- Geringe Komplexität: Wenige Features, schneller Fit (liblinear).

## Schwächen / Risiken
- Datenhungrig: Benötigt ausreichende Historie im Trainingsfenster.
- Instabil bei Seitwärtsmärkten; Overfitting auf kurze Fenster möglich.
- Keine expliziten Stops/TPs – Risiko muss extern gemanagt werden.
