# Bot und Partieablauf

## Basisklasse `sbm.Bot`

| Methode | Pflicht | Aufgerufen |
|---------|---------|------------|
| `on_game_start(self, info: GameInfo) -> None` | nein | Einmal vor dem ersten Zug, innerhalb des Startbudgets |
| `choose_move(self, board: Board, clock: Clock) -> Move` | **ja** | Bei jedem eigenen Zug; die Rückgabe beendet die eigene Bedenkzeit |
| `on_game_end(self, result: GameResult) -> None` | nein | Nach dem Partieende, für Aufräumen und letzte Log-Zeilen |
| `report(self, info: Info) -> None` | – | Vom Bot selbst aufgerufen, siehe [Suchinformation](#suchinformation) |

- Pro Prozess wird genau eine Partie gespielt; `run` erzeugt die Instanz einmal.
- Objektfelder bleiben zwischen den Zügen erhalten (Transpositionstabelle, Killerzüge, Statistik).
- `__init__` darf überschrieben werden, muss aber ohne Argumente aufrufbar sein. Aufwendige Vorbereitung (Daten laden, Tabellen bauen) gehört nach `on_game_start`, weil dort das Startbudget gilt und die Partieparameter bekannt sind.

## Ablauf einer Partie

```
run(MyBot)
 ├─ MyBot()                         Instanz
 ├─ init      → on_game_start(info) Startbudget (startup_ms)
 ├─ turn      → choose_move(...)    je eigener Zug, Uhr läuft
 │  …                               dazwischen ist der Prozess eingefroren
 └─ game_over → on_game_end(result)
```

- **Einfrieren:** Außerhalb des eigenen Zuges hält der Server den Bot-Prozess an. Rechnen in der Zeit des Gegners ist nicht möglich.
- **Zeit:** Gemessen wird Wanduhrzeit. Bei Zeitüberschreitung beendet der Server den Prozess hart; `on_game_end` läuft dann nicht mehr.
- **Gegnerzug:** Das SDK führt den Zug des Gegners selbst auf seinem Brett aus und gleicht die Stellung mit dem Schiedsrichter ab. Der Bot sieht in `choose_move` immer die aktuelle Stellung.

## `choose_move`

```python
def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
    ...
```

| Parameter | Inhalt |
|-----------|--------|
| `board` | Kopie der aktuellen Partiestellung samt Zugverlauf. Freies Ziehen und Zurücknehmen erlaubt |
| `clock` | Zeitlage dieses Zuges ([uhr.md](uhr.md)) |

Rückgabe:

| Wert | Wirkung |
|------|---------|
| Ein `Move`, z. B. aus `board.legal_moves()` oder `board.parse_move("e2e4")` | Wird als Zug gesendet |
| `sbm.Move.RESIGN` (auch `sbm.RESIGN`) | Aufgabe |
| `sbm.Move.NULL_MOVE`, `None` oder ein anderer Typ | Fehler: Prozess endet, Wertung `crash` |

Das SDK prüft die Legalität des zurückgegebenen Zuges nicht; darüber entscheidet allein der Schiedsrichter. Ein illegaler Zug verliert die Partie (`illegal_move`).

Für die Rückgabe reicht ein Zug mit Start, Ziel und Umwandlung; `sbm.Move.parse("e7e8q")` ohne Flags funktioniert also ebenfalls ([zuege.md](zuege.md)).

## `GameInfo`

Unveränderlicher Datensatz, übergeben an `on_game_start`.

| Feld | Typ | Inhalt |
|------|-----|--------|
| `game_id` | `str` | Kennung der Partie |
| `color` | `int` | Eigene Farbe, `sbm.WHITE` oder `sbm.BLACK` |
| `opponent_name` | `str` | Name des Gegners |
| `start_fen` | `str` | Startstellung (nicht immer die Grundstellung) |
| `initial_time_ms` | `int` | Bedenkzeit zu Beginn |
| `increment_ms` | `int` | Zeitgutschrift je eigenem Zug |
| `startup_ms` | `int` | Budget für den Start bis zur Bereitmeldung |
| `memory_limit_mib` | `int` | Speichergrenze des Prozesses |
| `discipline` | `str` | Name der Disziplin |

```python
def on_game_start(self, info: sbm.GameInfo) -> None:
    self.color = info.color
    self.table = {}
    sbm.Log.info(f"{'White' if info.color == sbm.WHITE else 'Black'} vs {info.opponent_name}")
```

## `GameResult`

Übergeben an `on_game_end`.

| Feld | Werte |
|------|-------|
| `result` | `"1-0"`, `"0-1"`, `"1/2-1/2"`, `"*"` (abgebrochen, ohne Wertung) |
| `termination` | `checkmate`, `resignation`, `timeout`, `illegal_move`, `protocol_violation`, `crash`, `memory_limit`, `startup_timeout`, `stalemate`, `threefold_repetition`, `fifty_move_rule`, `insufficient_material`, `timeout_insufficient_material`, `max_moves`, `aborted` |

## Suchinformation

`self.report(info)` speichert eine `sbm.Info` für den laufenden Zug. Sie wird mit dem Zug gesendet und in Arena und Partie-Viewer angezeigt; auf das Ergebnis hat sie keinen Einfluss.

```python
self.report(sbm.Info(depth=6, score_cp=35, nodes=120_000, pv=[best, reply], text="tt hit 41%"))
```

| Feld | Typ | Grenzen |
|------|-----|---------|
| `depth`, `seldepth` | `int` | 0 bis 1024 |
| `score_cp` | `int` | −100 000 bis 100 000, Centipawns aus Sicht des Bots |
| `score_mate` | `int` | −1024 bis 1024 ohne 0; Matt in n Zügen, negativ = wird mattgesetzt |
| `nodes` | `int` | 0 bis 2^53 − 1 |
| `pv` | `list[Move]` | Hauptvariante; mehr als 32 Züge werden gekürzt |
| `text` | `str` | Freitext; mehr als 256 Zeichen werden gekürzt |

- Alle Felder sind optional und nur als Schlüsselwort angebbar.
- Es zählt der letzte Aufruf vor der Rückgabe; ein neuer Zug beginnt ohne Info. Häufiges Aufrufen ist billig, es wird nur gespeichert.
- Ungültige Werte werden nicht gesendet, sondern mit einer Warnung im Log weggelassen. Sind `score_cp` und `score_mate` beide gesetzt, gilt `score_mate`.
- Bei `RESIGN` wird keine Info gesendet.

## `sbm.run` und Startoptionen

```python
if __name__ == "__main__":
    sbm.run(MyBot)
```

`run` erwartet die Klasse, nicht eine Instanz. Transport und Log-Stufe kommen aus Argumenten oder Umgebung:

| Argument | Umgebungsvariable | Wirkung |
|----------|-------------------|---------|
| `--tcp [PORT]` | `SBM_TRANSPORT=tcp`, `SBM_PORT` | Verbindet zu einer wartenden Arena auf `127.0.0.1` (Standardport 7470) statt stdin/stdout |
| `--log-level LEVEL` | `SBM_LOG_LEVEL` | Startstufe: `trace`, `debug`, `info`, `warn`, `error`, `off` |
| `--log-file PATH` | `SBM_LOG_FILE` | Log zusätzlich an eine Datei anhängen (nur lokal sinnvoll) |

- Argumente schlagen Umgebungsvariablen; ohne beides gelten `stdio` und `INFO`.
- Andere Argumente bleiben unberührt in `sys.argv` und gehören dem Bot.
- Auf dem Server wird der Bot ohne diese Argumente gestartet.

## Exit-Verhalten

| Situation | Folge |
|-----------|-------|
| Partie regulär beendet | `run` kehrt zurück, Exit-Code 0 |
| Ausnahme in einem Callback oder unbrauchbarer Rückgabewert | Log auf Stufe ERROR mit Traceback, Exit-Code 1, Wertung `crash` |
| Arena bei `--tcp` nicht erreichbar | Log-Meldung, Exit-Code 1 |
| Ungültige Startoption | Meldung auf stderr, Prozess endet |
