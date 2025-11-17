# Dynamic Time Warping Strategie

Vergleicht das aktuelle Kursfenster per Dynamic Time Warping (DTW) mit einfachen Referenzmustern und handelt, wenn die Distanz klein ist.

## Idee & Setup
- Fenster: Letzte N Schlusskurse (`window`, Standard 20).
- Referenzen: Lineare Auf-/Abwärtslinien zwischen Start/Ende des Fensters.
- Metrik: DTW-Distanz; Schwelle (Standard 5.0) steuert Auslösungen.

## Einstiegs-/Ausstiegslogik
- Einstieg Long: DTW-Distanz zum Aufwärts-Referenzpfad < Schwelle.
- Einstieg Short: Distanz zum Abwärts-Referenzpfad < Schwelle.
- Ausstieg: Beide Distanzen überschreiten das Doppelte der Schwelle (starker Bruch des Musters).

## Stärken
- Musterbasiert: Erkennt unsauber gestreckte Trends (DTW erlaubt zeitliche Verzerrung).
- Parameterfrei bis auf Fenster & Schwelle.

## Schwächen / Risiken
- DTW ist rechenintensiver; sensibel auf Wahl von `window` und Schwelle.
- Kann in volatilen Seitwärtsmärkten häufige Fehlsignale produzieren.
- Keine Stops/TPs; Risiko muss extern begrenzt werden.
