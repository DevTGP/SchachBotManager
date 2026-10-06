# C-Schnittstelle des Kerns

Flache C-Schnittstelle des C++-Kerns (A11). Sie ist die einzige Grenze zwischen dem Kern und den Bindings der fünf Sprachen; Referee und Arena nutzen den Kern ebenfalls über sie.

## Quelle der Wahrheit

- **Signaturen:** Die Header unter `sdk/core/include/sbm/` sind maßgeblich (E50). Bindings binden nur `sbm/sbm.h` ein.
- **Bedeutung jeder Funktion:** `spec/api/` (E39). Die C-Schnittstelle legt nur fest, wie Werte, Fehler und Speicher über die Grenze gehen; sie fügt keine eigene Schachlogik hinzu.
- **Diese Datei:** Regeln für Handles, Puffer, Statuscodes und Versionen.

| Header | Inhalt | Gegenstück in `spec/api/` |
|--------|--------|---------------------------|
| `export.h` | `SBM_API`, `extern "C"` | – |
| `types.h` | Typen, Codes (E34, E35, E45, E47), Puffergrößen | `types.json`, `constants.json` |
| `status.h` | Statuscodes, `sbm_status_name` | `errors.json` |
| `version.h` | ABI-Version, SemVer des Kerns | – |
| `move.h` | `Move.parse`, `Move.uci` | `move.json` |
| `board.h` | Handle anlegen, kopieren, freigeben; FEN, Hash, Verlauf, Text | `board.json` |
| `board_query.h` | Einzelne Eigenschaften der Stellung | `board_query.json` |
| `board_moves.h` | Züge erzeugen, prüfen, ausführen, zurücknehmen; SAN | `board_moves.json` |
| `board_state.h` | Endbedingungen | `board_state.json` |
| `board_raw.h` | Bitboards und Felder | `board_raw.json` |
| `sbm.h` | Bindet alle Header ein | – |

## Abbildung der API

- Jede Funktion von `Board` heißt `sbm_board_<name>`; `Board.create` wird zu `sbm_board_new`. Alle Funktionen außer `sbm_board_free` liefern `sbm_status`, Ergebnisse gehen über Ausgabezeiger am Ende der Parameterliste.
- `Move` ist im Binding ein Wert (E34). Die reinen Bitoperationen (`from_square`, `to_square`, `flags`, `promotion`, `is_promotion`, `is_capture`, `is_castling`, `is_en_passant`, `value`) sowie die Prüfungen von `Move.create` und `Move.from_value` rechnet jedes Binding selbst; ein nativer Aufruf je Zugriff wäre teurer als die Rechnung. Das ist keine Schachregel, sondern Dekodierung von E34; die API-Testvektoren prüfen sie in jedem Binding. `Move.parse` und `Move.uci` liegen im Kern.
- `Clock`, `Log`, `Bot`, `run` und `load_data` gehören zum Binding und haben kein Gegenstück im Kern.
- Wahrheitswerte sind `sbm_bool` (`int32_t`, nur 0 oder 1), weil `bool` von Fremdaufruf-Schnittstellen unterschiedlich übergeben wird.
- Mengen und Kapazitäten sind `uint32_t`, Zahlen der API mit Typ `i32` sind `int32_t`.
- Leere Ergebnisse nutzen die Codes aus E35: `piece_at` liefert `SBM_NO_PIECE`, `en_passant_square` `SBM_NO_SQUARE`.

## Statuscodes (E52)

Jede Funktion liefert genau einen Statuscode; es gibt keinen weiteren Fehlerzustand und keine Fehlertexte. `sbm_status_name(code)` liefert einen festen Namen (`"illegal_move"`, unbekannte Werte `"unknown"`); das Binding baut daraus und aus dem Funktionsnamen die Meldung der Ausnahme.

| Code | Wert | Ausnahme im Binding (E49) | Bedeutung |
|------|------|---------------------------|-----------|
| `SBM_OK` | 0 | – | Erfolg |
| `SBM_INVALID_ARGUMENT` | 1 | `InvalidArgument` | Feld, Farbe, Figurtyp oder Anzahl außerhalb des Bereichs; Nullzeiger |
| `SBM_INVALID_FEN` | 2 | `InvalidFen` | Siehe `Board.from_fen` |
| `SBM_INVALID_UCI` | 3 | `InvalidUci` | Kein Text der Form `[a-h][1-8][a-h][1-8][nbrq]?` |
| `SBM_ILLEGAL_MOVE` | 4 | `IllegalMove` | Zug in dieser Stellung nicht legal, auch fehlerhaft codierte Zugwerte |
| `SBM_INVALID_STATE` | 5 | `InvalidState` | Z. B. `undo_move` ohne Zug im Verlauf |
| `SBM_BUFFER_TOO_SMALL` | 6 | `ChessError` | Puffer des Aufrufers zu klein; nur bei einem Fehler im Binding möglich |
| `SBM_OUT_OF_MEMORY` | 7 | Speichermangel-Fehler der Sprache | Anlegen eines Bretts oder Wachsen des Verlaufs scheitert |
| `SBM_INTERNAL_ERROR` | 8 | `ChessError` | Fehler im Kern |

