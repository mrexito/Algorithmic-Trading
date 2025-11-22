# SMA Strategie

Die SMA-Strategie gehört zu den einfachsten Formen der Trendfolge und basiert ausschliesslich auf dem Vergleich zwischen aktuellem Schlusskurs und einem einfachen gleitenden Durchschnitt (Simple Moving Average, SMA). Trotz ihrer Einfachheit ist sie ein häufig verwendeter Ansatz, da sie frühe Trendwechsel sichtbar macht und ohne komplexe Parameter auskommt.

## Idee & Setup

Als Indikator dient ein SMA mit einer Periodenlänge von 10 Kerzen. Der kurze Zeitraum sorgt dafür, dass der Durchschnitt schnell auf neue Marktbewegungen reagiert und kurzfristige Trendimpulse früh erkannt werden können. In der Basisversion wird nur die Long-Seite gehandelt, was die Strategie besonders übersichtlich und leicht interpretierbar macht.

## Einstiegs-/Ausstiegslogik

Der Einstieg erfolgt, sobald der Schlusskurs über den SMA(10) steigt. Dies wird als Beginn eines aufwärtsgerichteten Trendimpulses interpretiert. Die Position wird gehalten, solange der Preis oberhalb des Durchschnitts liegt.

Ein Ausstieg erfolgt entsprechend, wenn der Schlusskurs unter den SMA fällt, was auf einen potenziellen Trendbruch oder eine Schwächephase hindeutet. Shorts werden nicht eingesetzt, und es gibt keine integrierten Stop-Loss- oder Take-Profit-Mechanismen.

## Stärken

Die Strategie ist äusserst leicht verständlich, schnell zu implementieren und robust gegenüber einzelnen Ausreissern im Kursverlauf, da der SMA extreme Einzelbewegungen glättet. Durch die kurze Periodenlänge reagiert sie relativ früh auf Trendwechsel und kann dadurch dynamische Aufwärtsbewegungen frühzeitig erfassen.

## Schwächen / Risiken

Eine der grössten Herausforderungen liegt in der hohen Umschlagshäufigkeit, insbesondere in seitwärts gerichteten Marktphasen. Hier kommt es häufig zu Fehlsignalen, da der Kurs wiederholt über und unter den SMA pendelt, ohne einen klaren Trend auszubilden. Zudem ist die Wahl der Periodenlänge entscheidend: Ein zu kurzer SMA reagiert stark auf Marktrauschen, während ein zu langer SMA Trendwechsel erst verzögert abbildet. Die fehlenden Risiko-Management-Regeln machen die Strategie anfällig für drawdowns, sofern kein externes Risikomanagement ergänzt wird.