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
| C-Schnittstelle | C | Stabile, flache Funktionen auf einem Brett-Handle; einzige Grenze für alle Bindings |
| Binding | Zielsprache | Klassen `Board`, `Move`, `Clock`, `Log`, Basisklasse `Bot`, Hauptschleife |

| Sprache | Anbindung | Auslieferung |
|---------|-----------|--------------|
| Python | Erweiterungsmodul | Vorkompiliertes Wheel (`pip install`) |
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

Zustand in Objektfeldern (Transpositionstabelle, Suchbaum) bleibt zwischen den Zügen erhalten, begrenzt durch das Speicherlimit. Einstieg je Sprache über genau eine Funktion, z. B. `run(MyBot)`; Transport und Log-Stufe kommen aus Argumenten/Umgebung, sodass dieselbe Datei lokal, im Debugger und auf dem Server läuft.

## API – hohe Ebene

Namen sind wortgleich, Schreibweise idiomatisch (`legal_moves` / `legalMoves` / `LegalMoves`). Die kanonische Definition liegt maschinenlesbar unter `spec/api/`.

| Gruppe | Funktionen |
|--------|-----------|
| Abfrage | `piece_at(square)`, `side_to_move()`, `castling_rights()`, `en_passant_square()`, `halfmove_clock()`, `fullmove_number()`, `king_square(color)` |
| Züge | `legal_moves()`, `legal_captures()`, `is_legal(move)`, `make_move(move)`, `undo_move()`, `make_null_move()` / `undo_null_move()` |
| Zustand | `is_check()`, `is_checkmate()`, `is_stalemate()`, `is_draw()`, `is_repetition(count)`, `is_fifty_move_rule()`, `is_insufficient_material()`, `is_game_over()` |
| Hilfen | `fen()`, `from_fen(fen)`, `copy()`, `hash()` (Zobrist), `move_history()`, `to_text()` (lesbares Brett fürs Debugging) |

- `Move`: `from`, `to`, `promotion`, `is_capture`, `is_castling`, `is_en_passant`, `uci()`, `parse(uci)`; intern eine kompakte Ganzzahl.
- `Clock`: `remaining_ms()`, `opponent_remaining_ms()`, `increment_ms()`, `elapsed_ms()`.
- `GameInfo`: `game_id`, `color`, `opponent_name`, `start_fen`, `initial_time_ms`, `increment_ms`, `memory_limit_mb`, `discipline`.

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

Festlegungen, die dadurch Teil der öffentlichen API werden: Feldnummerierung (a1 = 0 … h8 = 63), Bitreihenfolge, Kodierung von Figur und Farbe, Kodierung eines Zuges als Ganzzahl.

Darstellung von 64-Bit-Werten: Python `int`, C++ `uint64_t`, Java `long`, C# `ulong`, JavaScript `BigInt` (alternativ zwei 32-Bit-Hälften, da `BigInt`-Arithmetik langsam ist – beides anbieten).

## Kosten der Sprachgrenze (R7)

Jeder Aufruf aus Python/Java/C#/JS in den Kern kostet einen festen Betrag, unabhängig von der Arbeit im Kern. Deshalb:

- **Grobkörnige Aufrufe:** `legal_moves()` liefert die ganze Liste in einem Aufruf, `bitboards()` und `squares()` liefern alles auf einmal.
- **Züge als Ganzzahlen** über die Grenze, keine Objekte pro Zug im Kern.
- **Kein Rückruf vom Kern in die Bot-Sprache.**
- Schnelle Sprachen (Java, C#) verlieren gegenüber einer rein nativen Lösung etwas; Python und JavaScript gewinnen deutlich. Der C++-Bot ruft den Kern ohne Übergang auf und ist damit strukturell am schnellsten.

## Log (Debug-Bibliothek)

- Stufen: `TRACE < DEBUG < INFO < WARN < ERROR < OFF`
- `log.debug(...)` usw., `log.set_level(level)`, `log.is_enabled(level)`
- Stufe zusätzlich per Umgebungsvariable/CLI-Flag setzbar
- Lokal: Konsole (optional Datei) mit Zeitstempel, Zugnummer, Stufe. Server: `stderr`, mengenbegrenzt gespeichert, nur für Besitzer/Admin einsehbar
- Die Disziplin legt für den Server eine maximale Stufe und Menge fest

## Tests

| Ebene | Inhalt |
|-------|--------|
| Kern | Perft-Vektoren, Regel-Vektoren (Matt, Patt, Wiederholung, 50 Züge, Material), FEN/UCI – einmal, im Kern |
| Binding je Sprache | Jede API-Funktion gegen feste Erwartungswerte aus `spec/testvectors/`; Speicherverhalten (kein Leck bei vielen Brettkopien); Fehlerfälle (illegaler Zug, ungültige FEN) als Ausnahme der Sprache |
| Protokoll je Sprache | Aufgezeichnete Nachrichtenfolgen |
| Kreuztest | Jedes SDK spielt in CI gegen jedes andere über die Arena |

## Zu beachten

- **Kein Debugger-Schritt in den Kern** aus Python/Java/C#/JS (R9). Ausgleich: `to_text()`, `fen()`, klare Ausnahmen.
- **Fehler im Kern dürfen den Prozess nicht abstürzen lassen:** Die C-Schnittstelle prüft Argumente und meldet Fehler als Rückgabecode; das Binding wandelt sie in Ausnahmen.
- **Lebensdauer von Brett-Handles** wird vom Binding verwaltet (Freigabe über die Speicherverwaltung der Sprache); der Bot-Autor sieht keine Handles.
- **Bot-Code darf selbst keine nativen Aufrufe machen** – das SDK ist die einzige Ausnahme in der [statischen Analyse](statische-analyse.md).
- **Das SDK wird serverseitig bereitgestellt**, nicht mit hochgeladen.
- **Versionierung:** Kern und Bindings tragen dieselbe Versionsnummer; ein verifizierter Bot bleibt an seine SDK-Version gebunden.
- **Zeitüberschreitung in `choose_move`:** Der Server beendet den Prozess hart; es läuft kein Bot-Code mehr.
- **Kein Threading in der API**, solange A4 gilt.

Lokales Setup je Sprache: [lokale-entwicklung.md](lokale-entwicklung.md).
