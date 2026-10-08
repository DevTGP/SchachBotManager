# Debugging

Auf dem Server und in der Arena spricht der Bot über stdin/stdout mit dem Schiedsrichter. Für den Debugger kehrt sich die Reihenfolge um: Die Arena wartet auf einer TCP-Verbindung, der Bot wird normal als Hauptprogramm im Debugger gestartet und verbindet sich.

## Grundmuster

1. Arena mit `tcp` und ohne Uhr starten:
   ```
   sbm-arena tcp material --no-clock --moves
   ```
2. Den Bot mit dem Argument `--tcp` im Debugger der IDE starten (oder `SBM_TRANSPORT=tcp` setzen).
3. Haltepunkt in `choose_move` – die Arena wartet, die Uhr ist abgeschaltet.

| Ausgabe | Erscheint in |
|---------|--------------|
| Züge, Suchinformation, Ergebnis | Terminal der Arena |
| `sbm.Log`, `print` | Terminal bzw. Konsole des Bots |

Anderer Port: `sbm-arena tcp:7480 …` und `python bot.py --tcp 7480`.

## VS Code

Das Vorlagenprojekt [`templates/python/`](../../../templates/python/README.md) enthält fertige Konfigurationen in `.vscode/launch.json` und `.vscode/tasks.json`:

| Konfiguration | Wirkung |
|---------------|---------|
| „Bot debuggen: Weiß gegen material“ (bzw. Schwarz) | Startet die Arena als Hintergrundaufgabe, dann den Bot mit `--tcp` im Debugger |
| „Bot debuggen: Stellung aus games.pgn, Weiß“ (bzw. Schwarz) | Fragt nach Partie und Halbzügen, startet genau dort |
| „Bot debuggen: Arena läuft schon“ | Nur der Bot, für eine selbst gestartete Arena |

## PyCharm und andere IDEs

Arena im Terminal starten, dann eine Run-Konfiguration für `bot.py` mit dem Parameter `--tcp` im Debug-Modus ausführen.

## Stellung nachspielen

Läuft eine Partie schief, die Partien mit `--pgn` aufzeichnen und die Stellung im Debugger nachstellen:

```
sbm-arena bot.py material --games 10 --pgn games.pgn
sbm-arena tcp material --no-clock --replay games.pgn --replay-game 3 --replay-ply 41
```

- `--replay-ply` zählt Halbzüge ab Partiebeginn; danach übernehmen die Bots.
- Die Farbe ergibt sich aus der Reihenfolge der Bot-Angaben: im Beispiel spielt der TCP-Bot Weiß. Für Schwarz `sbm-arena material tcp …`.
- Nachgespielt wird nur die Stellung. Wiederholungen aus den Zügen davor zählen nicht.
- Direkt mit FEN: `sbm-arena tcp material --no-clock --fen "…"`.

## Einzelne Stellungen ohne Arena

Suche und Bewertung lassen sich auch ohne Protokoll testen, z. B. in einem Test oder einer interaktiven Sitzung:

```python
import sbm
from bot import MyBot

board = sbm.Board.from_fen("r1bqkbnr/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 2 4")
clock = sbm.Clock(remaining_ms=60_000, opponent_remaining_ms=60_000, increment_ms=0)
move = MyBot().choose_move(board, clock)
print(board.san(move))  # Qxf7#
```

`sbm.Clock` ist hier direkt erzeugbar; `report` funktioniert ebenfalls, wird aber nicht gesendet. Solche Tests gehören nicht in den Upload oder werden mit `sbm-check --exclude 'tests/*'` ausgenommen, weil `pytest` und Ähnliches dort nicht erlaubt sind.

## Log-Stufe

```
python bot.py --tcp --log-level debug --log-file bot.log
```

Details in [log.md](log.md).

## Grenzen

- Der Debugger hält im eigenen Code und im Python-Teil des SDK, nicht in der Zuggenerierung des C++-Kerns. Zum Nachvollziehen dienen `board.to_text()`, `board.fen()` und `board.move_history()`.
- TCP-Bots werden nicht eingefroren und haben keine Speichergrenze; Zeitverhalten deshalb immer auch ohne `tcp` und mit Uhr prüfen.
