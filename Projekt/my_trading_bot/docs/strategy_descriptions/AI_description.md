# AI Strategie

Die KI-basierte Handelsstrategie nutzt ein leichtgewichtiges Machine-Learning-Modell, das darauf ausgelegt ist, kurzfristige Kursbewegungen anhand einfacher, aber aussagekräftiger technischer Indikatoren vorherzusagen. Kern der Methode ist eine logistische Regression, die in jedem Zeitschritt neu auf den aktuellsten Marktdaten trainiert wird. Dieser kontinuierliche Re-Train-Prozess ermöglicht es dem Modell, sich dynamisch an veränderte Marktphasen wie Trendwechsel, hohe Volatilität oder Seitwärtsbewegungen anzupassen.

## Idee & Setup

Als Eingangsgroessen dienen der Relative Strength Index (RSI) und ein Simple Moving Average (SMA), jeweils mit einer Periodenlänge von 14 Kerzen. Beide Indikatoren bilden grundlegende Marktdynamiken ab: Der RSI misst kurzfristige Ueberkauft- oder Ueberverkauft-Zustaende, während der SMA Preisschwankungen glättet und strukturelle Trends sichtbar macht.  

Die Zielvariable ist binär formuliert und gibt an, ob die nächste Schlusskerze höher liegt als die vorherige. Damit fungiert das Modell als Klassifikator, der die Wahrscheinlichkeit eines kurzfristigen Aufwärtsimpulses schätzt.

Das Training erfolgt rollierend auf einem definierten Zeitfenster (`train_period`, typischerweise 200 Bars). Dadurch reagiert das Modell schnell auf neue Regime, ohne zu stark auf kurzfristige Ausreisser zu überfitten. Nach jedem Fit berechnet es die Wahrscheinlichkeit eines Kursanstiegs. Überschreitet diese Wahrscheinlichkeit die definierte Schwelle von 0.55, wird eine Long-Position aufgebaut. Faellt die Wahrscheinlichkeit später unter 0.45, wird die Position wieder geschlossen.

## Einstiegs-/Ausstiegslogik

Die Handelslogik folgt klar definierten, deterministischen Regeln:  
- **Einstieg:** Wird keine Position gehalten und die Modellwahrscheinlichkeit übersteigt den Long-Schwellenwert, wird eine Long-Position eröffnet.  
- **Ausstieg:** Befindet sich die Strategie bereits im Markt und die Wahrscheinlichkeit fällt unter die Rückkehrschwelle, erfolgt ein unmittelbareres Schliessen der Position.  

Die Grundversion der Strategie enthält bewusst keine Short-Logik, um Komplexität zu reduzieren und das Verhalten klar interpretierbar zu machen.

## Stärken

Besonders hervorzuheben ist die Adaptivität des Ansatzes. Durch das ständige Retraining passt sich das Modell laufend an neue Marktphasen an. Dies kann insbesondere in volatilen oder trendstarken Perioden zu stabilen Entscheidungen führen. Gleichzeitig ist die verwendete Modellklasse aufgrund ihrer linearen Struktur effizient trainierbar und transparent: Die Gewichtungen der Features sind nachvollziehbar und erlauben eine direkte Interpretation des Modellverhaltens.

Ein weiterer Vorteil ist die robuste Einfachheit. Mit nur zwei Indikatoren wird bewusst ein minimalistisches Feature-Set verwendet, das Überanpassung reduziert und Rechenaufwand minimiert.

## Schwächen / Risiken

Die Strategie ist allerdings in hohem Masse datenabhängig. Das Modell benötigt eine ausreichend lange Historie, um stabile Koeffizienten zu bilden. Zu kurze Trainingsfenster können zu instabilem Verhalten führen, während zu lange Fenster veraltete Marktinformationen einbeziehen könnten.

In Seitwärtsmärkten tendieren probabilistische Klassifikatoren dazu, inkonsistente Signale zu liefern, was die Performance verschlechtern kann. Zudem verzichtet diese Standardkonfiguration auf explizite Risiko-Management-Mechanismen wie Stop-Loss, Take-Profit oder Trailing-Regeln. Ohne zusätzliche Schutzmechanismen ist die Strategie trendfreundlich, jedoch anfällig für plötzliche Marktumschwünge.

Insgesamt bietet die Strategie einen strukturierten, adaptiven und leichtgewichtigen Ansatz, der sich gut als Basisbaustein für komplexere Handelssysteme eignet. Sie kann durch weiterführende Risiko-Management-Regeln oder zusätzliche Features sinnvoll erweitert werden.