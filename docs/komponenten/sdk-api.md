# SDK / Bot-API

Ein gemeinsamer Schachkern in C++ und darüber je Sprache ein dünnes Binding (E3). Der Bot-Autor schreibt nur Suche und Bewertung; Protokoll, Schachregeln und Logging sind gekapselt.

## Schichten

```
Bot-Code (Python | C++ | Java | C# | JavaScript)
        │  idiomatische API der Sprache
Binding der Sprache  ── Protokoll, Uhr, Log, Transporte (in der jeweiligen Sprache)
        │  flache C-Schnittstelle (A11)
Schachkern (C++)     ── Stellung, Zuggenerierung, make/undo, Endbedingungen, FEN/UCI
```

| Teil | Sprache | Inhalt |
|------|---------|--------|
| Kern (`sdk/core`) | C++ | Alle Schachregeln. Wird auch vom Referee und von der Arena benutzt |
| C-Schnittstelle | C | Stabile, flache Funktionen auf einem Brett-Handle; einzige Grenze für alle Bindings; Regeln in [kern-c-schnittstelle.md](kern-c-schnittstelle.md) |
| Binding | Zielsprache | Klassen `Board`, `Move`, `Clock`, `Log`, Basisklasse `Bot`, Hauptschleife |

| Sprache | Anbindung | Auslieferung |
|---------|-----------|--------------|
| Python | Erweiterungsmodul `sbm._core` mit nanobind, Kern statisch eingebunden (E58) | Vorkompiliertes Wheel je Python-Version (`pip install schachbotmanager`, E59) |
| C++ | Direkt (Header + Bibliothek) | Archiv mit CMake-Einbindung |
| Java | JNI oder Foreign-Function-API | JAR mit eingebetteten nativen Bibliotheken je Plattform |
| C# | P/Invoke (nur innerhalb des SDK) | NuGet-Paket mit nativen Bibliotheken je Plattform |
| JavaScript | Nativer Node-Addon (A12) | npm-Paket mit vorkompilierten Binaries |

## Eigene Brett-Instanz pro Bot (E22)

- Jeder Bot-Prozess besitzt sein eigenes `Board`-Objekt im eigenen Speicher.
- `make_move` / `undo_move`, Kopien und beliebig viele weitere Bretter sind reine lokale Aufrufe in den Kern. Es entsteht keine Nachricht an den Match-Runner.
- Der Runner erfährt ausschließlich den Rückgabewert von `choose_move`.
- Das an `choose_move` übergebene Brett ist die aktuelle Partiestellung. Der Bot darf darauf frei ziehen und zurücknehmen; nach der Rückgabe stellt das SDK die Partiestellung in jedem Fall wieder her, sodass ein vergessenes `undo_move` nichts beschädigt.
- Der Referee führt unabhängig davon sein eigenes Brett; nur dieses entscheidet über Legalität und Ergebnis.

## Aufrufmodell: Callback (E21)

Das SDK besitzt die Hauptschleife und ruft den Bot auf.

| Funktion | Pflicht | Beschreibung |
|----------|---------|--------------|
| `on_game_start(info)` | nein | Einmalige Initialisierung; läuft im Startbudget |
| `choose_move(board, clock) -> Move` | **ja** | Pro eigenem Zug; die Rückgabe beendet die eigene Bedenkzeit |
| `on_game_end(result)` | nein | Aufräumen, letzte Logs |

- **Suchinformation (E45):** `report(info)` aus der Basisklasse speichert ein `Info` (Felder wie `info` im Protokoll, E43) für den laufenden Zug. Der letzte Aufruf vor der Rückgabe wird mit dem Zug gesendet; ein neuer Zug beginnt ohne Info. Zu lange `pv`/`text` kürzt das SDK, andere ungültige Felder lässt es mit einer Warnung weg (E63).
- **Aufgeben (E45):** `choose_move` gibt `Move.RESIGN` zurück; das SDK sendet `resign`.
- **Fehler im Bot (E49):** Eine Ausnahme aus einem Callback wird auf Stufe ERROR protokolliert und beendet den Prozess (Wertung `crash`). Die Legalität des Rückgabewerts von `choose_move` prüft das SDK nicht, darüber entscheidet der Referee; ein Wert, der kein Zug ist, oder `NULL_MOVE` wird wie eine Ausnahme behandelt.

