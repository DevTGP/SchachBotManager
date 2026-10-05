# SDK / Bot-API

Ein SDK pro Sprache (Python, C++, Java, C#, JavaScript), jeweils nativ implementiert (E3). Der Bot-Autor schreibt nur Suche und Bewertung; Protokoll, Schachregeln und Logging sind gekapselt.

## Aufbau eines SDK

| Modul | Aufgabe |
|-------|---------|
| `bot` | Basisklasse/Interface, die der Autor implementiert |
| `board` | Stellung, Zuggenerierung, make/undo, Endbedingungen |
| `move`, `square`, `piece` | Werttypen |
| `clock` | Restzeiten, verstrichene Zeit im aktuellen Zug |
| `log` | Debug-Bibliothek mit Stufen |
| `runtime` | Hauptschleife, Protokoll, Transporte (`stdio`, `tcp`, `remote`) |

## Kanonische API

Namen sind in allen Sprachen wortgleich; Schreibweise folgt der Sprachkonvention (A10). Kanonische Definition liegt maschinenlesbar unter `spec/api/` und ist Grundlage für Doku und Konformitätstests.

### Bot (vom Autor zu implementieren)

| Funktion | Pflicht | Beschreibung |
|----------|---------|--------------|
| `on_game_start(info)` | nein | Einmalige Initialisierung; läuft im Startbudget |
| `choose_move(board, clock) -> Move` | **ja** | Wird pro eigenem Zug aufgerufen; Rückgabe beendet die eigene Bedenkzeit |
| `on_game_end(result)` | nein | Aufräumen, letzte Logs |

Zustand in Objektfeldern bleibt zwischen den Zügen erhalten (Transpositionstabelle, Suchbaum), begrenzt durch das Speicherlimit der Disziplin.

### GameInfo

`game_id`, `color`, `opponent_name`, `start_fen`, `initial_time_ms`, `increment_ms`, `memory_limit_mb`, `discipline`

### Board

| Gruppe | Funktionen |
|--------|-----------|
| Abfrage | `piece_at(square)`, `side_to_move()`, `castling_rights()`, `en_passant_square()`, `halfmove_clock()`, `fullmove_number()`, `king_square(color)`, `pieces(color, type)` |
| Züge | `legal_moves()`, `legal_captures()`, `is_legal(move)`, `make_move(move)`, `undo_move()` |
| Zustand | `is_check()`, `is_checkmate()`, `is_stalemate()`, `is_draw()`, `is_repetition(count)`, `is_fifty_move_rule()`, `is_insufficient_material()`, `is_game_over()` |
| Hilfen | `fen()`, `from_fen(fen)`, `copy()`, `hash()` (Zobrist), `move_history()`, `attackers(square, color)`, `is_attacked(square, color)` |

### Move / Clock

- `Move`: `from`, `to`, `promotion`, `is_capture`, `is_castling`, `is_en_passant`, `uci()`, `parse(uci)`
- `Clock`: `remaining_ms()`, `opponent_remaining_ms()`, `increment_ms()`, `elapsed_ms()`

### Log (Debug-Bibliothek)

- Stufen: `TRACE < DEBUG < INFO < WARN < ERROR < OFF`
- `log.debug(...)`, `log.info(...)` usw., `log.set_level(level)`, `log.is_enabled(level)` (um teure Ausgaben zu vermeiden)
- Stufe zusätzlich per Umgebungsvariable/CLI-Flag setzbar, ohne Codeänderung
- Ausgabe: lokal Konsole (optional Datei) mit Zeitstempel, Zugnummer, Stufe; auf dem Server `stderr`, mengenbegrenzt gespeichert und nur für Besitzer/Admin einsehbar
- Auf dem Server legt die Disziplin eine Maximalstufe fest, damit Logging nicht als Zeitfresser oder Speicherbombe wirkt

### Einstieg

Jede Sprache hat genau einen Einstiegspunkt, z. B. `run(MyBot)`. Er liest Transport und Log-Stufe aus Argumenten/Umgebung, sodass dieselbe Bot-Datei unverändert lokal, im Debugger und auf dem Server läuft.

## Konformität über 5 Sprachen (R2)

| Maßnahme | Inhalt |
|----------|--------|
| Perft-Vektoren | Stellungen mit bekannten Knotenzahlen pro Tiefe; decken Rochade, en passant, Umwandlung, Fesselungen ab |
| Regel-Vektoren | Matt, Patt, dreifache Wiederholung, 50-Züge-Regel, ungenügendes Material |
| Format-Vektoren | FEN lesen/schreiben, UCI lesen/schreiben |
| Protokoll-Vektoren | Aufgezeichnete Nachrichtenfolgen, die jedes SDK korrekt beantworten muss |
| Kreuztest | Jedes SDK spielt in CI eine Partie gegen jedes andere über die Arena |

Alle Vektoren liegen sprachneutral als JSON unter `spec/testvectors/`; jedes SDK hat einen Test-Runner dafür. Ein SDK gilt erst als freigegeben, wenn alle Vektoren bestehen.

## Zu beachten

- **Performance des Kerns bestimmt die Bot-Stärke.** Unterschiede zwischen den Sprachen sind erwartbar; Ausgleich erfolgt nur über Disziplin-Konfiguration (E8).
- **Brettdarstellung** (Bitboards vs. Mailbox) ist eine SDK-interne Entscheidung, aber die öffentliche API darf sie nicht festschreiben.
- **`undo_move` braucht einen Zustandsstapel** (Rochaderechte, e. p., Halbzugzähler, Hash) – identisch zu testen.
- **Zeitüberschreitung in `choose_move`:** Der Server beendet den Prozess hart. Das SDK bietet keine Garantie, dass noch Code des Bots läuft.
- **SDK wird serverseitig bereitgestellt**, nicht mit hochgeladen. Uploads, die SDK-Namensräume überschreiben, werden abgelehnt.
- **SDK-Versionen:** Semantische Versionierung; ein verifizierter Bot bleibt an seine SDK-Version gebunden, alte Versionen bleiben im Sandbox-Image verfügbar.
- **Kein Threading in der API**, solange A4 gilt.
