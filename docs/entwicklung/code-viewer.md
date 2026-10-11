# Code-Karte: Viewer

Der Viewer unter `sdk/viewer` ist das Programm `sbm-viewer` (C++20, SDL3, Dear ImGui). Es zeigt die Partien eines Bot-Programms live und zum Vor- und Zurückspulen (E106–E108). Das SDK startet es und schreibt Zeilen nach viewer-v1 auf seine Standardeingabe; Schachregeln kommen aus dem Kern. Konzepte: [viewer.md](../komponenten/viewer.md) und [`spec/protocol/viewer-v1/`](../../spec/protocol/viewer-v1/).

## Einstieg

| Einstieg | Ort | Zweck |
|----------|-----|-------|
| `main` | [`src/app/main.cpp`](../../sdk/viewer/src/app/main.cpp) | Hauptschleife: Zeilen lesen, Modell fortschreiben, Bild zeichnen, auf Ereignisse warten |
| `Session::apply_line` | [`src/model/session.cpp`](../../sdk/viewer/src/model/session.cpp) | Eingang des Modells: eine Zeile viewer-v1 |
| `sbm_viewer_model_tests` | [`tests/`](../../sdk/viewer/tests/) | Modelltests ohne Fenster (ctest `viewer_model`) |
| `ExternalProject_Add(sbm_viewer …)` | [`sdk/python/CMakeLists.txt`](../../sdk/python/CMakeLists.txt) | Baut den Viewer ins Python-Paket nach `sbm/bin` (E107) |
| `open_window` | [`sdk/python/src/sbm/viewer/window.py`](../../sdk/python/src/sbm/viewer/window.py) | Python-Seite: startet das Programm und schreibt die Nachrichten |

Lesereihenfolge:

1. `spec/protocol/viewer-v1/viewer_message.schema.json` mit den Schemas je Nachricht und `examples/`: was ankommt.
2. `src/model/messages.hpp`, dann `game_record.hpp` und `session.hpp`: Datenmodell.
3. `src/model/navigation.hpp`: welcher Halbzug welcher Partie gezeigt wird.
4. `src/app/main.cpp`, `view_state.hpp`, `frame.cpp`: Schleife und Aufbau des Fensters.
5. Ein Baustein wie `move_list.cpp` oder `controls.cpp`.
6. `sdk/python/src/sbm/viewer/game_view.py` und `window.py`: wer die Zeilen schreibt.

## Ziele und Optionen

| Ziel / Option | Wirkung |
|---------------|---------|
| `sbm_viewer_model` | Statische Bibliothek ohne Fenster (`src/model/*.cpp`), öffentlich gegen `sbm`, privat gegen nlohmann/json; Include-Wurzel `src` |
| `sbm-viewer` | Programm (`src/app/*.cpp`, unter Windows als `WIN32`-Programm ohne Konsole) gegen `sbm_viewer_model` und `sbm_viewer_imgui` |
| `sbm_viewer_imgui` | Dear ImGui mit den Backends `imgui_impl_sdl3` und `imgui_impl_sdlrenderer3`, `IMGUI_DISABLE_DEMO_WINDOWS` |
| `SBM_VIEWER_BUILD_TESTS` | Standard: nur wenn `sdk/viewer` das Hauptprojekt ist |
| `SBM_VIEWER_BUILD_APP` | Standard `ON`; `OFF` baut nur Modell und Tests, ohne SDL3 und ImGui |
| `SBM_VIEWER_INSTALL_DIR` | Zielordner des Programms, Standard `bin`; das Python-SDK setzt `bin` unter seinem Präfix |
| `SBM_VIEWER_LICENSE_DIR` | Zielordner der Lizenzen von SDL3, Dear ImGui, nlohmann/json und DejaVu |

