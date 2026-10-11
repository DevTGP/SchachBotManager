# Code-Karte: Python-SDK

Das Python-SDK unter `sdk/python` ist das Paket `schachbotmanager` (Import `sbm`). Es enthält das native Binding des Kerns (`sbm._core`, nanobind), die Bot-Laufzeit, Referee, Arena, Referenzbots, statische Analyse, Remote-Transport und die Python-Seite des Viewers (E58–E70, E90, E116, E120). Konzepte: [sdk-api.md](../komponenten/sdk-api.md), [bot-protokoll.md](../komponenten/bot-protokoll.md), [lokale-entwicklung.md](../komponenten/lokale-entwicklung.md), [statische-analyse.md](../komponenten/statische-analyse.md). Nutzerdoku: [`sdk/python/docs/`](../../sdk/python/docs/README.md).

## Einstieg

| Einstieg | Ort | Zweck |
|----------|-----|-------|
| `sbm.run(MyBot)` | [`runtime.py`](../../sdk/python/src/sbm/runtime.py) | Hauptschleife eines Bots über `stdio`, `tcp` oder `remote` (E61) |
| `sbm.play(MyBot, …)` | [`starter.py`](../../sdk/python/src/sbm/starter.py) | Partien per Code, lokal oder auf dem Server (E120) |
| `sbm-arena` | `sbm.arena.cli:main` | Lokale Arena (E67), auch `python -m sbm.arena` |
| `sbm-check` | `sbm.analysis.cli:main` | Statische Analyse vor dem Upload (E90), auch `python -m sbm.analysis` |
| `python -m sbm.bots.random_mover`, `sbm.bots.material` | [`bots/`](../../sdk/python/src/sbm/bots/) | Referenzbots (E68) |
| `NB_MODULE(_core)` | [`src/native/module.cpp`](../../sdk/python/src/native/module.cpp) | Natives Modul |

Lesereihenfolge: `__init__.py` → `bot.py`, `clock.py` → `runtime.py` → `game.py` → `channel.py`, `protocol.py` → `referee/match.py` → `arena/series.py` und `arena/cli.py`. Für das Binding: `native/module.cpp` → `board.hpp` → `query.hpp`, `status.cpp` → eine Datei wie `board_state.cpp`.

## Bau

| Teil | Ort | Inhalt |
|------|-----|--------|
| Build-Backend | [`pyproject.toml`](../../sdk/python/pyproject.toml) | `scikit-build-core~=1.1`, `nanobind~=3.1`; Version per Regex aus `sdk/core/CMakeLists.txt` (E36); `wheel.packages = ["src/sbm"]`, `build-dir = build/{wheel_tag}` |
| CMake | [`CMakeLists.txt`](../../sdk/python/CMakeLists.txt) | Unter Windows nur MSVC (sonst Abbruch); bindet `../core` mit `SBM_BUILD_TESTS=OFF` und `SBM_SHARED=OFF` ein; `nanobind_add_module(_core NB_STATIC …)`; `nanobind_add_stub` erzeugt `_core.pyi` und `py.typed`; Installation nach `sbm` |
| Option `SBM_VIEWER` | `CMakeLists.txt`, Standard `ON` | `ExternalProject_Add(sbm_viewer …)` baut `sdk/viewer` mit `SBM_VIEWER_BUILD_TESTS=OFF`, `SBM_VIEWER_INSTALL_DIR=bin`, `SBM_VIEWER_LICENSE_DIR=bin/licenses`, reicht macOS-Ziel und Architekturen durch, `BUILD_ALWAYS ON`; das Ergebnis landet in `sbm/bin` (E107). `-C cmake.define.SBM_VIEWER=OFF` baut ohne Viewer |
| Wheels | `[tool.cibuildwheel]` in `pyproject.toml` | cp311–cp314, ohne musllinux, `auto64`; Linux installiert vorher die X11-Header, macOS ab 11.0; Tests mit `SBM_REQUIRE_VIEWER=1` (E64) |
| Vorlage | [`templates/python/`](../../templates/python/README.md) | `bot.py` mit `data/book.txt`, `start.py` mit `sbm.play`, `.vscode/` mit Arena-Aufgaben (E69, E120) |

## Module

### Natives Modul (`src/native/`)

