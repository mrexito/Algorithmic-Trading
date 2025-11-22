# MACD Strategie

Die MACD-Strategie (Moving Average Convergence Divergence) gehört zu den etablierten Momentum- und Trendfolgeansätzen und kombiniert Informationen aus zwei exponentiellen gleitenden Durchschnitten. Im Zentrum steht das MACD-Histogramm, das den Abstand zwischen MACD-Linie und Signallinie darstellt und damit die Stärke sowie die Dynamik eines Trends abbildet. Die Strategie nutzt das Vorzeichenwechsel des Histogramms, um Trendwechsel zu erkennen und entsprechend Long-Positionen einzugehen oder zu schliessen.

## Idee & Setup

Der MACD basiert auf zwei EMAs unterschiedlicher Länge:  
- **EMA(12)** – schneller Durchschnitt  
- **EMA(26)** – langsamer Durchschnitt  

Die Differenz dieser beiden bildet die **MACD-Linie**. Anschliessend wird ein weiterer EMA, typischerweise mit Periode 9, als **Signallinie** darüber gelegt. Das daraus resultierende **Histogramm (MACD – Signal)** visualisiert die Trenddynamik: positive Werte deuten auf steigendes Momentum, negative auf fallendes.

Diese Standardparameter (12/26/9) sind seit Jahrzehnten im Einsatz und gelten als robust über verschiedene Märkte und Zeitrahmen hinweg.

## Einstiegs-/Ausstiegslogik

Ein Long-Einstieg erfolgt, sobald das Histogramm in den positiven Bereich wechselt, also die MACD-Linie über die Signallinie steigt. Dies wird als Beginn einer neuen Aufwärtsbewegung interpretiert. Solange das Histogramm über null bleibt, wird die Position gehalten.

Ein Ausstieg erfolgt, sobald das Histogramm wieder unter null fällt. Dieser Moment signalisiert, dass das Aufwärtsmomentum nachlässt oder sich eine Umkehr anbahnen könnte. Short-Positionen werden in der Basisversion nicht gehandelt.

## Stärken

Der MACD zählt zu den zuverlässigsten Trendfolgern im technischen Handel. Durch die Kombination zweier EMAs sowie einer zusätzlichen Glättung über die Signallinie reduziert der Indikator Rauschen und liefert klar interpretierbare Signale. Da nur wenige Parameter verwendet werden, ist das Modell relativ robust gegenüber Überoptimierung. Zudem erfasst das Histogramm nicht nur Trendrichtung, sondern auch Trendstärke.

## Schwächen / Risiken

Ein wesentlicher Nachteil liegt in der Nachlaufnatur des MACD: Da mehrere EMAs zum Einsatz kommen, werden Wendepunkte häufig erst verspätet erkannt. Dies führt dazu, dass ein Teil der Bewegung vor dem Einstieg bereits stattgefunden hat oder Ausstiege erst erfolgen, wenn ein grosser Teil des Trends bereits verloren wurde.

In seitwärts orientierten Märkten treten Whipsaws auf, also häufige Richtungswechsel des Histogramms, die zu schnellen Ein- und Ausstiegen ohne nennenswerten Trend führen. Ohne zusätzliche Filter kann dies die Performance reduzieren. Da die Strategie keine integrierten Risikoregeln wie Stops oder TPs enthält, muss das Risiko extern begrenzt werden.