Zustand in Objektfeldern (Transpositionstabelle, Suchbaum) bleibt zwischen den Zügen erhalten, begrenzt nur durch die feste Schutzgrenze der Sandbox. Einstieg je Sprache über genau eine Funktion, z. B. `run(MyBot)`; Transport und Log-Stufe kommen aus Argumenten/Umgebung, sodass dieselbe Datei lokal, im Debugger und auf dem Server läuft (E61):

| Argument | Umgebungsvariable | Wirkung |
|----------|-------------------|---------|
| `--tcp [PORT]` | `SBM_TRANSPORT=tcp`, `SBM_PORT` | Verbindet zu `127.0.0.1` (Standardport 7470) statt stdin/stdout zu nutzen |
| `--log-level LEVEL` | `SBM_LOG_LEVEL` | Startstufe: `trace`, `debug`, `info`, `warn`, `error`, `off` |
| `--log-file PATH` | `SBM_LOG_FILE` | Schreibt das Log zusätzlich in eine Datei (nur lokal) |

Argumente schlagen Umgebung; ohne beides gelten `stdio` und `INFO`. Andere Argumente bleiben dem Bot.

## API – hohe Ebene

Namen sind wortgleich, Schreibweise idiomatisch (`legal_moves` / `legalMoves` / `LegalMoves`). Die kanonische Definition liegt maschinenlesbar unter `spec/api/` (E39); sie schreibt Funktionen in `snake_case`, Typen in `PascalCase`, Konstanten in `UPPER_SNAKE`, und der kanonische Konstruktor `create` wird zum Konstruktor der Sprache (E47).

| Gruppe | Funktionen |
|--------|-----------|
| Abfrage | `piece_at(square)`, `side_to_move()`, `castling_rights()`, `en_passant_square()`, `halfmove_clock()`, `fullmove_number()`, `king_square(color)` |
| Züge | `legal_moves()`, `legal_captures()`, `is_legal(move)`, `make_move(move)`, `undo_move()`, `make_null_move()` / `undo_null_move()` |
| Zustand | `is_check()`, `is_checkmate()`, `is_stalemate()`, `is_draw()`, `is_repetition(count)`, `is_fifty_move_rule()`, `is_insufficient_material()`, `has_insufficient_material(color)`, `is_game_over()` |
| Hilfen | `Board()` (Grundstellung), `from_fen(fen)`, `fen()`, `copy()`, `hash()` (Polyglot-Zobrist, E46), `move_history()`, `to_text()` (lesbares Brett fürs Debugging), `parse_move(uci)` (vollständiger Zug mit Flags), `san(move)` (Kurznotation wie in PGN, E53) |

- `fen()` und `en_passant_square()` nennen das En-passant-Feld nur, wenn das Schlagen legal ist; gleiche Stellungen ergeben so gleiche FEN (E48).
- `has_insufficient_material(color)` sagt, ob eine Farbe nicht mehr mattsetzen kann; der Referee wertet damit Zeitablauf (E44, E53). `is_insufficient_material()` gilt, wenn das für beide Farben zutrifft.
- `is_draw()` umfasst Patt, dreifache Wiederholung, 50-Züge-Regel und ungenügendes Material, genau wie der Referee; `is_game_over()` zusätzlich Matt.
- `Move`: `from_square`, `to_square`, `flags`, `promotion`, `is_promotion`, `is_capture`, `is_castling`, `is_en_passant`, `uci()`, `value()`, `Move(from, to, flags)`, `Move.parse(uci)`, `Move.from_value(value)`; intern eine 16-Bit-Ganzzahl (E34). `from_square` statt `from`, weil `from` in Python reserviert ist (E47). `Move.parse(uci)` kennt ohne Brett keine Flags; `is_legal` und `make_move` vergleichen deshalb nur Start, Ziel und Umwandlung. Sonderwerte `NULL_MOVE` und `RESIGN` haben keine UCI-Form.
- `Clock`: `remaining_ms()`, `opponent_remaining_ms()`, `increment_ms()` aus der `turn`-Nachricht; `elapsed_ms()` misst lokal seit Empfang von `turn`.
- `load_data(name) -> Bytes`: Liest eine mit dem Bot hochgeladene Datendatei (E30). Einziger Weg zu Dateien; sie liest aus dem Ordner in `SBM_DATA_DIR` (setzt der Runner), lokal ohne diese Variable aus `data/` neben der Hauptdatei des Bots (E62). Fehlt die Datei, folgt `DataNotFound`.
- `GameInfo`: `game_id`, `color`, `opponent_name`, `start_fen`, `initial_time_ms`, `increment_ms`, `startup_ms`, `memory_limit_mib`, `discipline`.
- `GameResult`: `result`, `termination` wie in `game_over` (E44).