- Der Kern kommt über `add_subdirectory(../core)` mit `SBM_BUILD_TESTS=OFF` und `SBM_SHARED=OFF`; er ist also statisch im Programm.
- Die C++-Laufzeit ist statisch gelinkt (MSVC `MultiThreaded`, MinGW `-static-libgcc -static-libstdc++`), weil das Programm neben Bots jeder Sprache läuft.
- Ausgaben landen in `build/bin`. Jedes Ziel ruft `sbm_enable_warnings` aus dem Kern auf (Warnungen als Fehler).
- [`cmake/dependencies.cmake`](../../sdk/viewer/cmake/dependencies.cmake) holt nlohmann/json 3.12.0, SDL 3.4.16 und Dear ImGui 1.92.9b per `FetchContent` mit SHA-256. SDL baut statisch, nur Video und Rendering; Audio, GPU, Joystick und Ähnliches sind aus, ebenso Wayland, Vulkan und KMSDRM. Unter Linux läuft das Fenster über X11 (unter Wayland per XWayland); ohne die Header von libX11 und libXext bricht CMake früh ab, statt still ohne Fenstersystem zu bauen.
- [`cmake/embed_file.cmake`](../../sdk/viewer/cmake/embed_file.cmake) stellt `sbm_viewer_embed_file(target input symbol)` bereit und erzeugt aus der Schrift `assets/DejaVuSans-viewer.ttf` eine C++-Datei mit Byte-Array (`sbm_viewer_font`, `sbm_viewer_font_size`). Die Schrift ist eine Teilmenge von DejaVu Sans mit den Schachfiguren; Herkunft in [`assets/README.md`](../../sdk/viewer/assets/README.md).

## Module

### Modell (`src/model/`, Ziel `sbm_viewer_model`)

| Modul | Aufgabe |
|-------|---------|
| `messages.hpp`/`.cpp` | Structs `StartMessage`, `MoveMessage` (mit optionalem `SearchInfo`), `LogMessage` (`LogLevel`), `GameOverMessage`; `Message` als `std::variant`. `parse_line` liefert `ParsedLine` mit Nachricht oder Fehlertext; unbekannte Felder werden übergangen |
| `position.hpp`/`.cpp` | `Position`: hält ein `sbm_board` des Kerns (`unique_ptr` mit `sbm_board_free`); `from_fen`, `piece_at`, `side_to_move`, `fullmove_number`, `checked_king`, `fen`, `san`, `play`. Keine eigenen Regeln |
| `game_record.hpp`/`.cpp` | `GameRecord`: eine Partie mit Stellungen je Halbzug, `PlyRecord` (UCI, SAN, Uhren, Suchinfo), `LogLine` (Nachricht mit Halbzug) und Ergebnis. `position(ply)`, `ply(ply)`, `clocks(ply)` (übernimmt fehlende Uhren vom letzten bekannten Stand), `add_move`, `add_log`, `finish` |
| `session.hpp`/`.cpp` | `Session`: alle Partien eines Programms. `apply_line` übergeht Leerzeilen und macht aus unlesbaren Zeilen eine Warnung im Log; `start` legt eine neue Partie an, Logs vor dem ersten `start` warten in `early_logs_` |
| `navigation.hpp`/`.cpp` | `Navigation`: gewählte Partie und gezeigter Halbzug. Ohne Festlegung (`live()`) folgt die Anzeige dem neuesten Zug; `go_to`, `step`, `first` legen fest, `last` löst. Wer die neueste Partie ansieht, folgt neuen Partien (`follow_newest_`) |
| `notation.hpp`/`.cpp` | `move_rows` (Zeilen der Zugliste, auch wenn Schwarz beginnt), `score_text` (Bauerneinheiten oder Matt), `nodes_text`, `pv_text` (Hauptvariante als SAN ab einer Stellung) |
| `time_text.hpp`/`.cpp` | `clock_text` (Uhr), `duration_text` (Bedenkzeit eines Zuges) |

### Fenster (`src/app/`, Ziel `sbm-viewer`)

