# Bollinger Bands Strategie

Die Bollinger-Band-Strategie gehoert zu den klassischen Mean-Reversion-Ansätzen und nutzt statistische Ueberdehnungen des Preises als Einstiegspunkt für antizyklische Trades. Die Grundidee besteht darin, dass starke Abweichungen vom gleitenden Durchschnitt meist nicht nachhaltig sind und der Kurs tendenziell zu seinem Mittelwert zurückkehrt. Bollinger Bänder bilden diese Ueber- und Untertreibungen ab, indem sie die Volatilität direkt in die Breite der Bänder einbeziehen.

## Idee & Setup

Die Strategie verwendet Bollinger Bänder mit einer Periodenlänge von 20 Kerzen sowie einem Standardabweichungsfaktor von 2.0. Die Bänder bestehen aus einem mittleren SMA, einem oberen Band (SMA + 2 × Standardabweichung) und einem unteren Band (SMA – 2 × Standardabweichung). Durch diese Konstruktion passen sich die Bänder automatisch an die aktuelle Marktvolatilität an: In ruhigen Phasen werden sie eng, in volatilen Phasen erweitern sie sich.

Gehandelt wird in der Standardvariante ausschliesslich auf der Long-Seite. Dies reduziert die Komplexität und fokussiert die Strategie auf die Erholung nach kurzfristigen Übertreibungen nach unten.

## Einstiegs-/Ausstiegslogik

Ein Long-Einstieg erfolgt, sobald der Schlusskurs unter das untere Bollinger Band fällt. In diesem Moment wird davon ausgegangen, dass der Preis statistisch aussergewöhnlich stark gefallen ist und eine Rückkehr in Richtung Mittelband wahrscheinlich wird.

Der Ausstieg erfolgt beim Rücklauf über das mittlere Band (SMA 20). Damit wird der Mean-Reversion-Gedanke sauber umgesetzt: Einstieg in der Ueberdehnung, Ausstieg in der Normalisierung.

Short-Positionen werden bewusst nicht eingesetzt, ebenso wenig wie explizite Stop- oder Take-Profit-Marken. Der gesamte Handelszyklus wird rein durch die Interaktion des Preises mit den Bändern gesteuert.

## Stärken

Die Strategie profitiert besonders in seitwärts tendierenden Märkten oder in schwachen Trendphasen, in denen Übertreibungen regelmässig zurücklaufen. Da Bollinger Bänder auf statistisch gut etablierten Parametern basieren, sind die Standardwerte (20 Perioden, 2.0 Standardabweichungen) robust und in vielen Märkten ohne exzessive Optimierung einsetzbar.

Die Implementierung ist einfach, transparent und ressourcenschonend. Es gibt nur wenige Parameter, wodurch die Strategie resistenter gegen Overfitting ist als komplexe Modelle.

## Schwächen / Risiken

Mean-Reversion-Strategien sind grundsätzlich anfällig für starke Trendphasen. Wird ein Abwärtstrend dynamisch und anhaltend, kann die Strategie mehrfach in fallende Märkte hinein kaufen, während der erwartete Rücklauf ausbleibt. Ohne Stop-Loss-Mechanismen können Drawdowns dadurch länger andauern und tiefer ausfallen.

Ein weiterer kritischer Faktor ist die Bandbreite. Ein zu kleiner Standardabweichungsfaktor führt zu häufigen Fehlsignalen, während ein zu grosser Faktor sinnvolle Einstiege verzögert oder komplett ausfiltern kann. Insgesamt ist die Strategie daher empfindlich gegenüber Marktregimen: Sie funktioniert gut in stabilen oder seitwärtsorientierten Phasen, aber schlecht in Momentum-Märkten, die gegen den Mean-Reversion-Ansatz laufen.