# Viewer (grafisches Fenster im SDK)

Das Programm `sbm-viewer` zeigt die Partien eines Bots auf dem Rechner des Entwicklers: live und danach Zug für Zug (E106, E107). Es gehört zum SDK, nicht zur Website; der Viewer der Website ist Teil der SPA ([frontend.md](frontend.md)). Bedienung für Nutzer: [`sdk/python/docs/viewer.md`](../../sdk/python/docs/viewer.md). Aufbau des Codes: [Code-Karte Viewer](../entwicklung/code-viewer.md).

## Aufbau

```
Bot-Programm (Python)                                   sbm-viewer (eigener Prozess)
  sbm.run / sbm.play (viewer=True)                         stdin ─► Lese-Thread ─► Session
    └─ open_window() ── startet einmal je Programm ──►                              │
  Game ─► GameView ─► ViewerWindow ── viewer-v1, eine JSON-Zeile je Nachricht ──►  GameRecord je Partie
  Log ─────────────► ViewerWindow (Listener des Logs)                               │
                                                                                SDL3 + Dear ImGui
```

| Teil | Ort | Aufgabe |
|------|-----|---------|
| Programm | `sdk/viewer` (C++20, SDL3, Dear ImGui, Regeln aus dem Kern statisch gelinkt) | Liest viewer-v1 von stdin und zeichnet Brett, Zugliste, Uhren, Suchinformation und Log |
| Spezifikation | `spec/protocol/viewer-v1/` | Nachrichten SDK → Viewer; Beispiele unter `examples/valid` und `examples/invalid`, geprüft von `spec-check` |
| Python-Seite | `sdk/python/src/sbm/viewer/` | Startet das Programm, übersetzt Partie und Log in viewer-v1 |
| Auslieferung | `sdk/python/CMakeLists.txt` (Option `SBM_VIEWER`) | Baut das Programm per `ExternalProject_Add` und legt es in jedes Wheel unter `sbm/bin` (E107) |

## Prozessmodell

- Ein Fenster je Bot-Programm für alle Partien (E107). `open_window()` startet das Programm beim ersten Aufruf; spätere Partien finden es über `active_window()`.
- Der Viewer liest stdin bis zum Ende. Das Fenster bleibt offen, solange das Bot-Programm die Pipe hält. Am Programmende wartet das SDK per `atexit`, bis der Nutzer das Fenster schließt (`wait_until_closed`); Strg+C bricht das Warten ab.
- Der Viewer läuft außerhalb der Prozessgruppe des Bots, damit das Einfrieren durch die Arena (E67) ihn nicht anhält: unter POSIX mit eigener Sitzung (`start_new_session`), unter Windows mit `CREATE_BREAKAWAY_FROM_JOB`; verweigert der Job das, startet er darin.
- Fehler beim Schreiben (Fenster geschlossen, keine Anzeige) schalten `ViewerWindow` still ab. Die Partie läuft weiter; der Viewer beeinflusst nie Zeit oder Ergebnis.
- Das Programm schreibt nichts zurück (stdout geht nach `DEVNULL`). Der Viewer ist reine Anzeige und hat keinen Rückkanal zum Bot.

## Protokoll viewer-v1

Zeilenweises JSON auf stdin, eine Nachricht je Zeile, UTF-8. Die Schemas sind maßgeblich; hier nur die Reihenfolge und die Regeln, die nicht im Schema stehen.

| Nachricht | Wann | Inhalt |
|-----------|------|--------|
| `start` | Bei `init` des Referees; jede weitere Partie im selben Fenster beginnt erneut mit `start` | `v` (immer `1`), `bot`, `color` (Seite des Bots, unten im Brett), `opponent`, `start_fen`, `initial_time_ms`, `increment_ms`, optional `discipline` |
| `move` | Jeder Halbzug, lückenlos in Reihenfolge | `ply` ab 1, `move` (UCI), `fen` danach, `by` (`bot`/`opponent`); optional `white_ms`, `black_ms`, beim eigenen Zug `elapsed_ms` und `info` |
| `log` | Jede Log-Zeile des Bots | `level` (`debug`, `info`, `warn`, `error`), `text` (höchstens 4096 Zeichen), `time` (`HH:MM:SS.mmm`, lokale Zeit) |
| `game_over` | Ende der Partie | Unverändert die Nachricht des Referees (Bot-Protokoll v1) |

Regeln:

