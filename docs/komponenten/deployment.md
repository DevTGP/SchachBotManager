# Deployment und Betrieb

## Dienste (ein Docker-Compose-Stack, E28)

| Dienst | Netz | Besonderheit |
|--------|------|--------------|
| `frontend` | `local-web` + intern | Liefert den statischen SPA-Build aus, reicht `/api` an `api` und `/api/v1/play/socket` als WebSocket an `gateway` weiter; einziger Dienst, auf den der Proxy zeigt |
| `gateway` | intern + `relay` | WebSockets interaktiver Partien, ohne Rechte und ohne Datenbankzugang; Relay-Port nur im Netz `relay` (E112) |
| `api` | intern | Flask hinter WSGI-Server; kann keine Prozesse starten |
| `scheduler` | intern | Genau eine Instanz |
| `runner` | intern | Container mit erweiterten Rechten (A13), startet Bots über nsjail und führt auch die Verifikation aus (E81); Parallelität aus den Einstellungen in der DB |
| `runner-play` | intern + `relay` | Dasselbe Image und dieselben Rechte wie `runner`, Rolle `play`: spielt nur interaktive Partien, bis `PLAY_SLOTS` gleichzeitig (E111) |
| `mongo` | intern | Als Replica Set (Einzelknoten, ab M4, E75), Authentifizierung aktiv, Daten auf einem Volume |

Bot-Prozesse haben kein Netzwerk. Laufzeiten der fünf Sprachen, SDK und C++-Kern sind Teil des `runner`-Images und werden von dort read-only in die Sandbox eingehängt.

## Einbindung in den bestehenden Proxy (E29)

| Punkt | Umsetzung |
|-------|-----------|
| Netz | `local-web` wird im Compose-File als externes Netz eingebunden; nur `frontend` hängt daran |
| Proxy-Host | Im Nginx Proxy Manager: Subdomain → `frontend`, Port des Containers; einmalig von Hand anzulegen |
| TLS | Zertifikat über den Nginx Proxy Manager |
| WebSocket | Im Proxy-Host „Websockets Support“ aktivieren; nötig für Mensch gegen Bot und Remote-Bots (E112) |
| Zeitlimits | Lange Verbindungen: Lese-Timeout des Proxys für WebSockets hochsetzen |
| Upload-Größe | Maximale Request-Größe im Proxy passend zum Upload-Limit |
| Echte Client-IP | Weitergereichte IP-Header nur vom Proxy akzeptieren (für Rate-Limits pro IP) |
| Ports | Der Stack veröffentlicht keine Ports auf dem Host |

Welche Angaben wohin gehören, steht unter „Stand M2“.

## GitHub Actions

| Workflow | Auslöser | Schritte |
|----------|----------|----------|
| CI | Pull Request, Push, manuell; je Job nur bei Änderungen in seinem Bereich (E79) | Lint + Tests je Paket (Backend, Frontend, Dienste, Kern, Bindings), Kernvektoren, Binding-Tests, Kreuztest über die Arena, Analyzer-Tests |
| Deploy | Nach grüner CI auf `master`, nur bei Änderungen am Stack (E79), oder manuell | Per SSH auf den Server, Stack-Dateien setzen, `docker compose` baut die Images dort und startet die Dienste neu; Migrationen laufen beim Start; Health-Check |
| SDK-Release | Tag `sdk-vX.Y.Z` | Kern für Windows/Linux/macOS bauen, Pakete je Sprache mit eingebetteten Binaries erzeugen und veröffentlichen, Doku erzeugen |

Pfadfilter im Monorepo, damit eine Änderung am Frontend nicht alle SDK-Tests auslöst (E79, `.github/scripts/changed-areas.sh`). Die Wheels des Python-SDK baut `wheels.yml` nur bei einem Tag `v*` oder von Hand.

### Öffentliches Repo (E27)

