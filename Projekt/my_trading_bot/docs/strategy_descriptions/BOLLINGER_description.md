# Bollinger Bands Strategie

Klassische Mean-Reversion: Kauf bei Überdehnung unter das untere Bollinger Band, Ausstieg beim Rücklauf zum Mittelband.

## Idee & Setup
- Indikator: Bollinger Bänder mit Periode 20, Standardabweichungsfaktor 2.0.
- Handelsrichtung: Nur Long in der Standard-Implementierung.

## Einstiegs-/Ausstiegslogik
- Einstieg (Long): Schlusskurs unter dem unteren Band.
- Ausstieg: Schlusskurs zurück über das mittlere Band (SMA).
- Keine Shorts, keine expliziten Stops/TPs.

## Stärken
- Nutzt kurzfristige Überdehnung und mean reversion.
- Wenige Parameter, robuste Standardwerte.

## Schwächen / Risiken
- In starken Trends werden Kontra-Trades gefangen.
- Ohne Stop-Loss können Drawdowns lange anhalten.
- Sensitiv auf die Bandbreite; falscher `devfactor` führt zu Over-/Under-Trading.