| Modul | Aufgabe |
|-------|---------|
| `module.cpp` | `sbm._core`: prüft `SBM_ABI_VERSION` gegen `sbm_abi_version()` (sonst `ImportError`), `core_version`, bindet `Move` und `Board` |
| `board.hpp`/`.cpp` | `Board` besitzt ein Handle (Deleter `BoardFree`, E22); `create`, `from_fen`, `fen`, `copy`, `hash`, `move_history`, `to_text` |
| `board_moves.cpp` | Züge erzeugen, prüfen, ausführen, zurücknehmen |
| `board_query.cpp` | Einzelne Eigenschaften der Stellung |
| `board_raw.cpp` | Bitboards und Felder |
| `board_state.cpp` | Endbedingungen |
| `move.hpp`/`.cpp` | `Move` als unveränderlicher 16-Bit-Wert (E34); Bitoperationen hier, `parse`/`uci` im Kern |
| `move_list.hpp` | Zugwerte der C-Schnittstelle als Liste von `Move` |
| `query.hpp` | `query<T>(function, board, what, args…)`: ein Wert lesen, Status prüfen |
| `status.hpp`/`.cpp` | Statuscodes als Ausnahmen aus `sbm.errors` (E49, E52); Speichermangel als `MemoryError` |
| `arguments.hpp` | `to_c<T>`: Python-Ganzzahl in C-Typ, sonst `InvalidArgumentError` |
| `text.hpp` | Textausgaben in Puffer fester Größe |

### Paket `sbm` (oberste Ebene)

| Modul | Aufgabe |
|-------|---------|
| `__init__.py` | Öffentliche API: `Board`, `Move`, `Bot`, `Clock`, Konstanten, Fehler, `Log`, Records, `run`, `play`, `load_data`; `__version__ = core_version()` |
| `bot.py` | Basisklasse `Bot` mit Callbacks; `take_report` |
| `clock.py` | `Clock` des Bots |
| `constants.py` | Farben, Figurtypen, Felder, Ergebnisse |
| `errors.py` | Ausnahmen (E49) |
| `data.py` | `data_directory`, `load_data` (E62) |
| `info.py` | `info_fields`: Suchinformation zum Zug (E63) |
| `log.py` | `Log`, `configure`, `set_listener`, `set_ply` |
| `options.py` | Argumente von `run` (E61): `parse_options`, `Options`, `RemoteOptions`, `OptionsError` |
| `channel.py` | NDJSON über stdio und TCP: `Channel`, `open_stdio`, `open_tcp`, `ProtocolError` |
| `protocol.py` | Nachrichten von Protokoll v1 bauen und lesen |
| `game.py` | Zustandsautomat des Bots: `Game`, `guarded`, `describe`, `BotError` |
| `records.py` | `GameInfo`, `GameResult`, `Info`, `PlayedGame` |
| `runtime.py` | `run` |
| `starter.py` | `play` (E120); importiert Arena und Remote erst bei Bedarf |

### `sbm.referee` (E65, E66)

| Modul | Aufgabe |
|-------|---------|
| `match.py` | `Match`: eine Partie zwischen zwei `Player` |
| `player.py` | Schnittstelle `Player` (`start`, `send`, `receive`, `suspend`, `resume`, `close`); Fristen aus `monotonic_ns` |
| `clock.py` | `GameClock` |
| `settings.py` | `MatchSettings` |
| `bot_messages.py` | Strenge Prüfung der Bot-Nachrichten (E66) |
| `referee_messages.py` | `init`, `turn`, `error`, `game_over` an den Bot |
| `outcome.py` | Ergebnis und Abbruchgrund (E44) |
| `record.py` | Aufzeichnung einer Partie |

### `sbm.arena` (E67, E69)

