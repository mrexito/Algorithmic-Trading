Projektüberblick
================

Das ``My Trading Bot Dashboard`` bündelt Backtesting-Logik, Datenpipelines und eine Plotly-Dash-Oberfläche in einem Paket. Die wichtigsten Komponenten:

- ``backtest_runner.py`` orchestriert Strategien und speichert Ergebnis-Serien.
- ``data`` enthält Downloader sowie die Yahoo-Finance-Integration zur Versorgung von TimescaleDB.
- ``dashboard`` stellt drei Tabs bereit (Übersicht, Details, Strategiebeschreibungen) und triggert das Bootstrapping neuer OHLCV-Daten.
- ``strategies`` liefert Beispiel-Implementierungen wie Buy&Hold, SMA oder RSI.

Die Sphinx-Dokumentation extrahiert zu diesen Modulen automatisch alle Docstrings und stellt sie zusammen mit erläuternden Kapiteln bereit.