- Workflows aus Forks bekommen keine Secrets; der Deploy-Workflow läuft nur auf `master`.
- Kein Self-hosted Runner (Pull Requests aus Forks könnten sonst Code auf dem Server ausführen).
- Domain, Serveradresse und Pfade stehen nicht im Repo.
- Die Sandbox-Konfiguration ist öffentlich einsehbar; ihre Sicherheit darf nicht von Geheimhaltung abhängen.

### Build auf dem Server (R11)

- Der erste Build ist der teuerste (C++-Kern, Frontend, fünf Laufzeiten); danach greifen die Docker-Build-Caches.
- Mehrstufige Dockerfiles, damit Compiler und Build-Werkzeuge nicht im laufenden Image landen.
- Während des Builds leidet die Zeitmessung laufender Partien: Queue vor dem Deploy pausieren, laufende Partie zu Ende spielen lassen.
- Ausweichmöglichkeit ohne Konzeptänderung: Images in GitHub Actions bauen und auf dem Server nur ziehen.

## Stand M2

Umgesetzt unter `deploy/` und `.github/workflows/deploy.yml` (E78). Es laufen `mongo`, `api`, `runner` und `frontend`; `scheduler` und das Replica Set (E75) folgen später. Seit M3 Schritt 2 startet der Runner jeden Bot in nsjail (E86, E87). Einen eigenen `verifier` gibt es nicht (E81); seit Schritt 3 verifiziert der Runner hochgeladene Bots (E89, E92).

| Datei | Inhalt |
|-------|--------|
| `deploy/compose.yaml` | Stack `sbm`: Dienste, internes Netz ohne Ausgang (API dort mit Alias `sbm-api`, Gateway mit `sbm-gateway`), Netz `relay` nur für `gateway` (Alias `sbm-relay`) und `runner-play`, `local-web` nur für `frontend` (Alias `sbm-frontend`), Volume `mongo-data`, Härtung, Log-Rotation; Profil `setup` für die Einmal-Dienste `mongo-users` und `migrate` |
| `deploy/python.Dockerfile` | Ziel `services`, Image `sbm-python` für `migrate`, `api` und `gateway`: baut die Wheels von SDK (mit Kern), Store, Runner, Gateway und API, Laufzeit ohne Compiler als Nutzer `sbm`. Ziel `runner`, Image `sbm-runner`: zusätzlich nsjail, das Laufzeitverzeichnis der Python-Bots (Python 3.14.8 mit SDK) und `sandbox/`, läuft als root mit den Rechten aus `compose.yaml` (E87) |
| `deploy/frontend.Dockerfile` | Image `sbm-frontend`: Vite-Build, ausgeliefert von nginx ohne Root auf Port 8080 |
| `deploy/nginx.conf` | SPA mit Rückfall auf `index.html`, `/api/v1/play/socket` als WebSocket an `sbm-gateway:8001` (Lese-Timeout 1 h), `/api/` an `sbm-api:8000` (Alias der API nur im internen Netz, weil `api` an `local-web` einen fremden Container treffen kann), lange Cache-Zeit nur für `/assets/`, Sicherheits-Header, Anfragen an `/api/` bis 4 MB für Uploads (E92) |
| `deploy/mongo/users.js` | Legt die Rolle `sbm_api_writes` (E85; seit E94 auch `bots` und der Bucket `bot_files`, seit E100 Anlegen und Ändern in `disciplines`, seit E105 Löschen in `bots`, `matches`, `jobs` und `verification_reports`, seit E116 Einfügen und Ändern in `api_tokens`) und die Nutzer der Dienste an oder setzt Rechte und Passwörter neu |
| `deploy/deploy.sh` | Ablauf auf dem Server, aus dem Repo-Wurzelverzeichnis; hält am Ende den ausgerollten Commit in `deploy/.deployed-commit` fest |
| `deploy/needs-deploy.sh` | Sagt, ob sich seit dem ausgerollten Commit etwas geändert hat, woraus der Stack gebaut wird (E79) |
| `deploy/.env.example` | Alle Werte der Umgebungsdatei mit Erklärung |

