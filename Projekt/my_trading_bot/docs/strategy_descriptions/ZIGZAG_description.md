# ZigZag Strategie

Die ZigZag-Strategie nutzt prozentuale Kursbewegungen, um markante Trendwechsel zu identifizieren und darauf basierend zwischen Long- und Short-Positionen zu wechseln. Der Ansatz filtert kleinere Kursrauschbewegungen heraus und konzentriert sich bewusst auf grössere prozentuale Schwünge. Dadurch eignet sich die Strategie besonders für Märkte, die in klaren, gut ausgeprägten Swings verlaufen.

## Idee & Setup

Die Strategie speichert fortlaufend den letzten relevanten Extrempunkt (Pivot), entweder ein lokales Hoch oder Tief. Ein Trendbruch wird dann angenommen, sobald der Kurs sich relativ zu diesem Pivot um einen definierten Prozentsatz bewegt. Dieser Schwellenwert (`perc`) beträgt standardmässig 5 %, kann jedoch je nach Volatilität des Basiswertes angepasst werden.

Die Positionierung erfolgt entsprechend der Bewegungsrichtung:
- Ein Bruch nach oben erzeugt ein Long-Signal.
- Ein Bruch nach unten erzeugt ein Short-Signal.
- Jede neue Gegenbewegung um mindestens `perc` % führt zu einem vollständigen Positionswechsel.

Dieser Mechanismus bildet die klassische Funktionsweise des bekannten ZigZag-Indikators nach, jedoch mit aktiver Umsetzung im Trading.

## Einstiegs-/Ausstiegslogik

Ein Long-Einstieg erfolgt, sobald der Preis den letzten Pivot nach oben um mindestens `perc` % übersteigt. Analog wird ein Short-Signal generiert, wenn der Kurs den letzten Pivot nach unten um mindestens `perc` % unterschreitet.

Kommt es später zu einer Bewegung in die entgegengesetzte Richtung und überschreitet diese ebenfalls die definierte Schwelle, wird die bestehende Position geschlossen und unmittelbar eine Position in die Gegenrichtung eröffnet. Das System reagiert damit strikt auf Trendwechsel und bleibt nie flat, solange aktive Signale vorhanden sind.

## Stärken

Die Strategie besitzt eine klare und transparente Logik. Durch die prozentuale Schwellensteuerung werden kleine Schwankungen ignoriert und nur bedeutsame Marktbewegungen verarbeitet. In trendstarken Märkten oder in Assets mit grossen zyklischen Schwüngen kann die ZigZag-Strategie daher sehr effizient sein. Der feste Schwellenwert macht die Methode zudem einfach parametrisierbar und gut vergleichbar.

## Schwächen / Risiken

In volatilen Seitwärtsmärkten führt der Ansatz oft zu vielen Richtungswechseln, da der Kurs mehrfach die gleiche Schwelle über- und unterschreiten kann, ohne einen stabilen Trend auszubilden. Dadurch kann die Strategie unter choppy conditions deutliche Verluste erleiden.

Da weder Stop-Loss noch Take-Profit integriert sind, muss das Risikomanagement extern abgedeckt werden. Zudem kann die Wahl des `perc`-Werts entscheidend sein: Ein zu kleiner Wert erzeugt viele Fehlsignale, während ein zu grosser Wert potenziell profitable Trendphasen verspätet erkannt werden lässt.