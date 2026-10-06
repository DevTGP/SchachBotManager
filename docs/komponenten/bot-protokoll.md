# Bot-Protokoll (Referee ↔ Bot)

Einzige Schnittstelle zwischen Server und Bot-Prozess. Macht Spiele zwischen beliebigen Sprachen möglich, weil jeder Bot nur mit dem Referee spricht.

## Transport

| Transport | Einsatz | Bemerkung |
|-----------|---------|-----------|
| `stdio` | Sandbox auf dem Server, lokale Arena | Kein Netzwerk nötig → Sandbox läuft ohne Netzwerk |
| `tcp` (localhost) | Lokales Debugging: Bot wird aus der IDE gestartet und verbindet sich zur Arena | Nur lokal |
| `remote` (WebSocket über TLS) | Lokaler Bot gegen Web-API | Token-Auth, siehe [lokale-entwicklung.md](lokale-entwicklung.md) |

Die Nachrichten sind in allen Transporten identisch; das SDK kapselt den Transport vollständig.

## Format

- Eine Nachricht = eine Zeile UTF-8-JSON (NDJSON), Maximalgröße pro Zeile begrenzt (z. B. 64 KiB).
- `stdout` gehört ausschließlich dem Protokoll. Debug-Ausgaben gehen über `stderr` (das SDK erzwingt das).
- Jede Nachricht hat `type` und `v` (Protokollversion).
- Züge in UCI-Notation (`e2e4`, `e7e8q`), Stellungen als FEN.

## Nachrichten

| Richtung | `type` | Inhalt |
|----------|--------|--------|
| R → B | `init` | Unterstützte Protokollversionen (`supported`), Spiel-ID, Farbe, Start-FEN, Zeitkontrolle, Startbudget, feste Speicher-Schutzgrenze (A14, nur zur Information, z. B. für die Größe der Hashtabelle), Disziplin, Gegnername |
| B → R | `ready` | Gewählte Protokollversion (`v`), SDK-Version (`sdk`), Sprache (`lang`); muss innerhalb des Startbudgets kommen |
| R → B | `turn` | Letzter Gegnerzug (oder `null`), eigene/gegnerische Restzeit in ms, Zugnummer, optional FEN zur Synchronisation |
| B → R | `move` | Zug in UCI; optional `info` (Bewertung, Tiefe, Freitext – nur Anzeige, begrenzte Größe) |
| R → B | `game_over` | Ergebnis, Grund; danach kurze Frist bis zum Beenden |
| B → R | `resign` | Optional: Aufgabe |
| R → B | `error` | Protokollverstoß vor Abbruch (nur Diagnose) |

Bewusst **nicht** enthalten: Remisangebote, Zugrücknahme, Nachrichten zwischen Bots.

## Zustandsautomat aus Bot-Sicht

```
START → (init) → INITIALIZING → ready → IDLE
IDLE → (turn) → THINKING → move → IDLE
IDLE/THINKING → (game_over) → ENDED
```

Außerhalb von `THINKING` ist der Prozess auf dem Server eingefroren.

## Fehlerbehandlung

| Ereignis | Folge |
|----------|-------|
| Kein `ready` im Startbudget | Niederlage (`startup_timeout`) |
| Ungültiges JSON, unbekannter `type`, Verstoß gegen das Schema, zu lange Zeile | Niederlage (`protocol_violation`) |
| `v` in `ready` nicht in `supported` | Niederlage (`protocol_violation`) |
| Illegaler oder nicht parsbarer Zug | Niederlage (`illegal_move`) |
| Prozess endet / stürzt ab | Niederlage (`crash`) |
| Speicherlimit überschritten | Niederlage (`memory_limit`) |
| Zeit abgelaufen | Niederlage (`timeout`), Prozess wird hart beendet |

## Zu beachten

- **Versionierung (E36):** `v` ist eine Ganzzahl und steigt nur bei inkompatiblen Änderungen; neue optionale Felder ändern sie nicht. Der Referee nennt in `init` die unterstützten Versionen, der Bot wählt in `ready` eine davon; alle weiteren Nachrichten tragen diese Version. Jede SDK-Version spricht genau eine Protokollversion; ein Bot ist an die SDK-Version gebunden, mit der er verifiziert wurde.
- **Strenge:** Das SDK ignoriert unbekannte Felder in Nachrichten des Referees. Der Referee prüft Nachrichten des Bots streng gegen das Schema (feindliche Eingabe).
- **Schema als Quelle der Wahrheit:** JSON Schema 2020-12 unter `spec/protocol/v<N>/`, Beispielnachrichten unter `spec/protocol/v<N>/examples/`; Referee und alle SDKs testen gegen dieselben Beispiele.
- **Pufferung:** SDKs müssen nach jeder Nachricht flushen (häufige Fehlerquelle in C++/Java/Python).
- **Zeitmessung:** Die Uhr läuft beim Referee, nicht im Bot. Die im SDK angezeigte Restzeit ist eine lokale Schätzung ab Empfang von `turn`.