**Ablauf** (`deploy/deploy.sh`): Images bauen → beide Runner stoppen (laufende Partie geht an die Queue zurück, E75; interaktive Partien werden abgebrochen, E113) → `mongo` starten → `mongo-users` → `migrate` → `api`, `gateway`, `runner`, `runner-play`, `frontend` starten und auf ihre Health-Checks warten → `/api/v1/health` über das Frontend abfragen → Commit festhalten → alte Images entfernen. Nach der CI prüft der Workflow vorher mit `deploy/needs-deploy.sh`, ob sich etwas am Stack geändert hat, und überspringt sonst Umgebungsdatei und Build (E79). Während des Builds läuft der Runner weiter; wer keine Partie unterbrechen will, pausiert die Queue vorher auf der Admin-Seite.

**Einmalig auf dem Server einrichten:**

| Schritt | Detail |
|---------|--------|
| Docker | Docker Engine mit Compose-Plugin und `git`; der SSH-Nutzer ist in der Gruppe `docker` |
| Netz | `local-web` existiert bereits (Nginx Proxy Manager) |
| Proxy-Host | Im Nginx Proxy Manager: Subdomain → `sbm-frontend`, Port `8080`, Zertifikat anfordern |
| Zielordner | Das übergeordnete Verzeichnis von `DEPLOY_PATH` muss für den SSH-Nutzer beschreibbar sein; der erste Deploy klont das Repo dorthin |
| SSH | Eigener Schlüssel nur für das Deploy; öffentlicher Teil in `authorized_keys` des Nutzers |

**In GitHub anlegen** (Umgebung `production`):

| Name | Art | Inhalt |
|------|-----|--------|
| `SSH_HOST`, `SSH_USER` | Secret | Adresse und Nutzer des Servers |
| `SSH_PORT` | Secret, optional | Standard 22 |
| `SSH_PRIVATE_KEY` | Secret | Privater Deploy-Schlüssel |
| `SSH_KNOWN_HOSTS` | Secret | Ausgabe von `ssh-keyscan -p PORT HOST`, vorher mit dem Fingerabdruck des Servers abgleichen |
| `DEPLOY_PATH` | Secret | Absoluter Pfad des Repos auf dem Server, ohne Leerzeichen |
| `MONGO_ROOT_PASSWORD`, `MONGO_API_PASSWORD`, `MONGO_RUNNER_PASSWORD`, `MONGO_MIGRATE_PASSWORD` | Secret | Je mindestens 16 Buchstaben oder Ziffern, z. B. `openssl rand -hex 24` |
| `SBM_PUBLIC_URL` | Variable | Öffentliche Adresse, z. B. `https://schachbotmanager.devtgp.net` |

**Zu wissen:**

