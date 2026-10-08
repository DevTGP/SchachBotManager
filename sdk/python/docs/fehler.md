# Fehler

## Ausnahmen des SDK

Alle erben von `sbm.ChessError`. Bei einem Fehler bleibt das Brett unverändert.

| Ausnahme | Wann |
|----------|------|
| `InvalidArgumentError` | Wert außerhalb seines Bereichs: Feld > 63, Farbe > 1, unbekannte Log-Stufe, Dateiname mit Pfad, `uci()` auf `NULL_MOVE`/`RESIGN` |
| `InvalidFenError` | FEN fehlerhaft oder Stellung unmöglich |
| `InvalidUciError` | Text ist kein Zug in UCI-Notation |
| `IllegalMoveError` | Zug wohlgeformt, aber in der Stellung nicht legal |
| `InvalidStateError` | Aufruf im aktuellen Zustand nicht möglich: `undo_move` ohne Verlauf, Nullzug im Schach |
| `DataNotFoundError` | `load_data` findet die Datei nicht |

Falsche Python-Typen (z. B. ein `str` statt eines `Move`) lösen `TypeError` aus.

```python
try:
    move = board.parse_move(candidate)
except sbm.IllegalMoveError:
    move = board.legal_moves()[0]
```

## Fehler im eigenen Bot

| Ursache | Folge |
|---------|-------|
| Ausnahme in `__init__`, `on_game_start`, `choose_move` oder `on_game_end` | Log auf Stufe ERROR mit Traceback, Prozess endet mit Exit-Code 1, Wertung `crash` |
| `choose_move` gibt keinen `Move` zurück (z. B. `None`) oder `NULL_MOVE` | Wie eine Ausnahme |
| `choose_move` gibt einen illegalen Zug zurück | Partie verloren durch `illegal_move` |
| Bedenkzeit überschritten | Prozess wird hart beendet, `timeout` |
| `on_game_start` braucht länger als `startup_ms` | `startup_timeout` |
| Speichergrenze überschritten | `memory_limit` |

Typische Ursache für `None`: Eine Schleife wählt den besten Zug mit einem Startwert, den kein Zug übertrifft. Ein Startwert unterhalb jeder möglichen Bewertung oder `best = moves[0]` vermeidet das.

## Fehlersuche

- Die Arena zeigt die Log-Zeilen des Bots mit Traceback auf stderr.
- Eine schiefgelaufene Stellung lässt sich aus der PGN-Datei nachspielen und im Debugger untersuchen ([debugging.md](debugging.md)).
- `board.to_text()` und `board.fen()` geben die Stellung im Log aus.
