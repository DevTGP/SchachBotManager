# Backend (Flask-API)

Reine API (E5). Liefert kein HTML, führt keinen Bot-Code aus und kann keine Sandbox-Prozesse starten.

## Aufbau

| Blueprint | Aufgabe |
|-----------|---------|
| `auth` | Login, Logout, Invite einlösen, Passwort ändern, eigene API-Tokens |
| `bots` | Upload, Liste, Detail, Metadaten ändern, deaktivieren, neue Version anlegen, Report abrufen |
| `matches` | Liste/Filter, Detail (inkl. Züge), PGN-Export, laufende Spiele |
| `leagues` | Ligen, Saisons, Tabellen, Spielpläne |
| `tournaments` | Turniere, Runden, Bracket |
| `registrations` | Bot an-/abmelden |
| `play` | Mensch gegen Bot: Spiel anlegen, Zug senden, aufgeben |
| `remote` | Lokaler Bot gegen Server: Spiel anlegen, WebSocket-Endpunkt |
| `queue` | Öffentliche Sicht auf wartende Spiele mit geschätzten Startzeiten |
| `admin` | Nutzer, Invites, Disziplinen, Ligen, Turniere, Bots, Queue (pausieren, umsortieren, Parallelität), Systemeinstellungen, Audit-Log |
| `live` | WebSocket/SSE für Live-Updates |

Schichtung: Routen → Services (Geschäftslogik) → Repositories (MongoDB). Validierung aller Eingaben über Schemas; OpenAPI-Beschreibung als Vertrag für die SPA.

## Rollen und Rechte

| Rolle | Darf |
|-------|------|
| Gast | Alles lesen: Partien, Tabellen, Bot-Profile, Queue (E10); gegen Bots spielen (E11). Kein Zugriff auf Quellcode, Reports, Logs |
| Coder | Eigene Bots hochladen, bearbeiten (Metadaten), an-/abmelden, eigene Reports/Logs sehen, Einzelspiele eigener Bots ansetzen, API-Tokens verwalten |
| Admin | Alles: Nutzer/Invites, sämtliche Bots, Disziplinen, Ligen, Turniere, Jobs, Neuprüfungen, Overrides |

Jede Route prüft Rolle **und** Besitz (eigene Ressource vs. fremde).

## Authentifizierung

| Client | Verfahren |
|--------|-----------|
| SPA | Server-Session per HttpOnly-/Secure-/SameSite-Cookie, CSRF-Schutz für schreibende Requests |
| Lokaler Bot | Persönliches API-Token (nur gehasht gespeichert, widerrufbar, eingeschränkt auf `remote`-Endpunkte) |

- Invite: einmalig, mit Ablaufdatum, legt Rolle fest; nur der Hash wird gespeichert.
- Passwörter mit Argon2 oder bcrypt; Rate-Limit und Sperre nach Fehlversuchen.
- Passwort-Reset ohne Mailversand: durch Admin ausgelöster Einmal-Link (Mailversand optional später).

## Live-Kanal

| Option | Eigenschaft |
|--------|-------------|
| WebSocket (z. B. Flask-SocketIO) | Bidirektional; nötig für Mensch-gegen-Bot und Remote-Bots; braucht asynchronen Worker-Typ |
| Server-Sent Events | Einfach, nur Server → Client; reicht für Zuschauen und Tabellen |

Quelle der Ereignisse (Runner → API):

| Option | Eigenschaft |
|--------|-------------|
| MongoDB Change Streams | Keine Zusatzkomponente; erfordert Replica Set |
| Pub/Sub-Broker (z. B. Redis) | Zusätzlicher Dienst; entkoppelt, geringe Latenz |
| Polling der DB | Einfachste Variante, höhere Latenz und Last |

Züge von Menschen/Remote-Bots nehmen den umgekehrten Weg: API schreibt den Zug als Ereignis für den Runner, der ihn wie jeden anderen prüft.

## Upload

- Größen- und Typprüfung vor dem Speichern, Streaming statt Laden in den Speicher.
- Archive werden nie von der API entpackt, sondern erst im Verifier in der Sandbox.
- Upload erzeugt `bot` + `verify`-Job; Antwort enthält die Bot-ID zur Statusabfrage.

## Zu beachten

- **Paginierung und Filter** für alle Listen (Partien wachsen unbegrenzt).
- **Rate-Limits** pro Nutzer/IP für Login, Upload, Spielstart.
- **Kapazitätsgrenzen** für Mensch-/Remote-Spiele (gleichzeitig pro IP/Nutzer und gesamt), über die Website einstellbar.
- **Gast-Spiele ohne Account:** Zuordnung über ein anonymes Sitzungs-Cookie; Rate-Limit pro IP.
- **Quellcode-Download** nur für Besitzer und Admin (E15).
- **Einstellungen (E13):** Jede Konfiguration hat einen validierten API-Endpunkt mit Obergrenzen; Änderungen landen im Audit-Log und wirken ohne Neustart.
- **Fehlerformat** einheitlich (Code, Feldfehler); Texte übersetzt das Frontend (E32).
- **Hinter dem Proxy:** Client-IP nur aus den Headern des Nginx Proxy Manager übernehmen; Cookies als sicher markieren, obwohl die API intern unverschlüsselt angesprochen wird.
- **Audit-Log** für alle Admin-Aktionen und Statuswechsel von Bots.
- **Betrieb:** WSGI-Server (z. B. gunicorn) hinter dem Reverse Proxy; der Flask-Entwicklungsserver ist nicht für Produktion gedacht.
- **Tests:** Unit-Tests der Services, API-Tests gegen eine Test-MongoDB, Rechte-Matrix als eigener Testblock.
