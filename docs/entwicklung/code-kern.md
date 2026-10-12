# Code-Karte: C++-Kern

Der Kern unter `sdk/core` ist die einzige Implementierung der Schachregeln (A11, E50–E57). Er baut die Bibliothek `sbm` mit flacher C-Schnittstelle; Python-SDK, Viewer, Referee und Arena nutzen ihn darüber. Konzepte: [kern-c-schnittstelle.md](../komponenten/kern-c-schnittstelle.md) (Handles, Puffer, Statuscodes) und [sdk-api.md](../komponenten/sdk-api.md) (API-Schichten).

## Einstieg

| Einstieg | Ort | Zweck |
|----------|-----|-------|
| `project(sbm_core VERSION …)` | [`CMakeLists.txt`](../../sdk/core/CMakeLists.txt) | Version des Kerns und aller SDKs (E36), Ziele `sbm_engine` und `sbm` |
| `sbm/sbm.h` | [`include/sbm/`](../../sdk/core/include/sbm/) | Einziger Header, den Bindings einbinden |
| `sbm_vector_tests` | [`tests/vectors/main.cpp`](../../sdk/core/tests/vectors/main.cpp) | Prüft alle Vektoren unter `spec/testvectors/` über die C-Schnittstelle |
| `sbm_capi_tests`, `sbm_engine_tests` | [`tests/unit/`](../../sdk/core/tests/unit/) | Regeln der C-Schnittstelle bzw. interne Module |

Lesereihenfolge:

1. `include/sbm/types.h` und `status.h`: Typen, Codes, Puffergrößen.
2. `src/position.hpp`, `src/move.hpp`, `src/game.hpp`: Datenmodell und Verlauf.
3. `src/movegen.hpp` mit `attacks`, `threats`, `play`: Zugerzeugung.
4. `src/capi/guard.hpp`, `read_board.hpp`, `output.hpp`, dann ein Paar Header/Implementierung, etwa `include/sbm/board_state.h` und `src/capi/board_state.cpp`.
5. `tests/vectors/call.hpp` und `run_calls.cpp`: wie ein Vektor auf einen C-Aufruf abgebildet wird.

## Ziele und Optionen

| Ziel / Option | Wirkung |
|---------------|---------|
| `sbm_engine` | Statische Bibliothek mit den Regeln (`src/*.cpp`), ohne C-Schnittstelle; `src/` ist öffentliches Include-Verzeichnis, Sichtbarkeit `hidden` |
| `sbm` | C-Schnittstelle (`src/capi/*.cpp`) auf `sbm_engine`; privat `SBM_BUILD` und `SBM_VERSION_STRING` (aus der Projektversion) |
| `SBM_SHARED` | Standard `ON` (gemeinsame Bibliothek); `OFF` baut statisch und setzt öffentlich `SBM_STATIC`. Python-SDK und Viewer setzen `OFF` |
| `SBM_BUILD_TESTS` | Standard: nur wenn `sdk/core` das Hauptprojekt ist |
| `SBM_SLOW_TESTS` | Standard `OFF`; `ON` ruft `sbm_vector_tests --slow` auf und nimmt die langsamen Perft-Vektoren dazu |
| `SBM_TESTVECTORS_DIR` | Ordner der Vektoren, Standard `spec/testvectors` im Repo |

- C++20 und C11. Ausgaben landen in `build/bin` und `build/lib`, damit unter Windows Tests und DLL im selben Ordner liegen.
- MinGW linkt die C++-Laufzeit statisch.
- [`cmake/warnings.cmake`](../../sdk/core/cmake/warnings.cmake) stellt `sbm_enable_warnings(target)` bereit: MSVC `/W4 /WX /permissive- /utf-8`, sonst `-Wall -Wextra -Wpedantic -Werror`. Jedes Ziel ruft sie auf.

## Module

### Öffentliche Header (`include/sbm/`)

| Modul | Aufgabe |
|-------|---------|
| `export.h` | `SBM_API` (Export/Import je Plattform, leer bei `SBM_STATIC`), `SBM_BEGIN_DECLS`/`SBM_END_DECLS` |
| `types.h` | Typedefs (`sbm_move`, `sbm_bitboard`, `sbm_bool` …), Codes aus E34, E35, E45, E47, Puffergrößen |
| `status.h` | Enum `sbm_status`, `sbm_status_name` |
| `version.h` | `SBM_ABI_VERSION`, `sbm_abi_version`, `sbm_version` |
| `move.h` | `Move.parse` und `Move.uci` |
| `board.h` | Handle anlegen, kopieren, freigeben; FEN, Hash, Verlauf, Text |
| `board_query.h` | Einzelne Eigenschaften der Stellung |
| `board_moves.h` | Züge erzeugen, prüfen, ausführen, zurücknehmen; SAN |
| `board_state.h` | Endbedingungen |
| `board_raw.h` | Bitboards und Felder |
| `sbm.h` | Bindet alle Header ein |

