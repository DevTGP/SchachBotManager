# Bot-Protokoll (Referee ↔ Bot)

Einzige Schnittstelle zwischen Server und Bot-Prozess. Macht Spiele zwischen beliebigen Sprachen möglich, weil jeder Bot nur mit dem Referee spricht.

## Transport

| Transport | Einsatz | Bemerkung |
|-----------|---------|-----------|
| `stdio` | Sandbox auf dem Server, lokale Arena | Kein Netzwerk nötig → Sandbox läuft ohne Netzwerk |
| `tcp` (localhost) | Lokales Debugging: Bot wird aus der IDE gestartet und verbindet sich zur Arena | Nur lokal; die Arena wartet auf `127.0.0.1:7470`, der Bot wählt den Transport mit `--tcp [PORT]` oder `SBM_TRANSPORT=tcp` (E61) |
| `remote` (WebSocket über TLS) | Lokaler Bot gegen Web-API | Token-Auth, siehe [lokale-entwicklung.md](lokale-entwicklung.md) |

Die Nachrichten sind in allen Transporten identisch; das SDK kapselt den Transport vollständig.

## Format

- Eine Nachricht = eine Zeile UTF-8-JSON (NDJSON), höchstens 65 536 Bytes ohne Zeilenende.
- `stdout` gehört ausschließlich dem Protokoll. Debug-Ausgaben gehen über `stderr` (das SDK erzwingt das).
- Jede Nachricht hat `type`. Alle Nachrichten außer `init`, `error` und `game_over` tragen zusätzlich `v` (Protokollversion, siehe Versionierung).
- Züge in UCI-Notation mit kleingeschriebener Umwandlungsfigur (`e2e4`, `e7e8q`), Nullzug `0000` ist nicht erlaubt. Stellungen als vollständige FEN.
- Zeiten als ganze Millisekunden, Farben als `"white"` / `"black"`.

## Nachrichten

Maßgeblich sind die Schemas unter `spec/protocol/v1/`; die Tabelle fasst sie zusammen.

| Richtung | `type` | Felder |
|----------|--------|--------|
| R → B | `init` | `supported` (Protokollversionen), `game_id`, `color`, `start_fen`, `initial_time_ms`, `increment_ms`, `startup_ms` (Startbudget), `memory_limit_mib` (feste Speicher-Schutzgrenze, A14, nur zur Information, z. B. für die Größe der Hashtabelle), `discipline`, `opponent_name` |
| B → R | `ready` | `v` (gewählte Protokollversion), `sdk` (SDK-Version nach SemVer), `lang` (`python`, `cpp`, `java`, `csharp`, `javascript`); muss innerhalb von `startup_ms` kommen |
| R → B | `turn` | `last_move` (Gegnerzug in UCI oder `null`, wenn der Bot die Partie eröffnet), `fen` (Stellung nach `last_move`, immer vorhanden), `ply` (gespielte Halbzüge seit `start_fen`), `remaining_ms`, `opponent_remaining_ms` |
| B → R | `move` | `move` (UCI); optional `info` |
| B → R | `resign` | Aufgabe; nur als Antwort auf `turn` statt `move` |
| R → B | `error` | `code`, `message`; Diagnose eines Protokollverstoßes, danach folgt `game_over` |
| R → B | `game_over` | `result`, `termination`; danach kurze Frist bis zum Beenden |

`info` in `move` (alle Felder optional, öffentlich im Viewer, E33):

| Feld | Inhalt |
|------|--------|
| `depth`, `seldepth` | Suchtiefe, selektive Suchtiefe (0–1024) |
| `score_cp` / `score_mate` | Bewertung in Centipawns aus Sicht des Bots (±100 000) oder Matt in n Zügen (negativ: Bot wird mattgesetzt); höchstens eines von beiden |
| `nodes` | Durchsuchte Knoten |
| `pv` | Hauptvariante ab dem gespielten Zug, höchstens 32 Züge |
| `text` | Freitext, höchstens 256 Zeichen |

`result` in `game_over` folgt PGN (`1-0`, `0-1`, `1/2-1/2`, `*` für abgebrochen). `termination` ist einer dieser Codes, dieselben wie in der Datenbank:

