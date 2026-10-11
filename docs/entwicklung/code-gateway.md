# Code-Karte: sbm_gateway

Das Gateway unter `services/gateway` (Paket `sbm-gateway`, Modul `sbm_gateway`) verbindet WebSocket-Clients (Browser, Remote-Bots) mit dem Play-Runner. Es hat keinen Datenbankzugang und liest keine Spielinhalte (E112). Befehl: `sbm-gateway`. Konzepte: [gateway.md](../komponenten/gateway.md), Protokolle [gateway-v1](../../spec/protocol/gateway-v1/) und [relay-v1](../../spec/protocol/relay-v1/).

## Einstieg

| Befehl | Einstieg | Aufgabe |
|--------|----------|---------|
| `sbm-gateway` | `sbm_gateway.cli:main` | Liest die Umgebung, startet `Gateway` und wartet auf SIGTERM oder SIGINT |

`cli.main` setzt das Logging nach `SBM_LOG_LEVEL` und baut `GatewayConfig.from_env(os.environ)`. Ein `ValueError` aus der Konfiguration ergibt Exit-Code 1. `cli.run` ruft `Gateway.start`, wartet auf ein Signal und ruft dann `Gateway.stop`.

Die einzige Abhängigkeit ist `websockets` ab Version 15. Alles läuft in einer asyncio-Schleife.

Lesereihenfolge:

1. `config.py` – Adressen und Grenzen.
2. `messages.py` – was über die Leitungen geht.
3. `sessions.py` – `Session` und `Registry`, der Kern.
4. `links.py` – die beiden Enden einer Sitzung.
5. `client.py` und `relay.py` – je ein Handler für eine Verbindung.
6. `server.py` und `cli.py` – Start und Stopp.

## Module

| Modul | Aufgabe |
|-------|---------|
| [`__init__.py`](../../services/gateway/src/sbm_gateway/__init__.py) | Paketbeschreibung |
| [`cli.py`](../../services/gateway/src/sbm_gateway/cli.py) | `main` und `run`: Konfiguration, Start, Warten auf ein Signal, Stopp |
| [`config.py`](../../services/gateway/src/sbm_gateway/config.py) | `SOCKET_PATH` (`/api/v1/play/socket`) und die eingefrorene `GatewayConfig` mit `from_env`; `_positive` und `_port` prüfen Zahlen |
| [`server.py`](../../services/gateway/src/sbm_gateway/server.py) | `Gateway`: bindet Relay-Server (`asyncio.start_server`) und WebSocket-Server (`websockets` `serve`), hält die gebundenen Ports, stoppt beide |
| [`client.py`](../../services/gateway/src/sbm_gateway/client.py) | `check_path` (404 für andere Pfade), `handle_client` je WebSocket-Verbindung: Grenze `max_clients`, `_join`, `_carry` |
| [`relay.py`](../../services/gateway/src/sbm_gateway/relay.py) | `handle_relay` je TCP-Verbindung des Play-Runners: `attach`, dann Zeilen zum Client bis zum Ende; `LINE_LIMIT` |
| [`sessions.py`](../../services/gateway/src/sbm_gateway/sessions.py) | `Session` (ein Sitz: Relay, Client, wartende Zeilen) und `Registry` (alle Sitzungen und wartenden Clients); Protokolle `Client` und `Relay`; `Refused`, `PendingOverflow`, `REPLACED`, `SHUTDOWN` |
| [`links.py`](../../services/gateway/src/sbm_gateway/links.py) | `SocketClient` und `RelayLink` als Enden einer Sitzung, Close-Codes, `ClientGone`, Schließen im Hintergrund |
| [`messages.py`](../../services/gateway/src/sbm_gateway/messages.py) | Strenges Lesen (`parse_join`, `parse_attach`, `parse_line`), Bauen (`joined`, `refused_client`, `refused_relay`, `relay_line`, `PRESENT`, `ABSENT`), `seat_hash`, `InvalidMessage`, `MAX_LINE_CHARS` |

Eine Sitzung gehört zum Schlüssel `Key = (match_id, seat_hash)`. `seat_hash` ist der SHA-256 des Sitz-Tokens als Hex. Der Client schickt das Token, der Runner nur den Hash (E113).

## Ablauf

### Client verbindet sich (gateway-v1)

1. `websockets` prüft den Pfad mit `client.check_path`. Andere Pfade bekommen 404.
2. `client.handle_client` lehnt mit `busy` ab, wenn `registry.clients` die Grenze `max_clients` erreicht. Sonst zählt es den Client mit.
3. `client._join` liest die erste Nachricht innerhalb von `hello_seconds`. `messages.parse_join` liefert `match_id` und Token. Ein Fehler ergibt `invalid_message`.
4. `Registry.join` mit `(match_id, seat_hash(seat))`:
   - Sitzung vorhanden: `Session.bind` und zurück.
   - Sonst wartet der Client bis `join_wait_seconds` auf `attach`. Ein älterer wartender Client desselben Sitzes bekommt `REPLACED`.
   - Ergebnis `None` wird zu `no_game`, `REPLACED` zu `replaced`, `SHUTDOWN` zu `shutdown`.