| Modul | Aufgabe |
|-------|---------|
| `cli.py` | `sbm-arena`; Exit-Codes 0, 1, 2, 130 |
| `__main__.py` | `python -m sbm.arena` |
| `bot_spec.py` | `parse_bot`: `tcp[:PORT]`, `random`/`material`, `.py`-Datei oder Befehlszeile |
| `entrants.py` | Die zwei Bots einer Serie; frischer Spieler je Partie |
| `series.py` | `Series`, `Score`, `Game`: Partien mit wechselnden Farben |
| `local_game.py` | `play_local`: eigener Bot im Thread gegen einen Prozess (für `sbm.play`) |
| `stream_player.py` | Spieler über ein Paar Byte-Streams |
| `process_player.py` | `ProcessPlayer`: Bot als Kindprozess, stderr auf die Konsole |
| `tcp_player.py` | Bot aus der IDE über TCP auf `127.0.0.1`, wird nie eingefroren |
| `thread_player.py` | Bot im selben Prozess über ein Socket-Paar |
| `line_reader.py` | Liest Zeilen im Hintergrund-Thread, damit Fristen auch für Windows-Pipes gelten |
| `process_group.py` | `POPEN_OPTIONS`, Fassade `ProcessGroup` |
| `posix_group.py` | Einfrieren per `SIGSTOP`/`SIGCONT` |
| `windows_job.py` | Job-Objekt für einen Bot und seine Kindprozesse (ctypes) |
| `windows_processes.py` | Einzelne Windows-Prozesse über die Win32-API (ctypes) |
| `time_control.py` | `parse_time_control("60+1")` |
| `replay.py` | `replay_fen`: Startstellung aus einer PGN-Partie |
| `pgn_reader.py` | `read_games` |
| `pgn.py` | `to_pgn` |
| `report.py` | `ConsoleReport` |

### Weitere Unterpakete

| Modul | Aufgabe |
|-------|---------|
| `bots/random_mover.py` | Zufälliger legaler Zug |
| `bots/material.py` | Alpha-Beta über zwei Halbzüge mit Materialwertung |
| `analysis/analyzer.py` | `analyze`: liest Dateien als AST, importiert nie |
| `analysis/checker.py` | `FileChecker`: Regeln für eine Datei |
| `analysis/modules.py` | Welche Namen auf Module zeigen; Whitelist und eigene Module |
| `analysis/project.py` | `select_files`, `check_project`: Ordner wie beim Upload |
| `analysis/upload.py` | `check_upload`, `file_kind`: Upload-Regeln, gemeinsam mit API und Runner (E92) |
| `analysis/rules.py` | `Rules`, `load_rules` aus `python_rules.json` |
| `analysis/python_rules.json` | Regelsatz `python-1` |
| `analysis/report.py` | `Finding`, `Report`, `make_report`; Regel-IDs; JSON für den Runner |
| `analysis/cli.py` | `sbm-check`; Exit-Codes 0, 1, 2 |
| `analysis/__main__.py` | `python -m sbm.analysis`, so ruft der Runner die Analyse in der Sandbox |
| `remote/websocket.py` | WebSocket-Client nach RFC 6455 (nur Standardbibliothek); Lese-Thread beantwortet Pings |
| `remote/game_request.py` | `POST /api/v1/remote/matches`, `RemoteError` |
| `remote/opening.py` | `open_game` |
| `remote/channel.py` | `RemoteChannel`: Kanal von `Game` über den WebSocket |
| `remote/remote_game.py` | `play_remote` (E116) |
| `viewer/process.py` | `program_path`, `start_process`, `encode` |
| `viewer/window.py` | `ViewerWindow`, `open_window`, `active_window`; `SBM_NO_VIEWER` (E108) |
| `viewer/game_view.py` | `GameView`: übersetzt Ereignisse von `Game` in viewer-v1 |
| `viewer/messages.py` | Nachrichten `start`, `move`, `log`, `game_over` |

## Ablauf

`sbm.run(MyBot)` in einem Bot-Prozess (`runtime.py`, `game.py`):

1. `run` prüft die Typen, liest `parse_options(sys.argv[1:], os.environ)`, richtet `log.configure` (optional mit Logdatei) ein und öffnet bei `viewer=True` das Fenster (`open_window`).
2. `_open` wählt den Kanal: `remote` (importiert `sbm.remote` erst dann), `tcp` oder `stdio`.
3. `Game(guarded(bot), channel).play()` liest Nachrichten des Referees:
   - `init` → `_start`: `Board.from_fen`, Versionsprüfung, `on_game_start`, Antwort `ready(core_version())`.
   - `turn` → `_turn`: `Clock` bauen, `set_ply`, `_synchronize` (wendet `last_move` an; weicht die FEN ab, gilt die des Referees, E42/E48), `choose_move(board.copy(), clock)`, `_answer` prüft Zug bzw. `RESIGN` und hängt `info` an, senden, eigenen Zug ausführen.
   - `game_over` → `_end`: `GameResult`, `on_game_end`.
