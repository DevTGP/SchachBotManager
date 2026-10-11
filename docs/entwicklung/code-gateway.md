# Code-Karte: sbm_gateway

Das Gateway unter `services/gateway` (Paket `sbm-gateway`, Modul `sbm_gateway`) verbindet WebSocket-Clients (Browser, Remote-Bots) mit dem Play-Runner. Es hat keinen Datenbankzugang und liest keine Spielinhalte (E112). Außerdem nimmt es die Züge laufender Partien von den Runnern an und liefert sie als Server-Sent Events (Live-Kanal, E142). Befehl: `sbm-gateway`. Konzepte: [gateway.md](../komponenten/gateway.md), Protokolle [gateway-v1](../../spec/protocol/gateway-v1/), [relay-v1](../../spec/protocol/relay-v1/) und [live-v1](../../spec/protocol/live-v1/).

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
6. `feeds.py`, dann `live.py` und `watch.py` mit `live_messages.py`, `watch_request.py` und `events.py` – der Live-Kanal.
7. `server.py` und `cli.py` – Start und Stopp.

## Module

| Modul | Aufgabe |
|-------|---------|
| [`__init__.py`](../../services/gateway/src/sbm_gateway/__init__.py) | Paketbeschreibung |
| [`cli.py`](../../services/gateway/src/sbm_gateway/cli.py) | `main` und `run`: Konfiguration, Start, Warten auf ein Signal, Stopp |
| [`config.py`](../../services/gateway/src/sbm_gateway/config.py) | `SOCKET_PATH` (`/api/v1/play/socket`), `WATCH_PATH` (Regex für `/api/v1/matches/{id}/live`) und die eingefrorene `GatewayConfig` mit `from_env`; `_positive` und `_port` prüfen Zahlen |
| [`server.py`](../../services/gateway/src/sbm_gateway/server.py) | `Gateway`: bindet Relay-, Live- und Watch-Server (`asyncio.start_server`) und WebSocket-Server (`websockets` `serve`), hält die gebundenen Ports (`live_port`, `watch_port`), hält `feeds`, stoppt alle und schließt offene Verbindungen des Live-Kanals |
| [`client.py`](../../services/gateway/src/sbm_gateway/client.py) | `check_path` (404 für andere Pfade), `handle_client` je WebSocket-Verbindung: Grenze `max_clients`, `_join`, `_carry` |
| [`relay.py`](../../services/gateway/src/sbm_gateway/relay.py) | `handle_relay` je TCP-Verbindung des Play-Runners: `attach`, dann Zeilen zum Client bis zum Ende; `LINE_LIMIT` |
| [`sessions.py`](../../services/gateway/src/sbm_gateway/sessions.py) | `Session` (ein Sitz: Relay, Client, wartende Zeilen) und `Registry` (alle Sitzungen und wartenden Clients); Protokolle `Client` und `Relay`; `Refused`, `PendingOverflow`, `REPLACED`, `SHUTDOWN` |
| [`links.py`](../../services/gateway/src/sbm_gateway/links.py) | `SocketClient` und `RelayLink` als Enden einer Sitzung, Close-Codes, `ClientGone`, Schließen im Hintergrund |
| [`feeds.py`](../../services/gateway/src/sbm_gateway/feeds.py) | `Feed` (Züge einer laufenden Partie als fertige Ereignisse, Zuschauer als `asyncio.Queue`) und `Feeds` (alle Feeds, `open` ersetzt einen älteren, `find` wartet auf ein `open`, `shutdown`, Zähler `watchers`); `FeedError`, `Busy`, `CLOSE` |
| [`live.py`](../../services/gateway/src/sbm_gateway/live.py) | `handle_live` je TCP-Verbindung eines Runners: `open`, dann Züge in den Feed bis `end` oder Ende der Eingabe; `LINE_LIMIT` |
| [`live_messages.py`](../../services/gateway/src/sbm_gateway/live_messages.py) | Strenges Lesen von live-v1: `parse_open`, `parse_line` (`move` mit genau `MOVE_FIELDS` oder `end`) |
| [`watch.py`](../../services/gateway/src/sbm_gateway/watch.py) | `handle_watch` je HTTP-Verbindung eines Zuschauers: Anfrage lesen, Grenze `max_watchers`, Feed suchen, Ereignisse schreiben, `: ping` nach `watch_ping_seconds`; Fehler als JSON mit `code` und `message` |
| [`watch_request.py`](../../services/gateway/src/sbm_gateway/watch_request.py) | `parse_head`: Anfragezeile und `Last-Event-ID` zu `WatchRequest(match_id, after)`; `BadRequest` mit Status und Code; `HEAD_LIMIT` |
| [`events.py`](../../services/gateway/src/sbm_gateway/events.py) | Server-Sent Events als Text: `move(data)`, `END`, `PING`, `RETRY` |
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

### Live-Kanal (live-v1 und Server-Sent Events, E142)

