# Deployment und Betrieb

## Dienste (ein Docker-Compose-Stack, E28)

| Dienst | Netz | Besonderheit |
|--------|------|--------------|
| `frontend` | `local-web` + intern | Liefert den statischen SPA-Build aus und reicht `/api` sowie WebSocket an `api` weiter; einziger Dienst, auf den der Proxy zeigt |
| `api` | intern | Flask hinter WSGI-Server; kann keine Prozesse starten |
| `scheduler` | intern | Genau eine Instanz |
| `runner` | intern | Container mit erweiterten Rechten (A13), startet Bots über nsjail; Parallelität aus den Einstellungen in der DB |
| `verifier` | intern | Wie `runner`, nutzt dieselbe Sandbox |
| `mongo` | intern | Als Replica Set (Einzelknoten, ab M4, E75), Authentifizierung aktiv, Daten auf einem Volume |

Bot-Prozesse haben kein Netzwerk. Laufzeiten der fünf Sprachen, SDK und C++-Kern sind Teil des `runner`/`verifier`-Images und werden von dort read-only in die Sandbox eingehängt.

## Einbindung in den bestehenden Proxy (E29)

| Punkt | Umsetzung |
|-------|-----------|
| Netz | `local-web` wird im Compose-File als externes Netz eingebunden; nur `frontend` hängt daran |
| Proxy-Host | Im Nginx Proxy Manager: Subdomain → `frontend`, Port des Containers; einmalig von Hand anzulegen |
| TLS | Zertifikat über den Nginx Proxy Manager |
| WebSocket | Im Proxy-Host aktivieren (nötig für Live-Partien, Mensch gegen Bot, Remote-Bots) |
| Zeitlimits | Lange Verbindungen: Lese-Timeout des Proxys für WebSockets hochsetzen |
| Upload-Größe | Maximale Request-Größe im Proxy passend zum Upload-Limit |
| Echte Client-IP | Weitergereichte IP-Header nur vom Proxy akzeptieren (für Rate-Limits pro IP) |
| Ports | Der Stack veröffentlicht keine Ports auf dem Host |

Welche Angaben wohin gehören, steht unter „Stand M2“ (O18).

## GitHub Actions

| Workflow | Auslöser | Schritte |
|----------|----------|----------|
| CI | Pull Request, Push | Lint + Tests je Paket (Backend, Frontend, Dienste, Kern, Bindings), Kernvektoren, Binding-Tests, Kreuztest über die Arena, Analyzer-Tests |
| Deploy | Push auf `master` oder manuell, nach grüner CI | Per SSH auf den Server, Stack-Dateien setzen, `docker compose` baut die Images dort und startet die Dienste neu; Migrationen laufen beim Start; Health-Check |
| SDK-Release | Tag `sdk-vX.Y.Z` | Kern für Windows/Linux/macOS bauen, Pakete je Sprache mit eingebetteten Binaries erzeugen und veröffentlichen, Doku erzeugen |

Pfadfilter im Monorepo, damit eine Änderung am Frontend nicht alle SDK-Tests auslöst.

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

Umgesetzt unter `deploy/` und `.github/workflows/deploy.yml` (E78). In M2 laufen nur `mongo`, `api`, `runner` und `frontend`; `scheduler`, `verifier`, nsjail (E72) und das Replica Set (E75) folgen später.

| Datei | Inhalt |
|-------|--------|
| `deploy/compose.yaml` | Stack `sbm`: Dienste, internes Netz ohne Ausgang, `local-web` nur für `frontend` (Alias `sbm-frontend`), Volume `mongo-data`, Härtung, Log-Rotation; Profil `setup` für die Einmal-Dienste `mongo-users` und `migrate` |
| `deploy/python.Dockerfile` | Image `sbm-python` für `migrate`, `api`, `runner`: baut die Wheels von SDK (mit Kern), Store, Runner und API, Laufzeit ohne Compiler als Nutzer `sbm` |
| `deploy/frontend.Dockerfile` | Image `sbm-frontend`: Vite-Build, ausgeliefert von nginx ohne Root auf Port 8080 |
| `deploy/nginx.conf` | SPA mit Rückfall auf `index.html`, `/api/` an `api:8000`, lange Cache-Zeit nur für `/assets/`, Sicherheits-Header |
| `deploy/mongo/users.js` | Legt die Nutzer der Dienste an oder setzt ihre Passwörter neu |
| `deploy/deploy.sh` | Ablauf auf dem Server, aus dem Repo-Wurzelverzeichnis |
| `deploy/.env.example` | Alle Werte der Umgebungsdatei mit Erklärung |