| Modul | Aufgabe |
|-------|---------|
| `main.cpp` | Liest `--screenshot DATEI`, öffnet das Fenster, startet `InputReader`, führt die Schleife (siehe Ablauf) |
| `window.hpp`/`.cpp` | `Window`: SDL-Fenster und Renderer mit VSync, Größe nach Inhaltsskalierung des Bildschirms, eigenes Wecksignal (`SDL_RegisterEvents`), ImGui-Setup, `begin_frame`/`end_frame` (optional mit Bildschirmfoto), `handle_events(timeout_ms)` liefert `false` beim Schließen |
| `input_reader.hpp`/`.cpp` | `InputReader`: liest stdin in einem eigenen Thread, sammelt Zeilen und weckt die Schleife über einen Rückruf; `take_lines`, `closed` |
| `view_state.hpp` | `ViewState`: `Navigation`, `flipped`, Zeitpunkt der letzten Änderung, Ende der Eingabe, Zahl der gezeigten Logzeilen |
| `frame.hpp`/`.cpp` | `draw_frame`: links Brett mit Spielerleisten und Bedienelementen, rechts Partieleiste, Zugliste, Details und Log; Breite der rechten Seite 38 % in festen Grenzen |
| `board_view.hpp`/`.cpp` | `draw_board`: Felder, Figuren aus der Schrift, letzter Zug, Schach |
| `players_view.hpp`/`.cpp` | `PlayerBar`, `draw_player_bar`, `player_bar_height`: Name, Bot-Kennzeichen, Uhr, laufende Uhr hervorgehoben |
| `controls.hpp`/`.cpp` | `draw_controls` (Knöpfe) und `handle_keys`: Pfeil links/rechts, Pos1/Ende, `F` dreht das Brett, Mausrad über dem Brett |
| `game_bar.hpp`/`.cpp` | `draw_game_bar`: Partie und Ergebnis, Auswahlliste der Partien eines Programms |
| `move_list.hpp`/`.cpp` | `draw_move_list`: Zugliste mit Sprung per Klick |
| `details_view.hpp`/`.cpp` | `draw_details`: Suchinfo, Bedenkzeit und Uhren zum gezeigten Halbzug, Ergebnis |
| `log_view.hpp`/`.cpp` | `draw_log`: Logzeilen der Partie mit Farbe je Stufe, rollt bei neuen Zeilen mit |
| `theme.hpp`/`.cpp` | Farben in `colors::` und `apply_theme(scale)` |
| `font.hpp`/`.cpp` | `load_font`: lädt die eingebettete Schrift in ImGui |
| `screenshot.hpp`/`.cpp` | `save_bmp`: liest den Renderer aus und speichert BMP (für Tests) |

### Python-Seite (`sdk/python/src/sbm/viewer/`)

| Modul | Aufgabe |
|-------|---------|
| `process.py` | `PROGRAM`, `program_path()` (`sbm/bin` im Paket), `start_process` (unter Windows mit `CREATE_BREAKAWAY_FROM_JOB`, damit das Fenster den Job der Arena überlebt), `encode` |
| `window.py` | `ViewerWindow` und `open_window`/`active_window`: ein Fenster je Programm; `SBM_NO_VIEWER` schaltet ab; Schreibfehler schließen still; beim Programmende wartet `atexit`, bis das Fenster zu ist |
| `game_view.py` | `GameView`: übersetzt Ereignisse von `sbm.game.Game` (`started`, `opponent_moved`, `own_move`, `ended`) in Nachrichten |
| `messages.py` | `VIEWER_VERSION`, Längengrenzen, Abbildung der Logstufen, Bauer für `start`, `move`, `log`, `game_over` |

Eingeschaltet wird der Viewer über `sbm.run(MyBot, viewer=True)` (`runtime.py`) bzw. `sbm.play(..., viewer=True)` (`starter.py`); `log.py` reicht jede Logzeile an das offene Fenster weiter.

