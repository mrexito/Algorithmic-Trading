# RSI Strategie

Mean-Reversion-Ansatz auf Basis des RSI: Kauf bei Überverkauft, Ausstieg bei Überkauft.

## Idee & Setup
- Indikator: RSI(14) auf Schlusskursbasis.
- Schwellen: Einstieg < 30, Ausstieg > 70.

## Einstiegs-/Ausstiegslogik
- Einstieg Long: RSI fällt unter 30 (überverkauft).
- Ausstieg: RSI steigt über 70 (überkauft).
- Keine Short-Logik, keine Stops/TPs integriert.

## Stärken
- Klare, bekannte Schwellen; gute Signaldichte in volatilen Ranges.
- Wenige Parameter, leicht anpassbar.

## Schwächen / Risiken
- In starken Abwärtstrends kann „überverkauft“ lange anhalten.
- Ohne Stops potenziell tiefe Drawdowns; Trendfilter kann hilfreich sein.