| Codes | `result` |
|-------|----------|
| `checkmate`, `resignation`, `timeout`, `illegal_move`, `protocol_violation`, `crash`, `memory_limit` | `1-0` oder `0-1` |
| `startup_timeout` | `1-0` oder `0-1`; `*`, wenn beide Bots nicht starten |
| `stalemate`, `threefold_repetition`, `fifty_move_rule`, `insufficient_material`, `timeout_insufficient_material` (Zeit abgelaufen, Gegner kann nicht mattsetzen), `max_moves` | `1/2-1/2` |
| `aborted` | `*` |

`code` in `error`: `invalid_json`, `line_too_long`, `unknown_type`, `schema_violation`, `unsupported_version`, `unexpected_message`, `illegal_move`.

Bewusst **nicht** enthalten: Remisangebote, Zugrücknahme, Nachrichten zwischen Bots.

## Zustandsautomat aus Bot-Sicht

```
START → (init) → INITIALIZING → ready → IDLE
IDLE → (turn) → THINKING → move → IDLE
THINKING → resign → (game_over) → ENDED
IDLE/THINKING → (game_over) → ENDED
```

Außerhalb von `THINKING` ist der Prozess auf dem Server eingefroren.

## Fehlerbehandlung

| Ereignis | Folge |
|----------|-------|
| Kein `ready` im Startbudget | Niederlage (`startup_timeout`) |
| Ungültiges JSON, unbekannter `type`, Verstoß gegen das Schema, zu lange Zeile | Niederlage (`protocol_violation`) |
| `v` in `ready` nicht in `supported` | Niederlage (`protocol_violation`) |
| Nachricht außerhalb von `THINKING` (nur bei `tcp`/`remote` möglich, auf dem Server ist der Prozess eingefroren) | Niederlage (`protocol_violation`) |
| Illegaler oder nicht parsbarer Zug | Niederlage (`illegal_move`) |
| Prozess endet / stürzt ab | Niederlage (`crash`) |
| Speicherlimit überschritten | Niederlage (`memory_limit`) |
| Zeit abgelaufen | Niederlage (`timeout`), Prozess wird hart beendet |

## Zu beachten

- **Versionierung (E36):** `v` ist eine Ganzzahl und steigt nur bei inkompatiblen Änderungen; neue optionale Felder ändern sie nicht. Der Referee nennt in `init` die unterstützten Versionen, der Bot wählt in `ready` eine davon; `turn`, `move` und `resign` tragen danach diese Version. `init`, `error` und `game_over` können vor einer erfolgreichen Aushandlung kommen; sie tragen kein `v`, ihr Format ist über alle Protokollversionen gleich und wird nur um Felder ergänzt (E41). Jede SDK-Version spricht genau eine Protokollversion; ein Bot ist an die SDK-Version gebunden, mit der er verifiziert wurde.
- **Strenge:** Das SDK ignoriert unbekannte Felder in Nachrichten des Referees. Der Referee prüft Nachrichten des Bots streng gegen das Schema (feindliche Eingabe).
- **Schema als Quelle der Wahrheit:** JSON Schema 2020-12 unter `spec/protocol/v<N>/`, Beispielnachrichten unter `spec/protocol/v<N>/examples/`; Referee und alle SDKs testen gegen dieselben Beispiele.
- **Synchronisation (E42):** Das SDK wendet `last_move` auf sein Brett an und vergleicht das Ergebnis mit `fen`. Verglichen wird mit der FEN, die der Kern aus `fen` erneut schreibt, damit ein En-passant-Feld ohne legales Schlagen nicht als Abweichung zählt (E48). Bei einer Abweichung protokolliert es eine Warnung und übernimmt `fen`; die Wiederholungshistorie geht dabei verloren. Eine Abweichung bedeutet einen Fehler im SDK.
- **Pufferung:** SDKs müssen nach jeder Nachricht flushen (häufige Fehlerquelle in C++/Java/Python).
- **Zeitmessung:** Die Uhr läuft beim Referee, nicht im Bot. Die im SDK angezeigte Restzeit ist eine lokale Schätzung ab Empfang von `turn`.