- Das Root-Passwort übernimmt MongoDB nur beim ersten Start mit leerem Volume. Für einen späteren Wechsel zuerst in der Datenbank ändern (`db.getSiblingDB("admin").changeUserPassword("root", …)` über `docker compose -f deploy/compose.yaml exec mongo mongosh -u root`), dann das Secret. Die Passwörter der Dienste wechseln mit dem nächsten Deploy, der etwas baut; nach einer Änderung der Secrets daher den Deploy von Hand starten (Actions → Deploy → „Run workflow“).
- Erster Admin (E83): nach dem ersten Deploy `docker compose -f deploy/compose.yaml run --rm api sbm-invite --role admin` aufrufen; der Befehl gibt einen Einladungslink aus, über den der Admin Namen und Passwort wählt. Weitere Nutzer lädt der Admin auf der Website ein.
- Partien setzt der Admin auf der Website an (Admin → Partien); `sbm-enqueue` im Runner-Container bleibt für Tests.
- `SBM_PROXY_HOPS` steht in `compose.yaml` fest auf 2 (Nginx Proxy Manager und der Nginx im `frontend`, E84). Steht ein weiterer Proxy davor, muss der Wert mitwachsen, sonst zählt das Login-Limit falsche Adressen.
- Logs: `docker compose -f deploy/compose.yaml logs -f runner` (ebenso `api`, `gateway`, `runner-play`, `frontend`). Beim Start meldet der Runner „sandbox nsjail ready“; scheitert die Selbstprüfung der Sandbox, beendet er sich, und Docker startet ihn neu. Dann im Log nach dem Grund sehen (etwa kein cgroup v2, fehlende Controller, Kernel vor 5.14).
- Der Runner verschiebt beim Start alle Prozesse seines Containers in die cgroup `runner/`; die Wurzel seines cgroup-Baums nimmt danach keine Prozesse mehr auf. `docker compose exec runner …` geht trotzdem, weil runc dann die cgroup des Hauptprozesses nimmt (auf dem Server geprüft: der Befehl landet in `runner/`). Für Befehle wie `sbm-enqueue` ist ohnehin `docker compose run --rm runner …` vorgesehen, das einen eigenen Container startet.
- Interaktive Partien (M7, E111): Für den Proxy-Host im Nginx Proxy Manager „Websockets Support“ einschalten, sonst kommt keine WebSocket-Verbindung zum Gateway durch. `PLAY_SLOTS` in der Umgebungsdatei ist optional (Standard 2).
- Der Stack lässt sich lokal genauso starten: Netz `local-web` anlegen, `deploy/.env.example` nach `deploy/.env` kopieren und ausfüllen, `bash deploy/deploy.sh`.

## Zu beachten

- **Laufende Spiele beim Deploy:** Runner bekommen ein Signal „keine neuen Jobs annehmen“ und beenden laufende Spiele, oder abgebrochene Spiele werden neu angesetzt (bei 60-min-Partien relevant).
- **Laufzeitverzeichnisse sind Teil der Spielregeln:** Neue Laufzeit-/SDK-Version = neue Version; alte bleiben, solange Bots darauf verifiziert sind.
- **Geteilter Server (E12):** Ressourcenobergrenzen für die eigenen Dienste setzen, damit sie andere Anwendungen nicht verdrängen; Queue-Pause und Zeitfenster über die Website.
- **Host-Voraussetzungen (Ubuntu x86-64, E26):** cgroup v2 mit den Controllern `memory` und `pids`, Linux ab 5.14. nsjail ist im `runner`-Image enthalten und läuft dort mit den Rechten des Containers (E87). Die Einschränkung unprivilegierter User-Namespaces neuerer Ubuntu-Versionen trifft den Runner nicht, weil er sie mit `SYS_ADMIN` anlegt; die CI prüft das auf `ubuntu-latest`.
- **Secrets:** Nur über GitHub-Secrets bzw. Umgebungsdateien auf dem Server, nie im Repo; getrennte DB-Nutzer je Dienst mit minimalen Rechten.
- **Backups:** Regelmäßiger Dump von MongoDB und Artefakt-Speicher, außerhalb des Hosts abgelegt, Wiederherstellung testen.
- **Migrationen:** Versionierte Skripte, vor Dienststart ausgeführt.
- **Monitoring:** Health-Endpunkte, Queue-Länge, Spieldauer, Fehlerraten nach `termination`, Auslastung der Kerne, Speicherplatz; Benachrichtigung bei hängender Queue.
- **Logs:** Strukturierte Logs der Dienste mit Rotation; Bot-Logs getrennt und mengenbegrenzt.
- **Aufräumen:** Verwaiste Sandbox-Prozesse, alte Images und Laufzeitverzeichnisse, alte Build-Artefakte abgelehnter Bots.
- **Staging:** Optional ein zweiter Stack mit eigener DB und eigener Subdomain.
- **Host-Härtung:** Aktuelle Kernel-Versionen sind wegen der Ausführung fremden Codes besonders relevant (siehe [sandbox.md](sandbox.md)).