- **Uhren:** Die Restzeiten sind der Stand des SDK. Beim eigenen Zug schätzt es die Restzeit des Bots als `remaining − elapsed + increment`; maßgeblich bleibt der Referee. Fehlende Werte übernimmt der Viewer aus dem vorherigen Halbzug.
- **Letzter Zug:** Endet die Partie mit einem Zug des Gegners, kommt dieser nicht als `turn` beim Bot an. Das SDK schickt ihn vor `game_over` als `move` des Gegners, gebildet aus `last_move`, `fen` und `ply` der `game_over`-Nachricht.
- **FEN gewinnt:** Führt ein Zug im Viewer nicht zur gesendeten FEN, übernimmt er die FEN. Ein wiederholter oder älterer `ply` wird ignoriert.
- **Log-Zuordnung:** Eine Log-Zeile gehört zu dem Halbzug, der bei ihrem Eintreffen der letzte war. Zeilen vor dem ersten `start` hebt der Viewer für die erste Partie auf; ein `move` vor dem ersten `start` wird verworfen.
- **Robustheit:** Eine unlesbare Zeile wird zu einer Warnung im Log des Fensters. Zeilen über 1 MiB werden verworfen. Eine unlesbare `start_fen` ersetzt der Viewer durch die Grundstellung.
- **Kürzen:** Das SDK kürzt den Bot-Namen auf 64 und Log-Texte auf 4096 Zeichen, damit jede Zeile dem Schema entspricht.
- **Version:** SDK und Viewer liegen im selben Paket, deshalb gibt es keine Aushandlung. Eine neue Version ändert `v` und das Verzeichnis (`viewer-v2`).

Eine neue Nachricht oder ein neues Feld kommt zuerst ins Schema samt gültigem und ungültigem Beispiel (`spec-check spec`). Danach folgen der Leser im Viewer (`src/model/messages.cpp` mit `tests/messages_test.cpp`), die Python-Seite (`sbm/viewer/messages.py` mit `tests/test_viewer_messages.py`) und diese Datei.

## Auf dem Server ausgeschlossen

Die Website zeigt keine Viewer-Fenster (E108); zwei Schichten sorgen dafür:

- `sandbox/python.cfg` setzt `SBM_NO_VIEWER=1`. Dann öffnet `open_window()` nichts, ohne Meldung. Ein hochgeladener Bot darf `viewer=True` daher behalten.
- Die Images bauen das SDK mit `-C cmake.define.SBM_VIEWER=OFF` (`deploy/python.Dockerfile`). Das Programm fehlt dort also ganz; `open_window()` würde nur warnen.

Fehlt das Programm in einer Installation, schreibt das SDK einmal eine Warnung ins Log, und die Partie läuft ohne Fenster.

## Bauen

| Option | Standard | Wirkung |
|--------|----------|---------|
| `SBM_VIEWER_BUILD_APP` | `ON` | `OFF` baut nur die Bibliothek `sbm_viewer_model` ohne SDL3 und ImGui, etwa für Tests ohne Grafik |
| `SBM_VIEWER_BUILD_TESTS` | `ON`, wenn `sdk/viewer` das Hauptprojekt ist | Modelltests mit ctest |
| `SBM_VIEWER_INSTALL_DIR` | `bin` | Zielordner des Programms; das Python-SDK setzt `bin` im Paket |
| `SBM_VIEWER_LICENSE_DIR` | `share/sbm-viewer/licenses` | Lizenzen von SDL3, Dear ImGui, nlohmann/json und DejaVu; im Wheel `bin/licenses` |
| `SBM_VIEWER` (Python-SDK) | `ON` | `OFF` baut das Wheel ohne Viewer, wie in den CI-Jobs `python` und `services` und in den Images |

- Abhängigkeiten lädt `cmake/dependencies.cmake` mit fester Version und SHA-256. Die Schrift bettet `cmake/embed_file.cmake` ins Programm ein (Herkunft in `assets/README.md`).
- Das Programm bringt die C++-Laufzeit statisch mit (MSVC `MultiThreaded`, MinGW `-static-libstdc++`), weil es neben Bots jeder Sprache läuft.
- Befehle stehen in `CLAUDE.md` unter „Viewer bauen und testen“.

## Ohne Fenster prüfen

`--screenshot DATEI` liest stdin bis zum Ende, zeichnet den Stand, speichert ihn als BMP und beendet das Programm. Mit `SDL_VIDEO_DRIVER=offscreen` braucht das keine Anzeige:

```
SDL_VIDEO_DRIVER=offscreen sbm-viewer --screenshot bild.bmp < partie.jsonl
```

## Tests und CI

| Ebene | Ort | Was |
|-------|-----|-----|
| Modell | `sdk/viewer/tests/` (ctest) | Nachrichten lesen, Partieaufzeichnung, Navigation, Sitzung mit mehreren Partien, Zeit- und Zugtexte |
| Python-Seite | `sdk/python/tests/test_viewer_*.py`, Attrappen in `viewer_fakes.py` | Nachrichten gegen das Schema, Fenster und Partie ohne echtes Programm, Argument `viewer=` und `SBM_NO_VIEWER` |
| Programm | `sdk/python/tests/test_viewer_program.py` | Startet das installierte `sbm-viewer` im Screenshot-Modus; ohne Programm übersprungen, mit `SBM_REQUIRE_VIEWER=1` gescheitert |

CI-Job `viewer` in `.github/workflows/ci.yml`: Modelltests mit `SBM_VIEWER_BUILD_APP=OFF`, danach das Python-SDK mit Viewer unter Linux, Windows und macOS und `pytest sdk/python -k viewer` mit `SBM_REQUIRE_VIEWER=1`. `wheels.yml` setzt `SBM_REQUIRE_VIEWER=1` für die Tests jedes Wheels (`sdk/python/pyproject.toml`).