## Ablauf

1. `sbm.run(..., viewer=True)` ruft `open_window`. Das startet `sbm/bin/sbm-viewer` mit einer Pipe als stdin. Fehlt das Programm, warnt das SDK einmal und der Bot läuft ohne Fenster.
2. `Game` meldet Start, Züge und Ende an `GameView`; das baut Nachrichten nach viewer-v1 und schreibt sie über `ViewerWindow._send` als JSON-Zeilen.
3. Im Viewer sammelt `InputReader` die Zeilen und schiebt ein Weck-Ereignis in die SDL-Queue.
4. Die Schleife in `main.cpp` prüft zuerst `closed()`, holt dann alle Zeilen und gibt sie an `Session::apply_line`. Kam eine Partie oder ein Zug dazu, setzt sie `changed_at_ms`; `navigation.games_changed` springt bei Bedarf zur neuen Partie; der Fenstertitel wird „Weiß vs Schwarz – SchachBotManager Viewer“.
5. `draw_frame` zeichnet die gewählte Partie beim Halbzug `navigation.shown(...)`. Danach wartet die Schleife auf Ereignisse: 100 ms, solange eine Partie läuft (die Uhr tickt), sonst 500 ms.
6. Endet stdin (das Bot-Programm ist fertig), endet der Viewer. Damit das Fenster nach der letzten Partie offen bleibt, wartet das SDK per `atexit` (`wait_until_closed`), bis der Nutzer es schließt; Strg+C beendet das Warten.
7. Mit `--screenshot DATEI` zeichnet das Programm nach dem Ende der Eingabe noch drei Bilder, speichert das letzte als BMP und endet mit 0 bzw. 1 bei einem Fehler.

## Konventionen

- Das Modell kennt weder SDL noch ImGui und ist allein testbar; alles, was sich ohne Fenster prüfen lässt, gehört dorthin.
- Regeln, SAN und FEN nur über `Position` und damit über den Kern; der Viewer rechnet nichts selbst nach.
- Eingaben sind tolerant: unbekannte Felder übergehen, unlesbare Zeilen als Warnung zeigen, Züge mit kleinerem oder gleichem `ply` übergehen, nach `game_over` keine Züge mehr annehmen. Weicht die eigene Stellung von der `fen` der Nachricht ab, gilt die `fen`.
- Ein Baustein je Datei unter `src/app/`, jeweils eine `draw_*`-Funktion mit `GameRecord` und `ViewState`; Farben nur aus `theme.hpp`.
- Namensraum `sbm_viewer`, Dateinamen in `snake_case`, Format nach `.clang-format` im Repo.
- Abhängigkeiten nur mit fester Version und SHA-256 in `cmake/dependencies.cmake`; ihre Lizenzen werden mit installiert.
- Der Viewer darf den Bot nie stören: das SDK schaltet ihn bei Schreibfehlern still ab, ein fehlendes Programm ergibt nur eine Warnung; auf dem Server ist er durch `SBM_NO_VIEWER` aus (E108).

## Erweitern

### Neues Feld in einer Nachricht

1. **Spezifikation:** Feld im Schema unter `spec/protocol/viewer-v1/` eintragen, Beispiel in `examples/` ergänzen, `spec-check spec`. Felder nur hinzufügen; eine inkompatible Änderung braucht `viewer-v2`.
2. **Python:** Feld in `sbm/viewer/messages.py` schreiben, gegebenenfalls in `game_view.py` aus `Game` holen. `tests/test_viewer_messages.py` prüft gegen das Schema.
3. **Modell:** Feld im passenden Struct in `messages.hpp`, lesen in `messages.cpp`, ablegen in `GameRecord`. Test in `tests/messages_test.cpp` bzw. `game_record_test.cpp`.
4. **Anzeige:** im passenden Baustein unter `src/app/`, meist `details_view.cpp` oder `players_view.cpp`. Mit `--screenshot` ansehen.
5. **Doku:** [viewer.md](../komponenten/viewer.md) und bei neuer Festlegung `docs/00_entscheidungen.md`.