4. `BotError` oder `ProtocolError` werden geloggt; Exit-Code 1.

Eine Partie in der Arena (`sbm-arena a.py material`):

1. `arena/cli.py` liest die Optionen, `bot_spec.parse_bot` die Bots, `_settings` baut `MatchSettings`.
2. `entrants.create_entrant` legt je Bot einen Teilnehmer an; `Series.play` erzeugt je Partie frische `Player` und ruft `Match(white, black, settings).play()`.
3. `Match._turn`: `resume`, `turn` senden, `receive` bis zur Frist aus `GameClock`, `suspend` (bei Prozessen per `ProcessGroup` eingefroren), `bot_messages.read` prüft streng, der Zug läuft über das Brett des Kerns.
4. `ConsoleReport` gibt Züge und Stand aus, `pgn.to_pgn` hängt an `--pgn` an.

## Konventionen

- Keine Schachregeln in Python; alles geht über `sbm._core` und damit über den Kern.
- Fehlermeldungen des Bindings nennen die Funktion (`what`) und den Statusnamen; Ausnahmen kommen aus `sbm.errors`.
- Module mit Docstring in der ersten Zeile, der Zweck und Entscheidung nennt (z. B. `(E66)`).
- Optionale Teile (Arena, Remote, Viewer) importieren `runtime.py` und `starter.py` erst bei Bedarf; `sbm.remote` nutzt nur die Standardbibliothek.
- Fristen und Zeiten über `time.monotonic_ns`; der Referee rechnet in Nanosekunden, Nachrichten in Millisekunden.
- Plattformcode getrennt: `posix_group.py`, `windows_job.py`, `windows_processes.py` hinter `process_group.py`.
- Der Viewer darf eine Partie nie stören: Schreibfehler schalten `ViewerWindow` still ab.
- Ruff mit Zeilenlänge 100, Ziel Python 3.11, Regeln `E, F, W, I, B, UP, SIM`.

## Erweitern

### Neue Methode der Bot-API (`Board`/`Move`)

1. Funktion in `spec/api/<modul>.json` eintragen und API-Vektoren mit `tools/testvector-gen` erzeugen (siehe [Code-Karte Kern](code-kern.md), Rezept „Neue Funktion der C-Schnittstelle“).
2. C-Funktion im Kern umsetzen. Reine Bitoperationen von `Move` gehören stattdessen nach `native/move.cpp`.
3. Binding in der passenden Datei unter `src/native/` mit `query<T>`, `to_c<T>` bzw. den Hilfen aus `text.hpp` und `move_list.hpp`. Der Name in Python ist der Name aus `spec/api`.
4. Paket neu installieren (`pip install "./sdk/python[dev]"`). `test_vectors.py` ruft die neuen Vektoren über `spec/api` auf, `test_api_surface.py` prüft Art und Parameterzahl; `_core.pyi` entsteht beim Bau neu.
5. Nutzerdoku in `sdk/python/docs/` (z. B. `brett.md`, `zuege.md`) und [sdk-api.md](../komponenten/sdk-api.md) nachführen.

Für `Bot`, `Clock`, `Log` oder `run`: zuerst `spec/api/bot.json`, `clock.json`, `log.json` bzw. `runtime.json`, dann das Python-Modul; `test_runtime_surface.py` prüft die Signaturen.

### Neue Option der Arena

1. Option in `arena/cli.py` in `_parser()` mit `parser.add_argument` anlegen; Prüftypen wie `_positive` nutzen.
2. Gehört sie zur Partie, in `_settings()` an `MatchSettings` (`referee/settings.py`) weiterreichen und dort im Referee auswerten; sonst in `main()` verwenden.
3. Widersprüche zwischen Optionen als `ValueError` melden; `main` macht daraus `parser.error` (Exit 2).
4. Tests in `tests/test_arena_cli.py` bzw. dem passenden `test_arena_*.py`.
5. [lokale-entwicklung.md](../komponenten/lokale-entwicklung.md), `sdk/python/docs/arena.md` und bei Bedarf `templates/python/.vscode/tasks.json` nachführen.

### Neue Regel der Analyse

