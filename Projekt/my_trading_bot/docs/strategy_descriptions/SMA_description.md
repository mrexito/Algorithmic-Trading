# SMA Strategie

Einfache Trendfolge über den Preis relativ zum SMA.

## Idee & Setup
- Indikator: SMA(10) im aktuellen Code (statt eines Kreuzes 50/200).
- Richtung: Nur Long in der Basisvariante.

## Einstiegs-/Ausstiegslogik
- Einstieg: Close > SMA.
- Ausstieg: Close < SMA.
- Kein Short, keine Stops/TPs.

## Stärken
- Extrem einfach, robust gegenüber Ausreißern.
- Greift frühe Trendphasen; kurze Periode reagiert schnell.

## Schwächen / Risiken
- Hohe Umschlagshäufigkeit in Seitwärtsmärkten.
- Fehlersensitiv auf die gewählte Periode; zu kurz = Noise, zu lang = spät.