### Neue Bedienung oder neuer Baustein

1. Logik, die sich ohne Fenster ausdrücken lässt (etwa ein neuer Sprung in `Navigation`), ins Modell mit Test in `navigation_test.cpp`.
2. Taste oder Knopf in `controls.cpp`; neuen Zustand der Ansicht in `ViewState`.
3. Neuer Baustein als eigenes Paar `.hpp`/`.cpp` unter `src/app/`, in `CMakeLists.txt` unter `sbm-viewer` eintragen und aus `frame.cpp` aufrufen.
4. Tastenkürzel in [viewer.md](../komponenten/viewer.md) und in der Nutzerdoku des SDK nachführen.

### Viewer für ein weiteres SDK

1. Das SDK legt das Programm in sein Paket (wie `sbm/bin` im Python-Wheel) und startet es mit einer Pipe als stdin; unter Windows so, dass es einen Job der Arena überlebt.
2. Es schreibt Nachrichten nach viewer-v1 und schaltet sich bei `SBM_NO_VIEWER` oder Schreibfehlern still ab.
3. Die Tests des SDK prüfen die Nachrichten gegen das Schema und starten das Programm einmal mit `--screenshot`.

## Tests

| Test | Ort | Was |
|------|-----|-----|
| `viewer_model` (ctest) | [`tests/`](../../sdk/viewer/tests/) | `messages_test` (Lesen, Fehler, unbekannte Felder), `game_record_test` (Züge, Uhren, FEN-Übernahme), `navigation_test` (Live und Festlegen, Partiewechsel), `session_test` (frühe Logs, unlesbare Zeilen), `text_test` (Notation, Zeiten); Makro `CHECK` aus `sdk/core/tests/unit/check.hpp` |
| `test_viewer_messages.py` | `sdk/python/tests/` | Nachrichten der Python-Seite gegen die Schemas |
| `test_viewer_game.py`, `test_viewer_window.py`, `test_viewer_option.py` | `sdk/python/tests/` | `GameView`, `ViewerWindow` und die Option `viewer=` mit Attrappen aus `viewer_fakes.py` |
| `test_viewer_program.py` | `sdk/python/tests/` | Startet das installierte Programm mit SDL-Treiber `offscreen` und `--screenshot` und prüft, dass ein BMP entsteht; ohne Programm übersprungen, mit `SBM_REQUIRE_VIEWER=1` gescheitert |

Befehle (aus dem Repo-Wurzelverzeichnis):

```
cmake -S sdk/viewer -B build/viewer -DSBM_VIEWER_BUILD_APP=OFF   # nur Modell, ohne SDL3/ImGui
cmake --build build/viewer --config Release
ctest --test-dir build/viewer -C Release --output-on-failure

cmake -S sdk/viewer -B build/viewer                              # mit Programm
SDL_VIDEO_DRIVER=offscreen build/viewer/bin/sbm-viewer --screenshot bild.bmp < partie.jsonl
```

Unter Windows mit `-G "Visual Studio 17 2022"`; das Programm liegt dann unter `build/viewer/bin/Release/`. Unter Linux braucht der Bau des Programms `libx11-dev libxext-dev libxcursor-dev libxi-dev libxrandr-dev libxfixes-dev`.

CI-Job `viewer` baut und testet das Modell unter Linux, Windows und macOS, installiert dann das Python-SDK mit Viewer und führt `pytest sdk/python -k viewer` mit `SBM_REQUIRE_VIEWER=1` aus. Job `native-format` prüft `sdk/viewer/src` und `sdk/viewer/tests` mit clang-format. `wheels.yml` legt das Programm in jedes Wheel.