## API – Rohzugriff (E21)

Für Bots, die eigene Bewertung oder eigene Zugsortierung direkt auf den Daten rechnen.

| Funktion | Liefert |
|----------|---------|
| `bitboard(color, piece_type)` | 64-Bit-Maske der Felder |
| `occupied()`, `occupied_by(color)` | Belegungsmasken |
| `bitboards()` | Alle 12 Figurenmasken in einem Aufruf |
| `squares()` | Feldweise Darstellung: 64 Einträge mit Figur/Farbe, in einem Aufruf |
| `attacks_from(square)`, `attackers_of(square, color)`, `is_attacked(square, color)` | Angriffsmasken |
| `checkers()`, `pinned(color)` | Schachgebende bzw. gefesselte Figuren als Maske |
| `piece_count(color, piece_type)` | Materialzählung |

Festlegungen, die dadurch Teil der öffentlichen API werden (E34, E35):

| Begriff | Kodierung |
|---------|-----------|
| Feld | `rank * 8 + file`, a1 = 0 … h8 = 63 |
| Bitboard | Bit *i* = Feld *i* (a1 = niedrigstes Bit) |
| `Color` | `WHITE = 0`, `BLACK = 1` |
| `PieceType` | `PAWN = 0`, `KNIGHT = 1`, `BISHOP = 2`, `ROOK = 3`, `QUEEN = 4`, `KING = 5`, `NO_PIECE_TYPE = 6` |
| `Piece` | `color * 6 + type` (0–11), `NO_PIECE = 12`; Index in `bitboards()`, Wert in `squares()` |
| `Square` | Konstanten `A1` … `H8`, `NO_SQUARE = 64` |
| `CastlingRights` | Bitmaske: `WHITE_KINGSIDE = 1`, `WHITE_QUEENSIDE = 2`, `BLACK_KINGSIDE = 4`, `BLACK_QUEENSIDE = 8` (E47) |
| Zug | 16 Bit: Bits 0–5 Startfeld, 6–11 Zielfeld, 12–15 Flags; `0` = `NULL_MOVE`, `0xFFFF` = `RESIGN` (E45) |

| Flags | Bedeutung |
|-------|-----------|
| 0 | Ruhiger Zug |
| 1 | Doppelschritt des Bauern |
| 2 / 3 | Kurze / lange Rochade |
| 4 | Schlagzug |
| 5 | Schlagen en passant |
| 8–11 | Umwandlung in Springer, Läufer, Turm, Dame (`PieceType = (flags & 3) + 1`) |
| 12–15 | Umwandlung mit Schlagen, gleiche Reihenfolge |

Die maschinenlesbare Fassung liegt unter `spec/api/`.

Darstellung von 64-Bit-Werten: Python `int`, C++ `uint64_t`, Java `long`, C# `ulong`, JavaScript `BigInt`. Da `BigInt`-Arithmetik langsam ist, bietet JavaScript jede Funktion mit 64-Bit-Rückgabe zusätzlich mit der Endung `32` an (z. B. `bitboards32()`); sie liefert ein `Uint32Array` mit unterer und oberer Hälfte je Wert. Die Zuordnung aller Grundtypen steht in `spec/api/primitives.json`.

## Fehler (E49)

| Fehler | Wann |
|--------|------|
| `InvalidArgument` | Wert außerhalb seines Bereichs (Feld > 63, Farbe > 1, unbekannte Log-Stufe, Dateiname mit Pfad) |
| `InvalidFen` | FEN fehlerhaft oder Stellung unmöglich |
| `InvalidUci` | Text ist kein Zug in UCI-Notation |
| `IllegalMove` | Zug wohlgeformt, aber in der Stellung nicht legal |
| `InvalidState` | Aufruf im aktuellen Zustand nicht möglich, z. B. `undo_move` ohne Verlauf, Nullzug im Schach |
| `DataNotFound` | `load_data` findet die Datei nicht |

