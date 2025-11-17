# EMA (12/26)

**Idee:** Trendfolge über zwei exponentielle Durchschnitte. Geht long, wenn der kurzfristige EMA (12) über dem langfristigen EMA (26) liegt.

**Setup & Logik:**
- Indikatoren: EMA(12) und EMA(26) auf Schlusskursbasis.
- Einstieg: Long, wenn EMA(12) > EMA(26).
- Ausstieg: Flat, wenn EMA(12) < EMA(26).
- Kein Short-Modus in der Standardvariante.

**Stärken:**
- Schnelleres Reagieren auf Trendwechsel als SMA
- Glättet Ausreißer stärker als einfache Durchschnitte

**Schwächen:**
- Viele Umschichtungen in trendlosen Phasen möglich
- Nachlaufender Indikator; Wendepunkte werden oft verspätet erkannt
- Keine integrierten Stops/TPs; Risikobegrenzung extern nötig.
