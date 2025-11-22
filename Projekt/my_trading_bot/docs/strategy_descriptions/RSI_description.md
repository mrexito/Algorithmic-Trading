# RSI Strategie

Die RSI-Strategie basiert auf dem Mean-Reversion-Prinzip und nutzt den Relative Strength Index (RSI), um kurzfristige Übertreibungen im Markt zu identifizieren. Der RSI misst das Verhältnis von durchschnittlichen Aufwärts- und Abwärtsbewegungen über eine definierte Periodenlänge und ordnet den Markt in einen Skalenbereich zwischen 0 und 100 ein. Bereiche unterhalb von 30 gelten als überverkauft, während Werte über 70 eine überkaufte Marktsituation signalisieren. Die Strategie nutzt diese Extremzonen für antizyklische Einstiege und Ausstiege.

## Idee & Setup

Verwendet wird ein RSI mit einer Periodenlänge von 14, berechnet auf Basis der Schlusskurse – ein etablierter Standard in der technischen Analyse. Die Regeln sind bewusst minimalistisch gehalten: Ein Einstieg erfolgt bei klar überverkauften Situationen, ein Ausstieg bei überkauften Bedingungen. Die Parameter 30 und 70 gelten als robuste Schwellenwerte, können jedoch je nach Marktcharakteristik angepasst werden.

## Einstiegs-/Ausstiegslogik

Ein Long-Einstieg wird ausgelöst, sobald der RSI unter die Marke von 30 fällt. Dies wird als Zeichen interpretiert, dass der Markt kurzfristig zu stark gefallen ist und ein technischer Rebound wahrscheinlich erscheinen könnte.

Der Ausstieg erfolgt symmetrisch, sobald der RSI über 70 steigt. Dies deutet darauf hin, dass die Erholung abgeschlossen sein könnte und das Gewinnpotenzial begrenzt ist. Die Basisstrategie verzichtet bewusst auf Short-Positionen sowie auf Stop-Loss- oder Take-Profit-Regeln und verlässt sich ausschliesslich auf die RSI-Schwellen zur Positionssteuerung.

## Stärken

Der RSI liefert klare und gut interpretierbare Signale. Da die Strategie nur einen einzigen Indikator nutzt, ist sie äusserst einfach umzusetzen, schnell zu testen und kaum anfällig für Überoptimierung. In volatilen Seitwärtsmärkten erzeugt der RSI regelmässig gut verwertbare Mean-Reversion-Signale, was zu einer hohen Signaldichte führen kann. Die Standardparameter 14/30/70 sind seit Jahrzehnten erprobt und gelten als robust.

## Schwächen / Risiken

In stark ausgeprägten Abwärtstrends kann der RSI über längere Zeit im überverkauften Bereich verharren, weshalb ein frühes Kaufen ohne Schutzmechanismen zu deutlichen Drawdowns führen kann. Da die Strategie keine Stops integriert, ist das Risiko unlimitiert und muss extern verwaltet werden. Trendfilter – etwa gleitende Durchschnitte – können sinnvoll sein, um Einstiege gegen dominante Abwärtstrends zu vermeiden.

Generell ist der RSI anfällig für Fehlsignale in dynamischen Trendphasen, da Mean-Reversion-Impulse seltener auftreten oder zu spät einsetzen.