1. Regel zuerst in [statische-analyse.md](../komponenten/statische-analyse.md) und E90 festlegen.
2. Reicht eine Liste, Eintrag in `analysis/python_rules.json` (z. B. `forbidden_builtins`, `forbidden_attributes`, `modules`). Ein neues Feld braucht ein gleichnamiges Feld in `Rules` (`rules.py`).
3. Eine neue Art von Prüfung als Methode in `FileChecker` (`checker.py`), aufgerufen aus `check()`, gemeldet mit `_report(node, RULE, message)`; neue Regel-IDs als Konstante in `report.py`.
4. Bei geändertem Verhalten `ruleset` in `python_rules.json` hochzählen; der Runner legt ihn im Report ab.
5. Tests in `tests/test_analysis_rules.py` (erlaubt und verboten). Neue Python-Version des Runners verlangt keine Änderung hier.

### Release

1. Version in `sdk/core/CMakeLists.txt` (`project(sbm_core VERSION X.Y.Z …)`) setzen und committen; Kern, Paket und `sbm.__version__` übernehmen sie (E36, `test_version.py`).
2. `git tag vX.Y.Z` und `git push origin master vX.Y.Z`.
3. `.github/workflows/wheels.yml` baut mit cibuildwheel auf fünf Runnern, testet jedes Wheel mit `SBM_REQUIRE_VIEWER=1` und lädt es als Artefakt hoch.
4. Job `publish` prüft, dass die Wheels die Version des Tags tragen, und lädt sie über Trusted Publishing (Umgebung `pypi`) auf PyPI (E70).
5. Lokal vorher prüfbar mit `cibuildwheel --only cp312-win_amd64 sdk/python` (siehe `CLAUDE.md`).

## Tests

Ort: [`sdk/python/tests/`](../../sdk/python/tests/). Die Tests laufen gegen das installierte Paket; nach Änderungen neu installieren.

| Hilfsmodul | Zweck |
|------------|-------|
| `conftest.py` | Setzt den Log-Zustand vor und nach jedem Test zurück |
| `spec_files.py` | Liest `spec/api` und die Aufrufvektoren |
| `vector_codec.py` | Werte zwischen Vektor-Codierung und Python |
| `protocol_schemas.py` | Prüft Nachrichten gegen `spec/protocol/v1/` und `viewer-v1/` |
| `scripted_player.py` | Spieler nach Skript mit falscher Uhr, für Referee-Tests |
| `arena_bots.py` | Kleine Bots als Quelltext für Tests mit echten Prozessen |
| `remote_fakes.py` | Gateway-Attrappe für Remote-Tests |
| `viewer_fakes.py` | Viewer-Prozess, der aufzeichnet statt ein Fenster zu öffnen |

| Gruppe | Dateien |
|--------|---------|
| Binding gegen Spezifikation | `test_vectors.py` (alle API-Vektoren, E55), `test_api_surface.py`, `test_runtime_surface.py`, `test_objects.py`, `test_errors.py`, `test_constants.py`, `test_version.py` |
| Laufzeit | `test_run.py`, `test_game.py`, `test_channel.py`, `test_clock.py`, `test_log.py`, `test_info.py`, `test_data.py`, `test_options.py` |
| Referee und Arena | `test_referee_*.py`, `test_arena_*.py`, `test_reference_bots.py`, `test_acceptance.py` (Abnahme M1 mit echten Prozessen) |
| Analyse | `test_analysis_cli.py`, `test_analysis_rules.py`, `test_analysis_upload.py` |
| Code und Remote | `test_play_local.py`, `test_play_remote.py`, `test_remote.py` |
| Viewer | `test_viewer_game.py`, `test_viewer_messages.py`, `test_viewer_option.py`, `test_viewer_window.py`, `test_viewer_program.py` |
| Vorlage | `test_template.py` (prüft `templates/python`) |

- Befehle: `pytest sdk/python`, `ruff check sdk/python`, `ruff format --check sdk/python`; für die Vorlage zusätzlich `ruff check templates/python`.
- `test_viewer_program.py` startet das installierte `sbm-viewer` im Screenshot-Modus; ohne Programm übersprungen, mit `SBM_REQUIRE_VIEWER=1` gescheitert.
- CI-Job `python` baut ohne Viewer und testet mit Python 3.11 und 3.14 unter Linux, Windows und macOS; Job `viewer` baut mit Viewer und führt `pytest sdk/python -k viewer` aus.
