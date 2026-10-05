# Deployment und Betrieb

## Dienste (Docker Compose)

| Dienst | Erreichbarkeit | Besonderheit |
|--------|----------------|--------------|
| Reverse Proxy | Öffentlich (443) | TLS, liefert SPA aus, leitet `/api` und WebSocket weiter |
| `api` | Nur intern | Kein Runtime-Zugriff |
| `scheduler` | Nur intern | Genau eine Instanz |
| `runner` | Nur intern | Zugriff auf Container-Runtime; Anzahl paralleler Spiele = konfigurierte Kerne |
| `verifier` | Nur intern | Zugriff auf Container-Runtime |
| `mongo` | Nur intern | Als Replica Set (auch Einzelknoten), Authentifizierung aktiv |
| Sandbox-Images | – | Werden nicht als Dienst gestartet, nur vom Runner/Verifier instanziiert |

Getrennte Docker-Netze: öffentliches Netz (Proxy ↔ API) und internes Netz (API/Scheduler/Runner/Verifier ↔ Mongo). Bot-Container hängen an keinem Netz.

## GitHub Actions

| Workflow | Auslöser | Schritte |
|----------|----------|----------|
| CI | Pull Request, Push | Lint + Tests je Paket (Backend, Frontend, Services, 5 SDKs), Konformitätsvektoren je SDK, Kreuztest der SDKs über die Arena, Analyzer-Tests |
| Build | Push auf `main` / Tag | Images bauen (API, Scheduler, Runner, Verifier, Sandbox-Images je Sprache, Frontend-Build), in Registry (z. B. GHCR) pushen, mit Commit-SHA taggen |
| Deploy | Nach erfolgreichem Build oder manuell | Auf dem Server neue Images ziehen, DB-Migrationen ausführen, Dienste aktualisieren, Health-Check, bei Fehler auf vorigen Tag zurück |
| SDK-Release | Tag `sdk-vX.Y.Z` | Pakete veröffentlichen, Doku erzeugen |

Pfadfilter im Monorepo, damit eine Änderung am Frontend nicht alle SDK-Tests auslöst.

### Wege auf den Server

| Variante | Eigenschaft |
|----------|-------------|
| SSH aus dem Workflow | Einfach; Server muss per SSH von GitHub erreichbar sein, Deploy-Key mit minimalen Rechten nötig |
| Self-hosted Runner auf dem Server | Kein eingehender Zugriff nötig; der Runner führt Repo-Code auf dem Server aus → nur für vertrauenswürdige Branches, nicht für Pull Requests aus Forks |
| Pull-basiert (Server prüft Registry auf neue Tags) | Kein Zugriff von außen; weniger direkte Kontrolle über den Ablauf |

## Zu beachten

- **Laufende Spiele beim Deploy:** Runner bekommen ein Signal „keine neuen Jobs annehmen“ und beenden laufende Spiele, oder abgebrochene Spiele werden neu angesetzt (bei 60-min-Partien relevant).
- **Sandbox-Images sind Teil der Spielregeln:** Neue Laufzeit-/SDK-Version = neuer Tag; alte Tags bleiben, solange Bots darauf verifiziert sind.
- **Secrets:** Nur über GitHub-Secrets bzw. Umgebungsdateien auf dem Server, nie im Repo; getrennte DB-Nutzer je Dienst mit minimalen Rechten.
- **Backups:** Regelmäßiger Dump von MongoDB und Artefakt-Speicher, außerhalb des Hosts abgelegt, Wiederherstellung testen.
- **Migrationen:** Versionierte Skripte, vor Dienststart ausgeführt.
- **Monitoring:** Health-Endpunkte, Queue-Länge, Spieldauer, Fehlerraten nach `termination`, Auslastung der Kerne, Speicherplatz; Benachrichtigung bei hängender Queue.
- **Logs:** Strukturierte Logs der Dienste mit Rotation; Bot-Logs getrennt und mengenbegrenzt.
- **Aufräumen:** Verwaiste Container, alte Images, alte Build-Artefakte abgelehnter Bots.
- **Staging:** Zweite Compose-Umgebung (eigene DB, eigener Port) zum Testen von Deployments und Migrationen.
- **Host-Härtung:** Aktuelle Kernel-/Runtime-Versionen sind wegen der Ausführung fremden Codes besonders relevant (siehe [sandbox.md](sandbox.md)).