5. `Session.bind` lehnt einen älteren Client mit `replaced` ab, sendet `joined`, dann die wartenden Zeilen, dann `present` an den Runner.
6. `client._carry` reicht jede Textnachricht über `Session.to_runner` als `line` weiter. Binär schließt mit 1003, mehr als `MAX_LINE_CHARS` Zeichen mit 1009.
7. Endet die Verbindung, meldet `Session.leave` dem Runner `absent`, sofern der Client noch den Sitz hält.

### Runner verbindet sich (relay-v1)

1. Der Play-Runner öffnet eine TCP-Verbindung je Sitz. `relay.handle_relay` liest die erste Zeile innerhalb von `hello_seconds`.
2. `messages.parse_attach` liefert den Schlüssel. `Registry.attach` legt die `Session` an oder wirft `Refused` (`attached`, `busy`). Fehler gehen als `refused` zurück, danach schließt die Verbindung.
3. Wartet schon ein Client, bindet `attach` ihn sofort (`Session.bind`).
4. Jede weitere Zeile geht durch `parse_line` und `Session.to_client`. Fehlt der Client, landet sie in der Warteschlange. Über `max_pending_lines` wirft `to_client` `PendingOverflow`.
5. Ende der Eingabe ergibt den Grund `game over`. Ein Protokollbruch oder `ConnectionError` ergibt `relay error`, `PendingOverflow` ergibt `the client was away too long`.
6. Im `finally` ruft es `Registry.detach` und `RelayLink.close`. `Session.close` beendet den Client mit 1000 nach den schon gesendeten Zeilen.

### Stopp

`Gateway.stop` schließt den Relay-Server und ruft `Registry.shutdown`. Wartende Clients bekommen `shutdown` (Close-Code 1001). Jede Sitzung schließt ihr Relay und wird gelöst. Danach schließt der WebSocket-Server.

## Konventionen

- **Streng lesen:** `messages._exact` verlangt genau die Felder der Spezifikation und prüft sie per Regex. Fehler sind `InvalidMessage` (eine Unterklasse von `ValueError`). Neue Nachrichten folgen diesem Muster.
- **Bauen an einer Stelle:** Nachrichten entstehen nur in `messages.py`. Für den Client sind sie `str`, für das Relay `bytes` mit Zeilenende.
- **Inhalt bleibt unberührt:** `line.data` geht unverändert durch. Das Gateway kennt weder Züge noch Partien. Es gibt keinen Zugriff auf `sbm_store`.
- **Eine Sperre je Sitzung:** Alle Methoden von `Session` laufen unter `self._lock`. Damit bleibt die Reihenfolge `joined`, wartende Zeilen, `present` erhalten.
- **Ergebnis statt Ausnahme:** `Registry.join` gibt `Session`, `None`, `REPLACED` oder `SHUTDOWN` zurück. Erst `client._join` macht daraus `refused`.
- **Enden über Protokolle:** `Session` kennt nur `Client` und `Relay` (`typing.Protocol`), nicht `websockets` oder `asyncio.StreamWriter`. Das hält die Sitzungslogik frei von Transportdetails.
- **Schreibfehler am Relay werden ignoriert:** `RelayLink.send` schluckt `ConnectionError`. Ein kaputtes Relay zeigt sich als Ende seiner Eingabe in `handle_relay`.
- **Schreibfehler am Client werden zu `ClientGone`:** `Session` behält die Zeile dann für den nächsten Client.
- **Schließen im Hintergrund:** `SocketClient.end` und `refuse` ohne `wait` laufen über `_in_background`, damit keine Sitzung auf den Close-Handshake wartet. Der eigene Handler einer Verbindung ruft `refuse(..., wait=True)`.
- **Close-Codes:**

  | Code | Wann |
  |------|------|
  | 1000 | Partie oder Relay zu Ende (`end`) |
  | 1001 | `refused` mit `shutdown` |
  | 1003 | Binärnachricht |
  | 1008 | jedes andere `refused` |
  | 1009 | Nachricht zu lang |

- **Konfiguration:** Nur `from_env` liest die Umgebung. Ungültige Werte ergeben `ValueError` mit dem Namen der Variablen. Werte ohne Variable bleiben Felder mit Standard.
- **Logging:** `log = logging.getLogger(__name__)` je Modul, in `cli.py` der Name `sbm_gateway`. Geloggt wird `match_id`, nie das Sitz-Token.

## Erweitern

### Protokoll ändern (neue Nachricht, neues Feld, neuer Ablehnungsgrund)

