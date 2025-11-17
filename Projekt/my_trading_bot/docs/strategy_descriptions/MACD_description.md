# MACD Strategie

Momentum-/Trendfolge über das Vorzeichen des MACD-Histogramms.

## Idee & Setup
- Indikator: Standard-MACD (12/26 EMAs) mit Signal (9er EMA).
- Signalquelle: Histogramm = MACD – Signal.

## Einstiegs-/Ausstiegslogik
- Einstieg Long: Histogramm > 0 (MACD über Signal).
- Ausstieg: Histogramm < 0.
- Keine Shorts in der Basisversion.

## Stärken
- Solider Trendfolger mit wenig Parametern.
- Glättet Rauschen durch doppelte EMAs.

## Schwächen / Risiken
- Nachlaufender Indikator; Wendepunkte werden verzögert erkannt.
- Whipsaws in Range-Märkten möglich.
