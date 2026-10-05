# Deployment und Betrieb

## Dienste (ein Docker-Compose-Stack, E28)

| Dienst | Netz | Besonderheit |
|--------|------|--------------|
| `frontend` | `local-web` + intern | Liefert den statischen SPA-Build aus und reicht `/api` sowie WebSocket an `api` weiter; einziger Dienst, auf den der Proxy zeigt |
| `api` | intern | Flask hinter WSGI-Server; kann keine Prozesse starten |
| `scheduler` | intern | Genau eine Instanz |
| `runner` | intern | Container mit erweiterten Rechten (A13), startet Bots über nsjail; Parallelität aus den Einstellungen in der DB |
| `verifier` | intern | Wie `runner`, nutzt dieselbe Sandbox |
| `mongo` | intern | Als Replica Set (Einzelknoten), Authentifizierung aktiv, Daten auf einem Volume |

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

Was ich dafür von dir brauche (O18), jeweils erst zu M2 und nicht im Repo:

| Angabe | Wohin |
|--------|-------|
| Subdomain | Proxy-Host im Nginx Proxy Manager; als Variable für die API (erlaubter Ursprung, Cookie-Domain) |
| SSH-Host, Port, Nutzer, privater Schlüssel | GitHub-Secrets |
| Zielpfad des Stacks auf dem Server | GitHub-Secret oder Variable |
| Geheimnisse der Anwendung (DB-Passwort, Sitzungsschlüssel, erster Admin-Invite) | Umgebungsdatei auf dem Server oder GitHub-Secrets |

## GitHub Actions

| Workflow | Auslöser | Schritte |
|----------|----------|----------|
| CI | Pull Request, Push | Lint + Tests je Paket (Backend, Frontend, Dienste, Kern, Bindings), Kernvektoren, Binding-Tests, Kreuztest über die Arena, Analyzer-Tests |
| Deploy | Push auf `main` oder manuell, nach grüner CI | Per SSH auf den Server, Stack-Dateien setzen, `docker compose` baut die Images dort und startet die Dienste neu; Migrationen laufen beim Start; Health-Check |
| SDK-Release | Tag `sdk-vX.Y.Z` | Kern für Windows/Linux/macOS bauen, Pakete je Sprache mit eingebetteten Binaries erzeugen und veröffentlichen, Doku erzeugen |

Pfadfilter im Monorepo, damit eine Änderung am Frontend nicht alle SDK-Tests auslöst.

### Öffentliches Repo (E27)

- Workflows aus Forks bekommen keine Secrets; der Deploy-Workflow läuft nur auf `main`.
- Kein Self-hosted Runner (Pull Requests aus Forks könnten sonst Code auf dem Server ausführen).
- Domain, Serveradresse und Pfade stehen nicht im Repo.
- Die Sandbox-Konfiguration ist öffentlich einsehbar; ihre Sicherheit darf nicht von Geheimhaltung abhängen.

### Build auf dem Server (R11)

- Der erste Build ist der teuerste (C++-Kern, Frontend, fünf Laufzeiten); danach greifen die Docker-Build-Caches.
- Mehrstufige Dockerfiles, damit Compiler und Build-Werkzeuge nicht im laufenden Image landen.
- Während des Builds leidet die Zeitmessung laufender Partien: Queue vor dem Deploy pausieren, laufende Partie zu Ende spielen lassen.
- Ausweichmöglichkeit ohne Konzeptänderung: Images in GitHub Actions bauen und auf dem Server nur ziehen.

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
