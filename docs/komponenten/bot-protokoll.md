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
| R → B | `init` | Spiel-ID, Farbe, Start-FEN, Zeitkontrolle, Limits (Speicher, Startbudget), Disziplin, Gegnername |
| B → R | `ready` | SDK-Version, Sprache; muss innerhalb des Startbudgets kommen |
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
| Ungültiges JSON, unbekannter `type`, zu lange Zeile | Niederlage (`protocol_violation`) |
| Illegaler oder nicht parsbarer Zug | Niederlage (`illegal_move`) |
| Prozess endet / stürzt ab | Niederlage (`crash`) |
| Speicherlimit überschritten | Niederlage (`memory_limit`) |
| Zeit abgelaufen | Niederlage (`timeout`), Prozess wird hart beendet |

## Zu beachten

- **Versionierung:** Protokollversion wird in `init`/`ready` ausgehandelt; ein Bot ist an die SDK-Version gebunden, mit der er verifiziert wurde.
- **Schema als Quelle der Wahrheit:** JSON-Schema unter `spec/protocol/`; Referee und alle SDKs testen gegen dieselben Beispiel-Nachrichten.
- **Pufferung:** SDKs müssen nach jeder Nachricht flushen (häufige Fehlerquelle in C++/Java/Python).
- **Zeitmessung:** Die Uhr läuft beim Referee, nicht im Bot. Die im SDK angezeigte Restzeit ist eine lokale Schätzung ab Empfang von `turn`.