Jede Sprache wirft sie als eigene Ausnahme mit üblicher Endung (`IllegalMoveError`, `IllegalMoveException`), alle mit der gemeinsamen Basis `ChessError`. Bei einem Fehler bleibt das Brett unverändert.

## Kosten der Sprachgrenze (R7)

Jeder Aufruf aus Python/Java/C#/JS in den Kern kostet einen festen Betrag, unabhängig von der Arbeit im Kern. Deshalb:

- **Grobkörnige Aufrufe:** `legal_moves()` liefert die ganze Liste in einem Aufruf, `bitboards()` und `squares()` liefern alles auf einmal.
- **Züge als Ganzzahlen** über die Grenze, keine Objekte pro Zug im Kern.
- **Kein Rückruf vom Kern in die Bot-Sprache.**
- Schnelle Sprachen (Java, C#) verlieren gegenüber einer rein nativen Lösung etwas; Python und JavaScript gewinnen deutlich. Der C++-Bot ruft den Kern ohne Übergang auf und ist damit strukturell am schnellsten.

## Log (Debug-Bibliothek)

- Stufen: `TRACE < DEBUG < INFO < WARN < ERROR < OFF`
- `log.debug(...)` usw., `log.set_level(level)`, `log.level()`, `log.is_enabled(level)`; Startstufe `INFO`
- Stufe zusätzlich per Umgebungsvariable/CLI-Flag setzbar (E61)
- Lokal: Konsole (optional Datei) mit Zeitstempel, Zugnummer, Stufe, z. B. `14:03:12.517 [ply 12] INFO  depth 6`. Server: `stderr`, mengenbegrenzt gespeichert, nur für Besitzer/Admin einsehbar
- Die Disziplin legt für den Server eine maximale Stufe und Menge fest; wie die Stufe den Bot erreicht, ist offen (O19)

## Tests

| Ebene | Inhalt |
|-------|--------|
| Kern | Perft-Vektoren, Regel-Vektoren (Matt, Patt, Wiederholung, 50 Züge, Material), FEN/UCI/SAN, Polyglot-Hash – einmal, im Kern (`spec/testvectors/*.json`) |
| Binding je Sprache | Jede `Board`- und `Move`-Funktion gegen die API-Vektoren aus `spec/testvectors/api/` (Format E55); `Clock`, `Log`, `Bot`, `run` und `load_data` mit eigenen Tests des Bindings; Speicherverhalten (kein Leck bei vielen Brettkopien); Fehlerfälle (illegaler Zug, ungültige FEN) als Ausnahme der Sprache |
| Protokoll je Sprache | Aufgezeichnete Nachrichtenfolgen |
| Kreuztest | Jedes SDK spielt in CI gegen jedes andere über die Arena |

## Zu beachten

- **Kein Debugger-Schritt in den Kern** aus Python/Java/C#/JS (R9). Ausgleich: `to_text()`, `fen()`, klare Ausnahmen.
- **Fehler im Kern dürfen den Prozess nicht abstürzen lassen:** Die C-Schnittstelle prüft Argumente und meldet Fehler als Statuscode; das Binding wandelt sie in Ausnahmen ([kern-c-schnittstelle.md](kern-c-schnittstelle.md), E52).
- **Lebensdauer von Brett-Handles** wird vom Binding verwaltet (Freigabe über die Speicherverwaltung der Sprache); der Bot-Autor sieht keine Handles.
- **Bot-Code darf selbst keine nativen Aufrufe machen** – das SDK ist die einzige Ausnahme in der [statischen Analyse](statische-analyse.md).
- **Das SDK wird serverseitig bereitgestellt**, nicht mit hochgeladen.
- **Versionierung:** Kern und Bindings tragen dieselbe Versionsnummer nach SemVer; jede SDK-Version spricht genau eine Protokollversion (E36); ein verifizierter Bot bleibt an seine SDK-Version gebunden.
- **Zeitüberschreitung in `choose_move`:** Der Server beendet den Prozess hart; es läuft kein Bot-Code mehr.
- **Kein Threading in der API**, solange A4 gilt.

Lokales Setup je Sprache: [lokale-entwicklung.md](lokale-entwicklung.md).