1. Ein Runner öffnet eine TCP-Verbindung zum Live-Port. `live.handle_live` liest `open` innerhalb von `hello_seconds` (`parse_open`).
2. `Feeds.open` legt den Feed an; ein älterer Feed derselben Partie endet mit `end` für seine Zuschauer. Bei `max_feeds` wirft es `Busy`, die Verbindung schließt.
3. Jede `move`-Zeile geht über `Feed.add` als fertiges Ereignis an alle Zuschauer. Ein Halbzug außer der Reihe oder über `max_feed_moves` wirft `FeedError` und beendet die Verbindung.
4. `end` oder das Ende der Eingabe ruft im `finally` `Feeds.close`: Der Feed endet, Zuschauer bekommen `end`.
5. Ein Zuschauer verbindet sich über den `frontend`-Nginx mit dem Watch-Port. `watch.handle_watch` liest den Kopf bis zur Leerzeile (`parse_head`), prüft `max_watchers` und sucht mit `Feeds.find` bis `feed_wait_seconds` den Feed, sonst 404 `not_live`.
6. `_stream` schreibt den Antwortkopf mit `X-Accel-Buffering: no` und `RETRY`, dann die Ereignisse aus `Feed.watch(after)`: erst die Züge nach `after`, dann jeden neuen, zum Schluss `END`. `CLOSE` (beim Stopp) beendet den Strom ohne `end`.

### Stopp

`Gateway.stop` schließt den Relay-Server und ruft `Registry.shutdown`. Für den Live-Kanal schließt es Live- und Watch-Server und ruft `Feeds.shutdown`; Zuschauer bekommen `CLOSE` und verbinden sich im Browser neu. Wartende Clients bekommen `shutdown` (Close-Code 1001). Jede Sitzung schließt ihr Relay und wird gelöst. Danach schließt der WebSocket-Server.

## Konventionen

- **Streng lesen:** `messages._exact` verlangt genau die Felder der Spezifikation und prüft sie per Regex. Fehler sind `InvalidMessage` (eine Unterklasse von `ValueError`). Neue Nachrichten folgen diesem Muster.
- **Bauen an einer Stelle:** Nachrichten entstehen nur in `messages.py`. Für den Client sind sie `str`, für das Relay `bytes` mit Zeilenende.
- **Inhalt bleibt unberührt:** `line.data` geht unverändert durch. Das Gateway kennt im Relay weder Züge noch Partien. Es gibt keinen Zugriff auf `sbm_store`. Im Live-Kanal prüft es nur die Form der Züge (live-v1) und gibt sie unverändert als `data` weiter.
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
| `LiveEnd` | `conftest.py` | Spielt den Runner im Live-Kanal über eine TCP-Verbindung zum Live-Port |
| `WatchEnd` | `conftest.py` | Spielt einen Zuschauer: HTTP-Anfrage an den Watch-Port, liest Status und Ereignisse |
| `move(ply)` | `conftest.py` | Gültiger Zug für live-v1 |
| `join`, `receive` | `conftest.py` | `join` senden, nächste Client-Nachricht als JSON lesen |
| Fixture `config` | `conftest.py` | `127.0.0.1`, alle Ports 0 (frei gewählt), `join_wait_seconds=2` |
| Fixture `gateway` | `conftest.py` | Laufendes `RunningGateway`, am Ende gestoppt |

| Datei | Inhalt |
|-------|--------|
| `test_gateway.py` | Ende-zu-Ende-Abläufe: Warten auf den Runner, Zeilen in beide Richtungen, Ende nach der letzten Zeile, wartende Zeilen, Ersetzen, falscher Sitz, schlechte erste Nachricht, zweites und schlechtes `attach`, Protokollbruch des Relays, Binärnachricht, andere Pfade, Stopp |
| `test_messages.py` | Strenges Lesen und gebaute Nachrichten; vergleicht mit festen Literalen, nicht mit den Schema-Dateien |
| `test_live.py` | Live-Kanal über echte Verbindungen: Folgen ab einem Halbzug bis `end`, `Last-Event-ID`, kurzes Warten auf den Runner, `not_live`, Abbruch und Ersetzen des Runners, Züge außer der Reihe, schlechtes `open`, schlechte Anfragen, zu viele Zuschauer, Stopp, Pings |
| `test_live_messages.py` | live-v1 gegen die gültigen und ungültigen Beispiele unter `spec/protocol/live-v1/examples/` |
| `test_feeds.py` | `Feed` und `Feeds` ohne Netz: späte Zuschauer, Reihenfolge und Grenze, Ersetzen, Warten auf `open`, Grenze der Feeds, Stopp |
| `test_watch_request.py` | `parse_head`: `after`, `Last-Event-ID`, abgewiesene Anfragen |

Befehle aus dem Repo-Wurzelverzeichnis:

- Installieren: `pip install -e "services/gateway[dev]"`
- Tests: `pytest services/gateway`
- Lint und Format: `ruff check services/gateway` und `ruff format --check services/gateway`

Besonderheiten:

- Port 0 in der Konfiguration lässt das Betriebssystem einen freien Port wählen. `Gateway` merkt sich die gebundenen Ports.
- Die Runner-Tests unter `services/runner/tests/play/` starten das echte Gateway (`pytest.importorskip("sbm_gateway")`). `play/test_sdk_remote.py` prüft dort den Transport `remote` des Python-SDK dagegen. Nach Änderungen am Gateway auch `pytest services/runner` laufen lassen.
- Lokal mit Runner: `sbm-gateway`, dann `SBM_RUNNER_ROLE=play SBM_SANDBOX=none sbm-runner`.
- In CI laufen die Tests im Job `services`.