### Regeln (`src/`, Ziel `sbm_engine`)

| Modul | Aufgabe |
|-------|---------|
| `bitboard.hpp` | Hilfen für Felder und Bitboards |
| `piece.hpp` | `Color`, `PieceType` |
| `notation.hpp` | Buchstaben für Figuren und Felder |
| `move.hpp` | Zugcodierung nach E34 mit Flags |
| `move_list.hpp` | Zugliste mit fester Kapazität 256 (`kMaxMoves`) |
| `position.hpp`/`.cpp` | Eine Stellung: Figuren, Zugrecht, Rochaderechte, En-passant-Feld, Zähler |
| `attacks.hpp`/`.cpp` | Angriffsmengen mit klassischen Strahlen (E57), `between`, `line_through` |
| `threats.hpp`/`.cpp` | `attackers_of`, `is_attacked`, `attacks_from`, `checkers`, `pinned` |
| `en_passant.hpp`/`.cpp` | `is_legal_en_passant`, `legal_en_passant_square` |
| `movegen.hpp`/`.cpp` | `generate_legal_moves`, `generate_legal_captures`, `find_legal_move`, `generate_moves_from` (pseudo-legal für eine Figur, E188); ein `Generator` mit Modus legal/pseudo-legal und Maske der Ausgangsfelder |
| `play.hpp`/`.cpp` | `play_move`, `play_null_move`; Rochademasken, Zähler bleiben bei `INT32_MAX` stehen |
| `game.hpp`/`.cpp` | `Game` mit Verlauf als Kopien (`HistoryEntry{before, move}`, E57); `make`, `make_null`, `undo` |
| `repetition.hpp`/`.cpp` | `repetition_count` über den Verlauf |
| `material.hpp`/`.cpp` | `has_insufficient_material` nach den Regeln von python-chess |
| `end_conditions.hpp`/`.cpp` | `is_check`, `is_checkmate`, `is_stalemate`, `is_fifty_move_rule`, `is_insufficient_material`, `is_draw`, `is_game_over` |
| `fen.hpp`, `fen_parse.cpp`, `fen_write.cpp` | FEN lesen (mit den Prüfungen von `Board.from_fen`) und schreiben |
| `uci.hpp`/`.cpp` | `parse_uci`, `write_uci` |
| `san.hpp`/`.cpp` | `write_san` mit Mehrdeutigkeitsauflösung wie python-chess |
| `hash.hpp`/`.cpp` | `polyglot_hash`, bei Abfrage berechnet (E57) |
| `polyglot_keys.hpp`/`.cpp` | Die 781 Polyglot-Schlüssel |
| `text.hpp`/`.cpp` | `write_text`: Brett als Text |

### C-Schnittstelle (`src/capi/`, Ziel `sbm`)

| Modul | Aufgabe |
|-------|---------|
| `guard.hpp` | `guarded(...)`: fängt `std::bad_alloc` als `SBM_OUT_OF_MEMORY`, alles andere als `SBM_INTERNAL_ERROR` (E52) |
| `board_handle.hpp` | `struct sbm_board { sbm::Game game; }` |
| `read_board.hpp` | `read_board(board, out, lambda)`: Form aller Funktionen, die einen Wert lesen |
| `arguments.hpp` | `valid_square`, `valid_color`, `valid_piece_type` |
| `output.hpp`/`.cpp` | `write_text`, `write_moves`, `valid_move_output` nach den Pufferregeln (E51) |
| `board.cpp` | `board.h` |
| `board_query.cpp` | `board_query.h` |
| `board_moves.cpp` | `board_moves.h`; `make_move` löst den Zug über `find_legal_move` auf, `undo_*` prüfen die Art des letzten Verlaufseintrags |
| `board_state.cpp` | `board_state.h` |
| `board_raw.cpp` | `board_raw.h` |
| `move.cpp` | `move.h` |
| `status.cpp` | `sbm_status_name` |
| `version.cpp` | `sbm_abi_version`, `sbm_version` |

