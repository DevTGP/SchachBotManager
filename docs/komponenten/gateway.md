# Gateway und Play-Runner (interaktive Partien)

Partien gegen Menschen im Browser und gegen Bots auf dem Rechner eines Nutzers (M7). Beide laufen an der Queue vorbei (E24) über einen eigenen Runner und einen WebSocket-Gateway (E111, E112). Umgesetzt sind alle drei Schritte (E111): die gemeinsame Basis, Mensch gegen Bot (E114) und Remote-Bots (E116).

## Aufbau

```
Browser / lokaler Bot ──WebSocket──► frontend (nginx) ──► gateway ◄──TCP (Relay-Netz)── runner-play ──► nsjail: Bot
                         /api/v1/play/socket                          relay-v1                    │
                                                                                                   └──► MongoDB
```

| Teil | Ort | Aufgabe |
|------|-----|---------|
| `gateway` | `services/gateway` (Paket `sbm-gateway`, Befehl `sbm-gateway`) | Nimmt WebSockets an, paart sie mit dem Sitz einer Partie, reicht Nachrichten unverändert weiter. Ohne Rechte, ohne Datenbankzugang |
| `runner-play` | `services/runner` mit `SBM_RUNNER_ROLE=play` | Holt Jobs der Art `play`, spielt bis `SBM_PLAY_SLOTS` Partien gleichzeitig, startet Bots in nsjail wie der Queue-Runner, verbindet jeden Sitz über das Relay mit dem Gateway |
| Web-API | `backend` | Legt interaktive Partien an (`POST /play`, `POST /remote/matches`), prüft die Grenzen und gibt den Sitz-Token einmal aus (E114–E116) |

## Sitze

Eine Seite, die kein Bot ist, hat einen Sitz (E113):

- Die API erzeugt einen Token aus 32 Zufallsbytes (base64url, 43 Zeichen) und gibt ihn genau einmal aus. In der Partie steht nur sein SHA-256 (`seat_hash`).
- Der Client nennt beim Verbinden Partie und Token (`join`), der Play-Runner nennt Partie und Hash (`attach`). Der Gateway paart beide; er kennt keine Partien und braucht deshalb keine Datenbank.
- Wer den Token kennt, hält den Sitz. Eine neue Verbindung mit demselben Token ersetzt die ältere (`refused` mit `replaced`), etwa nach einem Neuladen der Seite.

## Protokolle

| Protokoll | Strecke | Spezifikation |
|-----------|---------|---------------|
| gateway-v1 | Client ↔ Gateway, Eröffnung der WebSocket-Verbindung | `spec/protocol/gateway-v1/`: `join`, dann `joined` oder `refused` |
| relay-v1 | Play-Runner ↔ Gateway, JSON-Zeilen über TCP | `spec/protocol/relay-v1/`: `attach`, `line` in beide Richtungen, `present`, `absent`, `refused` |
| Spielprotokoll | Nach `joined`, je WebSocket-Nachricht eine Zeile | Remote-Bot: Bot-Protokoll v1 (`spec/protocol/v1/`), Seite als `RelayPlayer`; Browser: play-v1 (`spec/protocol/play-v1/`), Seite als `HumanPlayer` (E114) |

Ablauf einer Verbindung:

1. Client öffnet `wss://…/api/v1/play/socket` und sendet innerhalb von 10 s `join`.
2. Hat der Play-Runner den Sitz schon angemeldet, antwortet der Gateway `joined`, sendet die für den Client aufgehobenen Zeilen und meldet dem Runner `present`. Sonst wartet der Client bis zu 30 s auf den Runner, danach `refused` mit `no_game`.
3. Danach reicht der Gateway jede Textnachricht als `line` an den Runner und jede `line` des Runners als Textnachricht an den Client.
4. Trennt sich der Client, meldet der Gateway `absent`; Zeilen für ihn hebt er auf (höchstens 256, sonst endet die Partie).
5. Schließt der Runner das Relay (Partie zu Ende), schließt der Gateway die WebSocket-Verbindung nach der letzten Zeile mit Code 1000.

| Close-Code | Bedeutung |
|------------|-----------|
| 1000 | Partie zu Ende |
| 1001 | Gateway stoppt (`refused` mit `shutdown` vorher, falls der Client noch wartet) |
| 1003 | Binärnachricht; nur Text ist erlaubt |
| 1008 | Abgewiesen; der Grund steht in `refused` davor |
| 1009 | Nachricht mit mehr als 65 536 Zeichen |

## Grenzen

| Grenze | Wert |
|--------|------|
| Partien gleichzeitig (Play-Runner) | `max_games` auf `/admin/play` (Standard 2), höchstens `PLAY_SLOTS` des Containers |
| Sitzungen im Gateway | 32 |
| WebSocket-Verbindungen | 128 |
| Zeit bis `join` bzw. `attach` | 10 s |
| Wartezeit eines Clients auf den Runner | 30 s |
| Wartezeit des Runners auf alle Sitze vor Partiebeginn | 30 s, sonst Abbruch |
| Abwesenheit während der Partie | 60 s, danach Abbruch ohne Ergebnis |
| Aufgehobene Zeilen je abwesendem Client | 256 |
| Ping | alle 20 s, Antwort binnen 20 s |

Grenzen je Adresse, Konto und Token (gleichzeitig und pro Tag) und die Plätze insgesamt setzt die Web-API beim Anlegen der Partie nach den Einstellungen auf `/admin/play` (E115); der Play-Runner nimmt höchstens `min(PLAY_SLOTS, max_games)` Partien.

## Mensch gegen Bot (E114)