- C++-Ausnahmen verlassen den Kern nie. Jede Funktion fängt sie ab und liefert `SBM_OUT_OF_MEMORY` (`std::bad_alloc`) oder `SBM_INTERNAL_ERROR`.
- Bei jedem Fehler bleiben Brett und Ausgaben unverändert. Ausnahmen davon stehen unter Puffer.
- `is_legal` meldet einen fehlerhaft codierten Zugwert als `false`, nicht als Fehler (wie in `spec/api/board_moves.json`).

## Regeln für Handles

- `sbm_board` ist undurchsichtig. Ein Handle entsteht nur durch `sbm_board_new`, `sbm_board_from_fen` oder `sbm_board_copy` und wird genau einmal mit `sbm_board_free` freigegeben; `sbm_board_free(NULL)` tut nichts.
- Ein freigegebenes Handle darf nicht mehr benutzt werden. Der Kern kann das nicht prüfen; das Binding stellt es über die Speicherverwaltung der Sprache sicher, der Bot-Autor sieht keine Handles.
- Kopien sind vollständig unabhängig, einschließlich Zugverlauf.
- Lesende Funktionen nehmen `const sbm_board*`; nur `make_move`, `undo_move`, `make_null_move` und `undo_null_move` ändern das Brett.
- Der Kern hat keinen veränderlichen globalen Zustand. Feste Tabellen (Angriffe, Polyglot-Schlüssel) sind konstant. Verschiedene Handles dürfen gleichzeitig aus verschiedenen Threads benutzt werden, ein Handle nicht.

## Regeln für Puffer (E51)

Der Aufrufer stellt allen Speicher für Ergebnisse bereit; der Kern hält keinen übergebenen Zeiger über den Aufruf hinaus und gibt keinen Speicher zurück, den der Aufrufer freigeben müsste. Speicher reserviert der Kern nur beim Anlegen eines Bretts und beim Wachsen des Zugverlaufs (`make_move`, `make_null_move`).

| Ausgabe | Form | Feste Obergrenze |
|---------|------|------------------|
| Text | `char* buffer, uint32_t size` | `SBM_FEN_BUFFER_SIZE` (128; eine FEN hat höchstens 103 Zeichen), `SBM_UCI_BUFFER_SIZE` (6), `SBM_SAN_BUFFER_SIZE` (16), `SBM_TEXT_BUFFER_SIZE` (512); jeweils mit abschließendem NUL |
| Zugliste | `sbm_move* out, uint32_t capacity, uint32_t* count` | `SBM_MAX_MOVES` (256) für `legal_moves` und `legal_captures`; `move_history` hat keine |
| Feste Felder | `sbm_bitboard* out` bzw. `sbm_piece* out` | Genau `SBM_PIECE_COUNT` (12) bzw. `SBM_SQUARE_COUNT` (64) Einträge |
| Einzelwert | `T* out` | – |

- **Text:** Bei Erfolg steht der Text mit NUL im Puffer. Ist er zu klein, folgt `SBM_BUFFER_TOO_SMALL` und der Puffer enthält bei `size > 0` den leeren Text.
- **Zugliste:** Bei Erfolg steht die Anzahl in `*count`. Reicht `capacity` nicht, folgt `SBM_BUFFER_TOO_SMALL`, `*count` enthält die nötige Anzahl und `out` bleibt unverändert. Mit `capacity = 0` darf `out` `NULL` sein; so fragt das Binding die Länge von `move_history` ab.
- Mit den festen Obergrenzen kann `SBM_BUFFER_TOO_SMALL` außer bei `move_history` nur bei einem Fehler im Binding auftreten.
- Übergebene Texte (FEN, UCI) sind NUL-terminiertes ASCII. Ausgegebene Texte sind ASCII.
- Alle anderen Nullzeiger ergeben `SBM_INVALID_ARGUMENT`.

## Versionen

- `SBM_ABI_VERSION` (Header) und `sbm_abi_version()` (Bibliothek) zählen inkompatible Änderungen der C-Schnittstelle. Das Binding vergleicht beide beim Laden und bricht bei Abweichung ab.
- Innerhalb einer ABI-Version kommen nur Funktionen und Konstanten hinzu; bestehende Signaturen, Werte und Statuscodes ändern sich nicht.
- `sbm_version()` liefert die SemVer des Kerns, gleich der SDK-Version (E36).

## Export und Bindung

- `SBM_API` exportiert die Funktionen: unter Windows `__declspec(dllexport)` beim Bau des Kerns (`SBM_BUILD`), sonst `dllimport`; auf anderen Plattformen mit Sichtbarkeit `default`. `SBM_STATIC` leert das Makro für statisches Linken.
- Die Header sind C11 und als C++20 übersetzbar (Coding-Standards). Alle Deklarationen haben C-Bindung.

## Prüfung

- CI übersetzt `sdk/core/tests/header_check.c` als C11 und `header_check.cpp` als C++20 mit `-Wall -Wextra -Wpedantic -Werror`. Die C-Datei prüft zusätzlich Größen und Codes aus E34, E35 und E45.
- Das Verhalten jeder Funktion prüfen ab M1 die Vektoren unter `spec/testvectors/` (Kern) und die API-Vektoren (je Binding).