## Ablauf

Ein Aufruf aus einem Binding, z. B. `board.is_check()` in Python:

1. Das Binding ruft `sbm_board_is_check(const sbm_board*, sbm_bool*)` aus `include/sbm/board_state.h`.
2. `src/capi/board_state.cpp` reicht an `read_board` weiter. Das prüft Nullzeiger (`SBM_INVALID_ARGUMENT`) und führt das Lambda in `guarded` aus.
3. Das Lambda ruft `sbm::is_check(game.position())` aus `end_conditions.cpp`; das nutzt `threats` und `attacks`.
4. Der Wert geht über den Ausgabezeiger zurück, der Status über den Rückgabewert. Bei einem Fehler bleibt die Ausgabe unverändert.

Ein Zug mit `sbm_board_make_move`:

1. `board_moves.cpp` sucht den übergebenen Zugwert mit `find_legal_move` (vergleicht Von, Nach und Umwandlung) in den legalen Zügen; fehlt er, folgt `SBM_ILLEGAL_MOVE`.
2. `Game::make` legt die Stellung vorher als `HistoryEntry` ab und ruft `play_move`.
3. `undo_move` stellt die gespeicherte Stellung wieder her; steht ein Nullzug oben, folgt `SBM_INVALID_STATE` (ebenso umgekehrt bei `undo_null_move`).

## Konventionen

- Jede C-Funktion liefert `sbm_status` (außer `sbm_board_free`) und prüft zuerst Nullzeiger; Ergebnisse gehen über Ausgabezeiger am Ende der Parameterliste.
- Der Körper läuft immer in `guarded`; C++-Ausnahmen verlassen den Kern nie.
- Bereichsprüfungen nur über `capi/arguments.hpp`, Textausgaben nur über `write_text`, Zuglisten nur über `write_moves`.
- Namen: `sbm_board_<name>` für `Board.<name>`, `Board.create` wird zu `sbm_board_new`. Ein Header, eine Datei in `capi/`, eine Datei in `spec/api/` und eine Handler-Datei in `tests/vectors/` gehören zusammen.
- Die C-Schnittstelle enthält keine Schachlogik; Regeln liegen nur in `sbm_engine`.
- Kein veränderlicher globaler Zustand; feste Tabellen sind `const`.
- `static_assert(sbm::kMaxMoves == SBM_MAX_MOVES)` verbindet interne und öffentliche Grenzen.
- Header bleiben C11 und als C++20 übersetzbar.

## Erweitern

### Neue Funktion der C-Schnittstelle

1. **Spezifikation:** Funktion in der passenden Datei unter `spec/api/` eintragen (`name`, `kind`, `owner`, `params`, `returns`, `errors`, `description`; Schema `api.schema.json`). `spec-check spec` prüfen.
2. **Vektoren:** In `tools/testvector-gen/src/testvector_gen` die Fälle im Modul `cases/api_<datei>.py` ergänzen (`Case(...)` mit `expect` bzw. `Raises(...)`) und in `oracle/<datei>.py` den Handler für `"Owner.name"` über python-chess anlegen. Je Funktion ein Erfolgsvektor und einer je deklariertem Fehler (E55). `testvector-gen spec` schreibt `spec/testvectors/api/*.json`; `testvector-gen spec --check --perft fast` und `spec-check spec` müssen grün sein.
3. **Header:** Deklaration mit `SBM_API` im passenden Header unter `include/sbm/`; neue Konstanten in `types.h`. Innerhalb von `SBM_ABI_VERSION` nur hinzufügen, nichts ändern. Bei neuen Codes `tests/header_check.c` ergänzen.
4. **Regel (falls nötig):** in `src/` als interne Funktion.
5. **C-Schnittstelle:** Implementierung in der passenden Datei unter `src/capi/` mit `read_board` bzw. `guarded`, Argumentprüfung und Ausgabehilfen.
6. **Vektor-Runner:** Handler in `tests/vectors/calls_<datei>.cpp` unter `registry["Owner.name"]` eintragen. Fehlt er, scheitert der Lauf mit „no handler for …“. Neue Statuscodes gehören in `kErrorStatus` (`run_calls.cpp`).
7. **Unit-Tests:** Puffer- oder Zeigerfälle, die kein Vektor abdeckt, in `tests/unit/capi_*_test.cpp`.
8. **Binding:** Funktion im Python-SDK binden ([Code-Karte Python-SDK](code-python-sdk.md)); `test_vectors.py` und `test_api_surface.py` greifen sie über `spec/api` auf.
9. **Doku:** Tabelle in [kern-c-schnittstelle.md](../komponenten/kern-c-schnittstelle.md) und [sdk-api.md](../komponenten/sdk-api.md) nachführen, bei neuer Festlegung `docs/00_entscheidungen.md`.

