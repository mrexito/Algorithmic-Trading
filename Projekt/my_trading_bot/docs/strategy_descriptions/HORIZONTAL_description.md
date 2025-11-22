# Horizontale Muster Strategie

Die Strategie für horizontale Muster fokussiert auf das Handeln von Kursbewegungen innerhalb klar definierter Seitwärtsphasen. Sie nutzt typische Range-Verhalten, bei dem Kurse wiederholt an lokalen Tiefs abprallen und zur oberen Begrenzung zurücklaufen. Um Fehlsignale zu vermeiden, kombiniert die Strategie Preisbereiche mit zusätzlichen Momentum- und Trendfiltern sowie einem festen Chance-Risiko-Verhältnis über Stop-Loss und Take-Profit.

## Idee & Setup

Das Grundprinzip besteht darin, lokale Tiefpunkte als temporäre Unterstützungszonen zu interpretieren. Wenn der Kurs in deren Nähe erneut nach oben dreht, entsteht ein potenzielles Bounce-Signal. Zur Identifikation dieser Bereiche wird ein Lookback-Fenster von 20 Kerzen genutzt, innerhalb dessen die jüngsten Hoch- und Tiefpunkte bestimmt werden.

Die Strategie kombiniert diese Zonen mit zwei Filtern:
- **Momentum-Filter:** RSI(14) < 35, um überverkaufte Situationen zu erkennen.
- **Trendfilter:** Der kurzfristige gleitende Durchschnitt (MA10) muss oberhalb des langfristigen Durchschnitts (MA50) liegen, was einen leichten Aufwärtsbias signalisiert.

Das Risiko-Management ist klar strukturiert: Ein Stop-Loss von 3 % unterhalb des Einsteigekurses begrenzt Verluste, während ein Take-Profit von 5 % ein definiertes Gewinnziel vorgibt.

## Einstiegs-/Ausstiegslogik

Ein Long-Einstieg erfolgt, wenn der RSI unter 35 fällt, der Kurs sich innerhalb eines engen Bereichs über dem jüngsten markanten Tief befindet (typisch maximal ca. 2 % darüber) und gleichzeitig der MA10 über dem MA50 liegt. Diese Kombination stellt sicher, dass nicht blind in fallende Märkte gekauft wird, sondern nur dann, wenn ein überverkaufter Zustand in einem leicht positiven Marktumfeld auftritt.

Die Position wird ausschliesslich über die vorab definierten Risikoparameter geschlossen. Ein Take-Profit von 5 % realisiert Gewinne, während ein Stop-Loss von 3 % das Risiko strikt begrenzt. Shorts werden nicht gehandelt, wodurch die Strategie klar auf Erholungsbewegungen in Seitwärtsmärkten ausgerichtet bleibt.

## Stärken

Die Strategie folgt einem strukturierten Range-Trading-Ansatz mit klar definiertem Chance-Risiko-Verhältnis. Durch die Kombination aus Preisniveau, RSI-basiertem Momentum und gleitenden Durchschnitten werden unvorteilhafte Käufe reduziert, insbesondere solche, die gegen starke Abwärtstrends gerichtet wären. Die feste TP/SL-Logik macht das Verhalten der Strategie transparent, reproduzierbar und gut analysierbar.

## Schwächen / Risiken

In stark trendenden Märkten funktioniert der Ansatz nur begrenzt. Bei dynamischen Abwärtsbewegungen kann der Kurs Unterstützungen nach unten durchbrechen, bevor die Strategie die Möglichkeit zur Anpassung hat. Zudem sind TP und SL relativ eng gesetzt, was in volatilen Phasen zu häufigen Ausstoppern führen kann.

Da die Signale stark von Lookback-Fenster, Trendfiltern und der Nähe zum letzten Tief abhängen, ist die Strategie empfindlich gegenüber Parameterwahl und Marktregimen. Da ausschliesslich Long gehandelt wird, sind Phasen mit klaren Abwärtstrends praktisch unhandelbar.