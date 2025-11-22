# Buy & Hold

Die Buy-&-Hold-Strategie bildet die schlichteste und gleichzeitig fundamentalste Form des Investierens ab. Sie dient im quantitativen Trading häufig als neutrale Benchmark, um die Wertschöpfung aktiver Strategien objektiv zu beurteilen. Der Grundgedanke ist einfach: Anstatt Marktbewegungen aktiv zu timen, wird ein Basiswert einmal gekauft und über den gesamten Betrachtungszeitraum hinweg gehalten.

## Idee & Setup

Die zugrunde liegende Annahme ist, dass Finanzmärkte langfristig einem strukturellen Aufwärtstrend folgen – sei es aufgrund von Wirtschaftswachstum, Inflation oder Gewinnsteigerungen der Unternehmen. Buy & Hold verzichtet bewusst auf jede Form der taktischen oder technischen Steuerung und nutzt dadurch die reine Marktentwicklung als Renditetreiber.

Operativ besteht die Strategie darin, zu Beginn des Testzeitraums eine Position aufzubauen und diese bis zum Ende unverändert zu halten. Es werden weder zusätzliche Käufe noch Verkäufe durchgeführt. Rebalancing findet nicht statt, ebenso erfolgt keine Hebelung. Dividendenausschüttungen können zwar in der Praxis reinvestiert werden, werden im Standardmodell jedoch nicht berücksichtigt.

## Handelslogik

Die Logik ist vollständig deterministisch und nicht signalbasiert:
- **Einstieg:** Eine fixe Long-Position wird zum Startzeitpunkt eröffnet.  
- **Halten:** Die Position bleibt während der gesamten Laufzeit unverändert bestehen.  
- **Ausstieg:** Ausschliesslich am Ende des Untersuchungszeitraums wird die Position geschlossen oder bilanziert.  

Die Strategie ist dadurch frei von Markt-Timing und reagiert nicht auf Zwischenereignisse, Trends, Volatilität oder fundamentale Entwicklungen.

## Stärken

Buy & Hold ist extrem effizient in der Umsetzung und verursacht minimale Transaktionskosten, da nur zwei Trades (Kauf und Verkauf) anfallen. Die Strategie profitiert direkt von längeren Aufwärtsphasen und partizipiert vollständig an der langfristigen Marktrendite. Da es keine Parameter gibt, ist die Strategie unempfindlich gegenüber Modellfehlern oder Überoptimierung. Sie stellt zudem eine ideale Referenz dar, um aktive Strategien vergleichbar zu machen.

## Schwächen / Risiken

Die Einfachheit birgt gleichzeitig erhebliche Risiken. Ohne Stop-Loss- oder Risikomanagement-Mechanismen ist die Strategie vollständig dem Marktrisiko ausgesetzt. In Einbrüchen, Seitwärtsphasen oder strukturell fallenden Märkten kann dies zu langen Drawdowns führen, die Jahre dauern können. Buy & Hold setzt implizit voraus, dass der betrachtete Markt langfristig steigt. Für Einzelaktien, volatile Sektoren oder nicht wachsende Märkte kann diese Annahme jedoch stark eingeschränkt sein.

Zudem bietet die Strategie keinerlei Mechanismen zur Optimierung von Kapitaleinsatz, Volatilität oder Risikoadjustierung. In Märkten ohne klaren, langfristigen Aufwärtspfad kann Buy & Hold im Vergleich zu aktiven Strategien deutlich unterperformen.