1. Spezifikation zuerst: Schema unter `spec/protocol/gateway-v1/` (Client-Seite) oder `spec/protocol/relay-v1/` (Runner-Seite) anpassen. Bei einer neuen Nachricht auch die Vereinigung erweitern: `gateway_message.schema.json` für Nachrichten des Gateways (in beiden Protokollen), `runner_message.schema.json` für Nachrichten des Runners.
2. Beispiele unter `examples/valid/` und `examples/invalid/` als `<typ>.<fall>.json` anlegen und `spec-check spec` laufen lassen.
3. `messages.py`: Leser mit `_exact` oder Bauer ergänzen. Grenzen wie `MAX_LINE_CHARS` dort halten.
4. Logik in `sessions.py`, Verdrahtung in `client.py` bzw. `relay.py`.
5. Gegenstellen nachziehen:
   - relay-v1: [`play/relay_connection.py`](../../services/runner/src/sbm_runner/play/relay_connection.py) im Runner.
   - gateway-v1: [`remote/channel.py`](../../sdk/python/src/sbm/remote/channel.py) im Python-SDK und [`play/protocol.ts`](../../frontend/src/play/protocol.ts) im Frontend.
6. Tests: `tests/test_messages.py` für Lesen und Bauen, `tests/test_gateway.py` für den Ablauf über echte Verbindungen. Im Runner `tests/play/` und im Frontend `src/pages/play.test.tsx` prüfen.
7. Doku: Tabellen in [gateway.md](../komponenten/gateway.md) und die Entscheidung in `docs/00_entscheidungen.md` nachführen.

### Neue Grenze oder Umgebungsvariable

1. Feld mit Standard in `GatewayConfig` anlegen, mit Kommentar.
2. Soll es einstellbar sein: in `from_env` über `_positive` oder `_port` lesen.
3. Verwendung in `sessions.py`, `client.py` oder `relay.py` über `config`, nie über `os.environ`.
4. Test: Wert in der Fixture `config` setzen und das Verhalten in `test_gateway.py` prüfen.
5. Bei Bedarf in `deploy/compose.yaml` beim Dienst `gateway` setzen und die Tabelle „Betrieb“ in [gateway.md](../komponenten/gateway.md) ergänzen.

## Tests

Die Tests liegen unter `services/gateway/tests/`. Sie brauchen keine MongoDB und keine Sandbox.

| Hilfe | Ort | Zweck |
|-------|-----|-------|
| `MATCH_ID`, `SEAT`, `TIMEOUT` | `conftest.py` | Gültige Kennung, gültiges Token, Zeitgrenze für Empfang (5 s) |
| `RunningGateway` | `conftest.py` | Startet ein echtes `Gateway` in einem eigenen Thread mit eigener Schleife; `client()` öffnet eine synchrone WebSocket-Verbindung, `relay()` eine TCP-Verbindung |
| `RelayEnd` | `conftest.py` | Spielt den Runner: `send`, `attach`, `line`, `receive`, `close` |
| `join`, `receive` | `conftest.py` | `join` senden, nächste Client-Nachricht als JSON lesen |
| Fixture `config` | `conftest.py` | `127.0.0.1`, Ports 0 (frei gewählt), `join_wait_seconds=2` |
| Fixture `gateway` | `conftest.py` | Laufendes `RunningGateway`, am Ende gestoppt |

| Datei | Inhalt |
|-------|--------|
| `test_gateway.py` | Ende-zu-Ende-Abläufe: Warten auf den Runner, Zeilen in beide Richtungen, Ende nach der letzten Zeile, wartende Zeilen, Ersetzen, falscher Sitz, schlechte erste Nachricht, zweites und schlechtes `attach`, Protokollbruch des Relays, Binärnachricht, andere Pfade, Stopp |
| `test_messages.py` | Strenges Lesen und gebaute Nachrichten; vergleicht mit festen Literalen, nicht mit den Schema-Dateien |

Befehle aus dem Repo-Wurzelverzeichnis:

- Installieren: `pip install -e "services/gateway[dev]"`
- Tests: `pytest services/gateway`
- Lint und Format: `ruff check services/gateway` und `ruff format --check services/gateway`

Besonderheiten:

- Port 0 in der Konfiguration lässt das Betriebssystem einen freien Port wählen. `Gateway` merkt sich die gebundenen Ports.
- Die Runner-Tests unter `services/runner/tests/play/` starten das echte Gateway (`pytest.importorskip("sbm_gateway")`). `play/test_sdk_remote.py` prüft dort den Transport `remote` des Python-SDK dagegen. Nach Änderungen am Gateway auch `pytest services/runner` laufen lassen.
- Lokal mit Runner: `sbm-gateway`, dann `SBM_RUNNER_ROLE=play SBM_SANDBOX=none sbm-runner`.
- In CI laufen die Tests im Job `services`.
