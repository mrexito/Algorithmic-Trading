# ZigZag Strategie

Reagiert auf prozentuale Schwingungen (ZigZag) und wechselt Trades bei Trendwechseln über eine definierte Schwelle.

## Idee & Setup
- Pivots: Letzter Extrempunkt wird gemerkt.
- Schwelle: Prozentuale Bewegung seit Pivot (`perc`, Standard 5 %) löst Aktion aus.
- Positionierung: Long bei Aufwärtsbruch, Short bei Abwärtsbruch; Wechsel bei Umkehr.

## Einstiegs-/Ausstiegslogik
- Einstieg Long: Preis > letzter Pivot um mindestens `perc` %.
- Einstieg Short: Preis < letzter Pivot um mindestens `perc` %.
- Ausstieg/Wechsel: Gegenbewegung um `perc` % triggern Positionsschließung und Richtungswechsel.

## Stärken
- Klare Schwellen; filtert kleine Bewegungen heraus.
- Funktioniert in trendstarken Phasen mit ausgedehnten Swings.

## Schwächen / Risiken
- In choppy Märkten häufige Richtungswechsel.
- Keine Stops/TPs; Risiko muss separat kontrolliert werden.
