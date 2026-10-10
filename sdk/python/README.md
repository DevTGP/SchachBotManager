# schachbotmanager

Python-SDK für [SchachBotManager](https://github.com/DevTGP/SchachBotManager), eine Website, auf der Schachbots in Ligen, Turnieren und Einzelspielen gegeneinander antreten. Mit dem Paket schreibt man einen eigenen Bot: Es bringt Brett, Zuggenerator, Uhr, Log und das Protokoll zum Server mit. Der Bot liefert nur den Zug.

Dazu gehören:

- die lokale Arena `sbm-arena`;
- zwei Referenzbots (`random`, `material`);
- die Prüfung `sbm-check` für den Upload;
- ein Viewer-Fenster, in dem die Partien live mitlaufen und sich Zug für Zug durchspulen lassen.

```
pip install schachbotmanager
```

- Vorkompilierte Wheels für Windows x64, Linux x64/arm64 (glibc) und macOS x64/arm64 (ab macOS 11), Python 3.11 bis 3.14.
- Keine weiteren Abhängigkeiten. Importiert wird das Paket als `sbm`.
- Die Schachregeln stecken in einem gemeinsamen C++-Kern, den alle SDKs und der Server nutzen. Lokal und auf dem Server gelten also dieselben Regeln.

## Der erste Bot

```python
# bot.py
import sbm


class MyBot(sbm.Bot):
    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        captures = board.legal_captures()
        return captures[0] if captures else board.legal_moves()[0]


if __name__ == "__main__":
    sbm.run(MyBot)
```

```
sbm-arena bot.py material --games 10 --pgn games.pgn
```

Dieselbe Datei läuft lokal, im Debugger und auf dem Server. `sbm.run` übernimmt das Protokoll, die Uhr und das Ende der Partie. Jede Partie bekommt eine neue Instanz der Klasse.

## Die API im Überblick

| Teil | Wichtigste Namen |
|------|------------------|
| `sbm.Bot` | `choose_move(board, clock)` (Pflicht), `on_game_start(info)`, `on_game_end(result)`, `report(info)` |
| `sbm.Board` | `legal_moves()`, `legal_captures()`, `is_legal(move)`, `make_move(move)`, `undo_move()`, `parse_move("e2e4")`, `san(move)`, `fen()`, `Board.from_fen(fen)`, `piece_at(sq)`, `side_to_move()`, `king_square(color)`, `is_check()`, `is_checkmate()`, `is_draw()`, `is_game_over()`, `hash()`, `copy()` |
| Rohzugriff auf `Board` | `bitboard(color, piece_type)`, `occupied()`, `attacks_from(sq)`, `attackers_of(sq, color)`, `is_attacked(sq, color)`, `checkers()`, `pinned(color)`, `make_null_move()` |
| `sbm.Move` | `uci()`, `from_square()`, `to_square()`, `promotion()`, `is_capture()`, `is_castling()`, `is_en_passant()`, `Move.parse(uci)` |
| `sbm.Clock` | `remaining_ms()`, `opponent_remaining_ms()`, `increment_ms()`, `elapsed_ms()` |
| `sbm.Log` | `trace`, `debug`, `info`, `warn`, `error`, `set_level`, `is_enabled` |
| `sbm.Info` | Suchinformation zum Zug: `depth`, `seldepth`, `score_cp`, `score_mate`, `nodes`, `pv`, `text` |
| `sbm.GameInfo`, `sbm.GameResult` | Farbe, Gegner, Startstellung, Bedenkzeit, Disziplin bzw. Ergebnis und Grund |
| `sbm.load_data(name)` | Liest eine mitgelieferte Datendatei (Eröffnungsbuch, Tabellen; bis 1 MB) als `bytes` |
| Konstanten | `WHITE`, `BLACK`, `PAWN` … `KING`, `WHITE_KNIGHT` …, Felder `A1` … `H8`, `NULL_MOVE`, `RESIGN` |
| Ausnahmen | `ChessError` als Basis; `InvalidFenError`, `InvalidUciError`, `IllegalMoveError`, `InvalidStateError`, `InvalidArgumentError`, `DataNotFoundError` |

Ein Bot mit Suchinformation:

```python
class SearchBot(sbm.Bot):
    def on_game_start(self, info: sbm.GameInfo) -> None:
        sbm.Log.info(f"against {info.opponent_name}, {info.initial_time_ms} ms")

    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        budget_ms = clock.remaining_ms() // 30 + clock.increment_ms()
        best = board.legal_moves()[0]
        # … search within budget_ms …
        self.report(sbm.Info(depth=6, score_cp=35, nodes=120_000, pv=[best]))
        return best
```

`Info` und die Ausgaben von `sbm.Log` erscheinen in der Arena, im Viewer-Fenster und im Partie-Viewer der Website. Auf das Ergebnis haben sie keinen Einfluss.

## Lokal spielen

Mit der Arena auf der Kommandozeile:

```
sbm-arena bot.py material --games 10 --time 10+0.1 --pgn games.pgn
sbm-arena bot.py gegner.py --moves
```

Oder aus einem Skript, ohne Argumente und mit Haltepunkten im Debugger:

```python
# start.py
import sbm
from bot import MyBot

games = sbm.play(MyBot, "material", games=4, time="60+1", viewer=True)
```

`sbm.play` gibt die Partien als Liste von `sbm.PlayedGame` zurück (Farbe, Gegner, Ergebnis, Grund) und schreibt den Punktestand ins Log. `random` und `material` sind die mitgelieferten Referenzbots; `sbm-arena --help` zeigt alle Optionen der Arena.

## Viewer-Fenster

Mit `viewer=True` öffnet sich ein Fenster, in dem die Partien live mitlaufen:

```python
sbm.play(MyBot, "material", games=4, viewer=True)  # alle Partien in einem Fenster
sbm.run(MyBot, viewer=True)  # in bot.py
```

- **Bedienung:** ←/→ oder das Mausrad über dem Brett springen einen Halbzug zurück oder vor. Pos1/Ende springen zum Anfang oder zum letzten Zug, „Live“ folgt wieder der laufenden Partie, F dreht das Brett.
- **Anzeige je Zug:** Uhren, Bedenkzeit, die Suchinformation aus `report` und die Log-Zeilen des Bots.
- **Ende:** Nach der letzten Partie wartet das Programm, bis das Fenster geschlossen wird. Strg+C oder das Beenden in der IDE schließt es ebenfalls.
- **Kein Fenster:** Ist `SBM_NO_VIEWER` gesetzt, bleibt das Fenster zu, etwa für Tests. Auf dem Server setzt die Sandbox die Variable selbst. Ein hochgeladener Bot darf `viewer=True` also behalten.
- **Programm:** Das Fenster ist das Programm `sbm-viewer` (C++, SDL3, Dear ImGui). Es steckt in jedem Wheel und braucht nichts weiter. Unter Linux läuft es unter X11 oder XWayland.

## Gegen Bots auf dem Server

Mit einem API-Token von der Kontoseite spielt der Bot vom eigenen Rechner aus gegen geprüfte Bots der Website, ohne Upload:

```python
sbm.play(MyBot, "Material", server="https://schachbotmanager.devtgp.net", games=2)
```

- Das Token kommt aus der Umgebungsvariable `SBM_TOKEN` oder aus dem Argument `token=`.
- Auf der Kommandozeile geht es so: `python bot.py --remote https://schachbotmanager.devtgp.net --opponent Material`.
- **Das Token ist ein Passwort**: Skripte mit Token nicht einchecken und nicht hochladen.

## Hochladen

Hochgeladene Bots laufen auf dem Server in einer Sandbox (nsjail mit seccomp), vorher wird der Code statisch geprüft. Erlaubt sind `sbm`, eigene Module und ein Teil der Standardbibliothek; Dateien liest der Bot nur über `load_data`. Dieselbe Prüfung läuft lokal:

```
sbm-check .
sbm-check my_bot --entry main.py --json
```

## Vorlage und Anleitung

- Ein lauffähiges [Vorlagenprojekt](https://github.com/DevTGP/SchachBotManager/tree/master/templates/python) bringt mit:
  - Eröffnungsbuch;
  - `start.py`;
  - Debug-Konfiguration und Arena-Aufgaben für VS Code.
- Die vollständige Anleitung liegt unter [`sdk/python/docs`](https://github.com/DevTGP/SchachBotManager/tree/master/sdk/python/docs):

| Thema | Seite |
|-------|-------|
| Installation, erster Bot, erste Partie | [erste-schritte.md](https://github.com/DevTGP/SchachBotManager/blob/master/sdk/python/docs/erste-schritte.md) |
| `Bot`, Ablauf einer Partie, `run`, Suchinformation | [bot.md](https://github.com/DevTGP/SchachBotManager/blob/master/sdk/python/docs/bot.md) |
| `Board`: Abfragen, Züge, Spielzustand, Rohzugriff | [brett.md](https://github.com/DevTGP/SchachBotManager/blob/master/sdk/python/docs/brett.md) |
| `Move`: Aufbau, Notation, Sonderwerte | [zuege.md](https://github.com/DevTGP/SchachBotManager/blob/master/sdk/python/docs/zuege.md) |
| Farben, Figuren, Felder, Flags | [konstanten.md](https://github.com/DevTGP/SchachBotManager/blob/master/sdk/python/docs/konstanten.md) |
| `Clock` und Zeiteinteilung | [uhr.md](https://github.com/DevTGP/SchachBotManager/blob/master/sdk/python/docs/uhr.md) |
| `Log` und Log-Stufen | [log.md](https://github.com/DevTGP/SchachBotManager/blob/master/sdk/python/docs/log.md) |
| `load_data` für Bücher und Tabellen | [datendateien.md](https://github.com/DevTGP/SchachBotManager/blob/master/sdk/python/docs/datendateien.md) |
| Ausnahmen und Fehler im Bot | [fehler.md](https://github.com/DevTGP/SchachBotManager/blob/master/sdk/python/docs/fehler.md) |
| Lokale Partien mit `sbm-arena` | [arena.md](https://github.com/DevTGP/SchachBotManager/blob/master/sdk/python/docs/arena.md) |
| Bot im Debugger, Stellungen nachspielen | [debugging.md](https://github.com/DevTGP/SchachBotManager/blob/master/sdk/python/docs/debugging.md) |
| Regeln für Bot-Code, `sbm-check`, Upload | [upload.md](https://github.com/DevTGP/SchachBotManager/blob/master/sdk/python/docs/upload.md) |
| Vollständiger Bot mit Suche und Zeitgrenze | [beispiel-suche.md](https://github.com/DevTGP/SchachBotManager/blob/master/sdk/python/docs/beispiel-suche.md) |
| Mit API-Token gegen Bots auf dem Server | [remote.md](https://github.com/DevTGP/SchachBotManager/blob/master/sdk/python/docs/remote.md) |
| Partien per Code mit `sbm.play` | [spielen-per-code.md](https://github.com/DevTGP/SchachBotManager/blob/master/sdk/python/docs/spielen-per-code.md) |
| Viewer-Fenster | [viewer.md](https://github.com/DevTGP/SchachBotManager/blob/master/sdk/python/docs/viewer.md) |

## Lizenz

MIT-0. Das Viewer-Programm enthält SDL3 (zlib), Dear ImGui (MIT), nlohmann/json (MIT) und DejaVu Sans (freie Lizenz); die Lizenztexte liegen im Paket unter `sbm/bin/licenses`.
