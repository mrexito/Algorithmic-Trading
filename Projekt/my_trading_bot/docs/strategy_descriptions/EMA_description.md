# EMA (12/26) Strategie

Die EMA-(12/26)-Strategie gehört zu den klassischen Trendfolgeansätzen und basiert auf der Interaktion zweier exponentieller gleitender Durchschnitte. Exponentielle Durchschnitte gewichten aktuelle Kursdaten stärker als ältere Werte und reagieren daher schneller auf neue Marktbewegungen als einfache gleitende Durchschnitte. Die Strategie nutzt dieses Verhalten, um entstehende Trends frühzeitig zu erkennen und trendkonform zu handeln.

## Idee & Setup

Die Strategie verwendet zwei EMAs:  
- einen kurzfristigen EMA mit Periode 12  
- einen mittelfristigen EMA mit Periode 26  

Beide basieren auf Schlusskursen. Die Grundidee besteht darin, dass ein Trend entsteht, sobald der schnellere Durchschnitt den langsameren überschreitet. Diese „Crossover“-Logik signalisiert eine strukturelle Trendverschiebung nach oben oder unten. In der Standardvariante wird jedoch ausschliesslich Long gehandelt, wodurch die Strategie bewusst vereinfacht und robuster gehalten wird.

## Einstiegs-/Ausstiegslogik

Ein Long-Einstieg erfolgt, sobald der EMA(12) den EMA(26) von unten nach oben kreuzt. Dieser Moment wird als Beginn eines neuen Aufwärtstrends interpretiert. Solange der kurzfristige Durchschnitt oberhalb des langfristigen liegt, bleibt die Position bestehen.

Sobald der EMA(12) unter den EMA(26) fällt, wird die Position geschlossen. Dadurch steigt die Strategie aus, wenn der Trend an Dynamik verliert oder eine markante Umkehr stattfindet. Shorts werden in der Standardkonfiguration nicht eingesetzt, sodass Signale in Trendphasen klar und einfach bleiben.

## Stärken

Exponentielle Durchschnitte reagieren schneller als SMAs und ermöglichen dadurch ein zeitnahes Erkennen von Trendwechseln. Gleichzeitig wirken sie glättend und reduzieren die Auswirkungen einzelner Ausreisser im Kursverlauf. Die Crossover-Logik ist intuitiv, seit Jahrzehnten erprobt und in vielen Märkten anwendbar. Sie funktioniert besonders gut in klaren Trendphasen mit mittlerer bis hoher Momentumstärke.

Da die Strategie nur zwei Parameter benötigt – die Periodenlängen – ist sie weniger anfällig für Überoptimierung und kann ohne grosse Anpassungen auf verschiedene Basiswerte angewendet werden.

## Schwächen / Risiken

Wie alle Trendfolgestrategien leidet auch die EMA-(12/26)-Variante in ausgeprägten Seitwärtsmärkten. Hier entstehen häufige Richtungswechsel der Durchschnitte, was zu vielen Ein- und Ausstiegen führt („Whipsaws“). Dies kann nicht nur die Performance beeinträchtigen, sondern auch die Transaktionskosten erhöhen.

Der EMA selbst ist ein nachlaufender Indikator. Wendepunkte werden daher regelmässig verspätet erkannt, wodurch ein Teil der Bewegung vor dem Einstieg bereits stattgefunden hat. Ebenso können späte Ausstiege in fallenden Märkten zu schmerzhaften Drawdowns führen. Da weder Stop-Loss noch Take-Profit-Regeln integriert sind, muss die Risikobegrenzung zwingend extern ergänzt werden.