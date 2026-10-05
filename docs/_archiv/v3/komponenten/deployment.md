# Deployment und Betrieb

## Dienste

| Dienst | Erreichbarkeit | Besonderheit |
|--------|----------------|--------------|
| Reverse Proxy | Öffentlich (443) | TLS, liefert SPA aus, leitet `/api` und WebSocket weiter |
| `api` | Nur intern | Kein Runtime-Zugriff |
| `scheduler` | Nur intern | Genau eine Instanz |
| `runner` | Nur intern | systemd-Dienst direkt auf dem Host (A13), startet Bots über nsjail; Parallelität aus den Einstellungen in der DB |
| `verifier` | Nur intern | systemd-Dienst direkt auf dem Host, nutzt dieselbe Sandbox |
| `mongo` | Nur intern | Als Replica Set (auch Einzelknoten), Authentifizierung aktiv |
| Laufzeitverzeichnisse | – | Versionierte Verzeichnisse je Sprache auf dem Host, read-only in die Sandbox eingehängt |

Proxy, `api`, `scheduler` und `mongo` laufen über Docker Compose; Runner und Verifier daneben auf dem Host und erreichen MongoDB über einen nur lokal gebundenen Port. Bot-Prozesse haben kein Netzwerk.

## GitHub Actions

| Workflow | Auslöser | Schritte |
|----------|----------|----------|
| CI | Pull Request, Push | Lint + Tests je Paket (Backend, Frontend, Services, 5 SDKs), Konformitätsvektoren je SDK, Kreuztest der SDKs über die Arena, Analyzer-Tests |
| Build | Push auf `main` / Tag | Images bauen (API, Scheduler, Frontend-Build) und in die Registry pushen; Runner/Verifier als Paket, C++-Kern und Laufzeitverzeichnisse je Sprache als versionierte Archive; alles mit Commit-SHA getaggt |
| Deploy | Nach erfolgreichem Build oder manuell | Auf dem Server neue Images und Archive holen, DB-Migrationen ausführen, Compose-Dienste und systemd-Dienste aktualisieren, Health-Check, bei Fehler auf vorigen Tag zurück |
| SDK-Release | Tag `sdk-vX.Y.Z` | Kern für Windows/Linux/macOS bauen, Pakete je Sprache mit eingebetteten Binaries erzeugen und veröffentlichen, Doku erzeugen |

Pfadfilter im Monorepo, damit eine Änderung am Frontend nicht alle SDK-Tests auslöst.

### Wege auf den Server

| Variante | Eigenschaft |
|----------|-------------|
| SSH aus dem Workflow | Einfach; Server muss per SSH von GitHub erreichbar sein, Deploy-Key mit minimalen Rechten nötig |
| Self-hosted Runner auf dem Server | Kein eingehender Zugriff nötig; der Runner führt Repo-Code auf dem Server aus → nur für vertrauenswürdige Branches, nicht für Pull Requests aus Forks |
| Pull-basiert (Server prüft Registry auf neue Tags) | Kein Zugriff von außen; weniger direkte Kontrolle über den Ablauf |

## Zu beachten

- **Laufende Spiele beim Deploy:** Runner bekommen ein Signal „keine neuen Jobs annehmen“ und beenden laufende Spiele, oder abgebrochene Spiele werden neu angesetzt (bei 60-min-Partien relevant).
- **Laufzeitverzeichnisse sind Teil der Spielregeln:** Neue Laufzeit-/SDK-Version = neue Version; alte bleiben, solange Bots darauf verifiziert sind.
- **Geteilter Server (E12):** Ressourcenobergrenzen für die eigenen Dienste setzen, damit sie andere Anwendungen nicht verdrängen; Queue-Pause und Zeitfenster über die Website.
- **Host-Voraussetzungen:** cgroup v2, User-Namespaces, nsjail installiert; delegierte cgroup für den Runner-Nutzer.
- **Secrets:** Nur über GitHub-Secrets bzw. Umgebungsdateien auf dem Server, nie im Repo; getrennte DB-Nutzer je Dienst mit minimalen Rechten.
- **Backups:** Regelmäßiger Dump von MongoDB und Artefakt-Speicher, außerhalb des Hosts abgelegt, Wiederherstellung testen.
- **Migrationen:** Versionierte Skripte, vor Dienststart ausgeführt.
- **Monitoring:** Health-Endpunkte, Queue-Länge, Spieldauer, Fehlerraten nach `termination`, Auslastung der Kerne, Speicherplatz; Benachrichtigung bei hängender Queue.
- **Logs:** Strukturierte Logs der Dienste mit Rotation; Bot-Logs getrennt und mengenbegrenzt.
- **Aufräumen:** Verwaiste Sandbox-Prozesse, alte Images und Laufzeitverzeichnisse, alte Build-Artefakte abgelehnter Bots.
- **Staging:** Zweite Compose-Umgebung (eigene DB, eigener Port) zum Testen von Deployments und Migrationen.
- **Host-Härtung:** Aktuelle Kernel-Versionen sind wegen der Ausführung fremden Codes besonders relevant (siehe [sandbox.md](sandbox.md)).