**Ablauf** (`deploy/deploy.sh`): Images bauen → Runner stoppen (laufende Partie geht an die Queue zurück, E75) → `mongo` starten → `mongo-users` → `migrate` → `api`, `runner`, `frontend` starten und auf ihre Health-Checks warten → `/api/v1/health` über das Frontend abfragen → alte Images entfernen. Während des Builds läuft der Runner weiter; das Pausieren der Queue vor dem Deploy kommt mit der Admin-Oberfläche (M3).

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

- Das Root-Passwort übernimmt MongoDB nur beim ersten Start mit leerem Volume. Für einen späteren Wechsel zuerst in der Datenbank ändern (`db.getSiblingDB("admin").changeUserPassword("root", …)` über `docker compose -f deploy/compose.yaml exec mongo mongosh -u root`), dann das Secret. Die Passwörter der Dienste wechseln mit dem nächsten Deploy.
- Partien ansetzen bis zur Admin-Oberfläche (M3): `docker compose -f deploy/compose.yaml run --rm runner sbm-enqueue Random Material --time 60+1 --games 2 --alternate`.
- Logs: `docker compose -f deploy/compose.yaml logs -f runner` (ebenso `api`, `frontend`).
- Der Stack lässt sich lokal genauso starten: Netz `local-web` anlegen, `deploy/.env.example` nach `deploy/.env` kopieren und ausfüllen, `bash deploy/deploy.sh`.

## Zu beachten

- **Laufende Spiele beim Deploy:** Runner bekommen ein Signal „keine neuen Jobs annehmen“ und beenden laufende Spiele, oder abgebrochene Spiele werden neu angesetzt (bei 60-min-Partien relevant).
- **Laufzeitverzeichnisse sind Teil der Spielregeln:** Neue Laufzeit-/SDK-Version = neue Version; alte bleiben, solange Bots darauf verifiziert sind.
- **Geteilter Server (E12):** Ressourcenobergrenzen für die eigenen Dienste setzen, damit sie andere Anwendungen nicht verdrängen; Queue-Pause und Zeitfenster über die Website.
- **Host-Voraussetzungen (Ubuntu x86-64, E26):** cgroup v2 aktiv. nsjail ist im `runner`-Image enthalten und läuft dort mit den Rechten des Containers; die Einschränkung unprivilegierter User-Namespaces neuerer Ubuntu-Versionen ist bei der Einrichtung zu prüfen.
- **Secrets:** Nur über GitHub-Secrets bzw. Umgebungsdateien auf dem Server, nie im Repo; getrennte DB-Nutzer je Dienst mit minimalen Rechten.
- **Backups:** Regelmäßiger Dump von MongoDB und Artefakt-Speicher, außerhalb des Hosts abgelegt, Wiederherstellung testen.
- **Migrationen:** Versionierte Skripte, vor Dienststart ausgeführt.
- **Monitoring:** Health-Endpunkte, Queue-Länge, Spieldauer, Fehlerraten nach `termination`, Auslastung der Kerne, Speicherplatz; Benachrichtigung bei hängender Queue.
- **Logs:** Strukturierte Logs der Dienste mit Rotation; Bot-Logs getrennt und mengenbegrenzt.
- **Aufräumen:** Verwaiste Sandbox-Prozesse, alte Images und Laufzeitverzeichnisse, alte Build-Artefakte abgelehnter Bots.
- **Staging:** Optional ein zweiter Stack mit eigener DB und eigener Subdomain.
- **Host-Härtung:** Aktuelle Kernel-Versionen sind wegen der Ausführung fremden Codes besonders relevant (siehe [sandbox.md](sandbox.md)).
