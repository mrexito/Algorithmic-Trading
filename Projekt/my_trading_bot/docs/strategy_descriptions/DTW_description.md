# Dynamic Time Warping Strategie

Die Dynamic-Time-Warping-(DTW)-Strategie nutzt ein distanzbasiertes Mustererkennungsverfahren, um kurzfristige Trendstrukturen in Kursverläufen zu identifizieren. DTW ermöglicht es, zwei Zeitreihen miteinander zu vergleichen, selbst wenn sie zeitlich gestaucht, gestreckt oder phasenverschoben sind. Dadurch können auch unregelmässige oder „unsauber“ verlaufende Trends erkannt werden, die durch klassische Indikatoren möglicherweise übersehen würden.

## Idee & Setup

Die Strategie vergleicht fortlaufend ein aktuelles Preisfenster – typischerweise bestehend aus den letzten 20 Schlusskursen – mit zwei idealisierten Referenzmustern: einem linearen Aufwärtspfad und einem linearen Abwärtspfad. Die Distanz zwischen dem realen Kursfenster und diesen zwei Referenzsequenzen wird mittels DTW berechnet.

Liegt die DTW-Distanz unterhalb einer definierten Schwelle, signalisiert dies eine strukturelle Ähnlichkeit zum entsprechenden Referenzmuster. Die Schwelle fungiert dabei als Sensitivitätsregler: Kleine Schwellen führen zu wenigen, aber präziseren Signalen; grössere Schwellen erzeugen mehr, dafür weniger selektive Signale.

## Einstiegs-/Ausstiegslogik

Ein Long-Einstieg erfolgt, wenn die DTW-Distanz des aktuellen Kursfensters zum Aufwärts-Referenzpfad unter die definierte Schwelle fällt. Analog wird ein Short-Einstieg ausgelöst, wenn der Kursverlauf deutliche strukturelle Ähnlichkeit mit dem Abwärts-Referenzpfad aufweist.

Positionen werden geschlossen, sobald beide Distanzen über das Doppelte der ursprünglichen Schwelle steigen. Dies deutet darauf hin, dass der zuvor erkannte Trend gebrochen wurde und das Muster nicht mehr zur aktuellen Preisstruktur passt.

Die Logik basiert damit rein auf Musterähnlichkeit und nicht auf starren Preisniveaus oder Indikatorgrenzen.

## Stärken

Die Nutzung von DTW erlaubt es, Trends zu erkennen, die zeitlich unregelmässig verlaufen – zum Beispiel Phasen, in denen ein Trend kurz pausiert, beschleunigt oder eine lokale Konsolidierung bildet. Dadurch eignet sich die Strategie besonders gut für Märkte, in denen strukturelle, aber nicht perfekt lineare Bewegungen auftreten.

Da lediglich zwei Parameter benötigt werden – Fensterlänge und Distanzschwelle – bleibt die Strategie vergleichsweise einfach und resistent gegenüber Overfitting. Gleichzeitig liefert sie einen flexibleren Ansatz als starre Indikatorlogiken.

## Schwächen / Risiken

DTW ist rechnerisch aufwendiger als klassische Indikatoren. Bei hohen Datenfrequenzen oder grossen Fenstergrössen kann dies die Performance beeinträchtigen. Gleichzeitig ist die Strategie empfindlich gegenüber der Wahl von Fenster und Schwelle: Ein zu kleines Fenster reagiert zu nervös, ein zu grosses verwässert kurzfristige Muster; eine falsch gewählte Schwelle führt zu entweder übermässigem oder zu seltenem Trading.

In volatilen Seitwärtsphasen können Fehlsignale gehäuft auftreten, da kurze Ausschläge Musterähnlichkeiten vortäuschen, die sich rasch wieder auflösen. Da die Strategie keine expliziten Schutzmechanismen wie Stops oder Take-Profit-Logiken enthält, muss das Risiko stets durch externe Regeln oder ein separates Portfolio-Risikomanagement begrenzt werden.