| Schritt | Ablauf |
|---------|--------|
| Anlegen | `/play` in der SPA: Bot, Farbe, Disziplin oder freie Zeiten; `POST /play` gibt Partie und Sitz-Token; die SPA hält den Token im `localStorage` |
| Verbinden | `/play/:id` öffnet die WebSocket-Verbindung, nimmt den Sitz ein und erhält nach `joined` den Stand als `state` |
| Ziehen | Die SPA bietet nur die Züge aus `legal_moves` an (Ziehen oder Anklicken, Umwandlung per Auswahl) und sendet `move`; ein abgewiesener Zug kommt als `error` zurück |
| Aufgeben | `resign`, mit Rückfrage; während der Bot rechnet, wirkt es zu Beginn des nächsten eigenen Zuges |
| Neuladen | Die SPA verbindet sich neu und nimmt den Sitz wieder ein; der `HumanPlayer` sendet den ganzen Stand erneut, die laufende Uhr um die Zeit seit dem letzten Stand verringert |

## Wertung (E117)

Spielt ein Mensch mit Konto unter einer gespeicherten Disziplin aus der Grundstellung, ist die Partie `rated`; Gäste, freie Zeiten und Remote-Partien nicht. Der Play-Runner verbucht nach jeder Partie sofort (`sbm_store.ratings.count_pending`), außer während eine Neuberechnung ansteht (E105); ein Datenbankfehler dabei wird nur protokolliert, der nächste Lauf holt es nach. Das Rating des Kontos steht auf der Kontoseite und mit Namen in der Rangliste der Spieler (E118); die Partien bleiben privat.

## Remote-Bots (E116)

Ein Coder legt auf der Kontoseite ein API-Token an und startet seinen Bot mit `--remote URL --opponent NAME` (Token in `SBM_TOKEN`). Das Python-SDK fragt `POST /remote/matches` an, nimmt den Sitz über den Gateway ein und spricht danach das Bot-Protokoll v1. Die Netzlaufzeit zählt zur Bedenkzeit; es gibt keinen Ausgleich.

## Fehlerfälle (E113)

Eine interaktive Partie kann nicht neu beginnen, weil ein Mensch oder ein lokaler Bot auf sie wartet. Der Play-Runner bricht sie deshalb ab statt sie zu wiederholen (`aborted`, Ergebnis `*`):

| Fall | Folge |
|------|-------|
| Sitz wird nicht binnen 30 s eingenommen | Abbruch vor dem Start |
| Gateway nicht erreichbar oder Relay bricht ab | Abbruch |
| Client länger als 60 s abwesend | Abbruch |
| Play-Runner stirbt (Lease läuft ab) | Abbruch durch den nächsten Play-Runner |
| Play-Runner wird gestoppt (SIGTERM) | Laufende Partien werden abgebrochen |
| Partie steht beim Abholen schon auf `running` | Abbruch, kein Neustart |

Ein Bot auf dem Server läuft wie in der Queue: Sandbox, Einfrieren außerhalb des eigenen Zuges, dieselben Endgründe. Die Seite eines Sitzes wird nie eingefroren; ihre Zeit misst der Referee auf dem Server und schließt die Netzlaufzeit ein.

## Sicherheit

- Der Gateway hängt am internen Netz (für den `frontend`-Nginx) und am Relay-Netz. Den Relay-Port bindet er nur an seine Adresse im Relay-Netz (`SBM_RELAY_HOST=sbm-relay`); dort hängt außer ihm nur `runner-play`. So braucht das Relay kein Geheimnis (E112).
- Der privilegierte Play-Runner baut die Verbindung zum Gateway selbst auf und nimmt keine Verbindungen an.
- Der Gateway liest keine Spielnachrichten; über Legalität, Zeit und Ergebnis entscheidet allein der Referee im Play-Runner, der jede Zeile eines Remote-Bots wie die eines Bots in der Sandbox prüft.
- Sitz-Token stehen nie in der Datenbank, nur ihr Hash.

## Betrieb

| Variable | Dienst | Bedeutung |
|----------|--------|-----------|
| `SBM_RELAY_HOST`, `SBM_RELAY_PORT` | `gateway` | Adresse des Relay-Ports (Standard `127.0.0.1:9000`) |
| `SBM_GATEWAY_PORT` | `gateway` | WebSocket-Port (Standard 8001) |
| `SBM_GATEWAY_MAX_SESSIONS`, `SBM_GATEWAY_MAX_CLIENTS` | `gateway` | Grenzen oben |
| `SBM_RUNNER_ROLE` | Runner | `queue` (Standard) oder `play` |
| `SBM_RELAY_ADDRESS` | `runner-play` | `host:port` des Relays (Standard `127.0.0.1:9000`) |
| `SBM_PLAY_SLOTS` | `runner-play` | Partien gleichzeitig (Compose: `PLAY_SLOTS`, Standard 2) |

Lokal ohne Container: `sbm-gateway` starten, dann `SBM_RUNNER_ROLE=play SBM_SANDBOX=none sbm-runner` (ohne Sandbox spielen nur die Referenzbots).

## Zu beachten

- **Fairness:** Interaktive Partien laufen neben der Queue-Partie; ein rechnender Bot einer interaktiven Partie kostet die Queue-Partie Rechenzeit (R10, E24).
- **Speicher:** Jeder Bot darf 1 GiB belegen; mit zwei Plätzen und der Queue-Partie sind es auf dem Server bis zu 3 GiB.
- **Proxy:** Im Nginx Proxy Manager muss „Websockets Support“ für den Proxy-Host aktiv sein ([deployment.md](deployment.md)).
