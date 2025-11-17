# Horizontale Muster Strategie

Range-/Bounce-Ansatz: Sucht Käufe nahe lokaler Tiefs in Seitwärtsphasen und schließt über TP/SL.

## Idee & Setup
- Lookback: Letzte 20 Kerzen für lokale Hochs/Tiefs.
- Momentum-Filter: RSI(14) < 35 (überverkauft) und MA10 > MA50 (leichter Aufwärtsbias).
- Risiko-Management: Stop-Loss 3 %, Take-Profit 5 % ab Entry.

## Einstiegs-/Ausstiegslogik
- Einstieg Long: RSI < 35, Kurs knapp über jüngstem Tief (~2 %), kurzfristiger MA über langfristigem MA.
- Ausstieg: Take-Profit oder Stop-Loss erreicht.
- Keine Shorts vorgesehen.

## Stärken
- Klare Regeln für Range-Bounces mit festem CRV (TP/SL).
- Kombination aus Preis- und Momentum-Filter reduziert Blindkäufe.

## Schwächen / Risiken
- Funktioniert schlecht in starken Trends (TP/SL können eng sein).
- Signal hängt von Lookback-Parametern und MA-Filter ab.
- Nur Long-Seite; keine Trades bei Abwärtstrends.