### Regeländerung

1. Die Bedeutung steht in `spec/api/*.json` (Feld `description`) bzw. in einer Entscheidung. Zuerst dort ändern; eine Abweichung von python-chess als Entscheidung festhalten.
2. Testfälle in `tools/testvector-gen/src/testvector_gen/cases/` ergänzen (Regeln in `rules.py`, FEN in `fen.py`, SAN in `san.py`, sonst `api_*.py`). Weicht die Regel von python-chess ab, muss der Generator sie nachbilden, wie `fen_rules.py` es für `Board.from_fen` tut. Danach `testvector-gen spec`.
3. Die Regel in `src/` ändern, meist in `movegen`, `play`, `end_conditions`, `material`, `fen_parse` oder `san`.
4. Kern bauen und alle Tests mit `-DSBM_SLOW_TESTS=ON` laufen lassen; für Perft-Änderungen `testvector-gen spec --check --perft all`.
5. Python-SDK neu installieren und `pytest sdk/python` ausführen. Referee und Viewer nutzen dieselben Regeln, sie brauchen keine eigene Änderung.

## Tests

| Test (ctest) | Programm | Was |
|--------------|----------|-----|
| `vectors` | `sbm_vector_tests [--slow] <dir>` | Alle `*.json` unter `spec/testvectors/` (ohne `*.schema.json`), sortiert, nach `$schema` auf Perft oder Aufrufe verteilt |
| `engine` | `sbm_engine_tests` | Interne Module gegen einfache Referenzen (`unit/attacks_test.cpp`) |
| `capi` | `sbm_capi_tests` | NULL-Zeiger, Puffer, Kopien, Rücknahmen, Versionen (`SBM_EXPECTED_VERSION` aus CMake) |

Vektor-Runner (`tests/vectors/`):

| Modul | Aufgabe |
|-------|---------|
| `main.cpp` | Sucht und verteilt die Dateien; Exit 0 nur ohne Fehlschlag und mit mindestens einem bestandenen Vektor, 2 bei falschem Aufruf |
| `call.hpp` | `Call` (Vektor, Brett, Ergebnis), `Handler`, `Registry` und die `add_*_calls` je Header |
| `calls_board.cpp` … `calls_move.cpp` | Handler je Header |
| `outputs.hpp` | Ausgabeformen: Text, Zugliste (fragt zuerst die Länge ab), Ganzzahl, Wahrheitswert, Hex |
| `json_values.hpp`/`.cpp` | `hex_text`, `same_result` (Vergleich ohne Reihenfolge) |
| `board_setup.hpp`/`.cpp` | `setup_board` aus FEN und Zügen (`0000` = Nullzug), `board_fen` |
| `run_calls.hpp`/`.cpp` | Prüft `result`, `result_contains`, `error`, `board_after`; überspringt die Bitoperationen von `Move` (`kWithoutCFunction`) |
| `perft.hpp`/`.cpp` | Rekursiver Perft über `legal_moves`/`make`/`undo`; langsame Vektoren nur mit `--slow` |
| `summary.hpp` | Zähler für bestanden, gescheitert, übersprungen |

- `tests/unit/check.hpp` liefert das Makro `CHECK` und `report()`; die Viewer-Tests nutzen es mit.
- nlohmann/json 3.12.0 kommt nur für die Tests per `FetchContent` mit SHA-256 (E56).
- `tests/header_check.c` und `header_check.cpp` übersetzt die CI direkt mit gcc/g++ (Befehl in `CLAUDE.md`); die C-Datei prüft Größen und Codes mit `_Static_assert`.

Befehle (aus dem Repo-Wurzelverzeichnis):

```
cmake -S sdk/core -B build/core -DCMAKE_BUILD_TYPE=Release [-DSBM_SLOW_TESTS=ON]
cmake --build build/core --config Release
ctest --test-dir build/core -C Release --output-on-failure
```

CI-Job `core` baut unter Linux, Windows und macOS mit Warnungen als Fehler, Job `core-headers` prüft die Header, Job `native-format` prüft clang-format.
