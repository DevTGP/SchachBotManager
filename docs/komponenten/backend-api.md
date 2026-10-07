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

### Stand M2 (E73, E76)

Umgesetzt ist nur der lesende Teil ohne Login, als Paket `sbm-api` unter `backend/` (Modul `sbm_api`, gunicorn lädt `sbm_api.wsgi:app`). Vertrag: `spec/web/openapi.json`, Präfix `/api/v1`.

| Datei | Aufgabe |
|-------|---------|
| `app.py` | `create_app(db, now, public_url)`; ohne `db` aus `SBM_MONGO_URI`/`SBM_MONGO_DB` |
| `routes/*.py` | Je ein Blueprint für `health`, `matches`, `bots`, `queue` |
| `params.py` | Prüfung von IDs, Status, `limit`, `offset` |
| `errors.py` | Fehlerformat und Fehlerbehandlung |
| `match_view.py`, `bot_view.py`, `timestamps.py` | Ausgabeform der Dokumente; Zeiten als RFC 3339 mit Millisekunden |
| `pgn.py` | PGN-Export im Format der Arena |
| `queue_view.py`, `queue_estimate.py` | Queue mit geschätzten Start- und Endzeiten (E20) |

Die API liest nur über `sbm-store` (E75). Statt Repositories und Services gibt es vorerst nur Routen und Ausgabefunktionen; die Schichtung oben entsteht mit den schreibenden Routen in M3. Die Tests prüfen jede Antwort mit openapi-core gegen den Vertrag.

### Stand M3, Schritt 1 (E83–E85)

Dazu kommen Anmeldung, Konten und die Admin-Routen. Alle ändernden Anfragen brauchen den Header `X-SBM-CSRF: 1` (E84).

| Route | Aufgabe |
|-------|---------|
| `GET/POST/DELETE /session` | Wer angemeldet ist (`user` oder `null`), Anmelden, Abmelden |
| `POST /invites/redeem` | Einladung einlösen: Konto anlegen und anmelden |
| `POST /password-resets/redeem` | Neues Passwort über den Link des Admins, beendet alle Sitzungen |
| `PUT /account/password` | Eigenes Passwort ändern, beendet die anderen Sitzungen |
| `GET /admin/users`, `PATCH /admin/users/{id}` | Nutzer auflisten, Rolle oder Aktiv-Status ändern |
| `POST /admin/users/{id}/password-reset` | Einmal-Link für ein neues Passwort |
| `GET/POST /admin/invites`, `DELETE /admin/invites/{id}` | Offene Einladungen, neue Einladung, Einladung zurückziehen |
| `POST /admin/matches` | Partien zwischen zwei geprüften Bots einreihen |
| `PATCH /admin/queue` | Queue pausieren oder fortsetzen |

| Datei | Aufgabe |
|-------|---------|
| `routes/session.py`, `routes/invites.py`, `routes/password_resets.py`, `routes/account.py` | Anmeldung und eigenes Konto |
| `routes/admin_*.py` | Je ein Blueprint für Nutzer, Einladungen, Partien und Queue |
| `current_user.py` | Konto zur Sitzung, einmal je Anfrage geladen; `require_user`, `require_admin`; Verlängerung der Sitzung |
| `session_cookie.py`, `csrf.py` | Cookie `sbm_session` und Header-Prüfung |
| `login.py`, `passwords.py`, `rate_limit.py` | Anmeldung mit Sperre, argon2id, Limit je Client-Adresse |
| `account_rules.py`, `body.py` | Prüfung von Namen, Passwörtern, Tokens und JSON-Bodys |
| `enqueue_request.py` | Body von `POST /admin/matches`, geprüft wie im Referee |
| `links.py`, `user_view.py`, `invite_view.py` | Einmal-Links und Ausgabeform von Konten und Einladungen |
| `admin_audit.py` | Eintrag im `audit_log` für jede Admin-Aktion |
| `invite_cli.py` | Befehl `sbm-invite` für die erste Einladung |

Die API schreibt nur über `sbm-store` und mit der MongoDB-Rolle `sbm_api_writes` (E85). Die Tests decken die Rechte-Matrix ab (jede Admin-Route mit Gast und Coder).

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

- Konto aus Nutzername und Passwort, ohne E-Mail (E83).
- Invite: einmalig, mit Ablaufdatum, legt Rolle fest; nur der Hash wird gespeichert (E83).
- Passwörter mit argon2id; Rate-Limit je Client-Adresse und Sperre nach fünf Fehlversuchen (E84).
- Passwort-Reset ohne Mailversand: durch Admin ausgelöster Einmal-Link (E83).
- CSRF-Schutz über den Header `X-SBM-CSRF: 1` bei jeder ändernden Anfrage (E84).

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
- Archive werden nie von der API entpackt, sondern erst bei der Verifikation im Runner in der Sandbox (E81); die Dateien liegen in GridFS (E82).
- Upload erzeugt `bot` + `verify`-Job; Antwort enthält die Bot-ID zur Statusabfrage.

## Zu beachten

- **Paginierung und Filter** für alle Listen (Partien wachsen unbegrenzt).
- **Rate-Limits** pro Nutzer/IP für Login, Upload, Spielstart.
- **Kapazitätsgrenzen** für Mensch-/Remote-Spiele (gleichzeitig pro IP/Nutzer und gesamt), über die Website einstellbar.
- **Gast-Spiele ohne Account:** Zuordnung über ein anonymes Sitzungs-Cookie; Rate-Limit pro IP.
- **Quellcode-Download** nur für Besitzer und Admin (E15).
- **Einstellungen (E13):** Jede Konfiguration hat einen validierten API-Endpunkt mit Obergrenzen; Änderungen landen im Audit-Log und wirken ohne Neustart.
- **Fehlerformat** einheitlich (Code, Feldfehler); Texte übersetzt das Frontend (E32).
- **Hinter dem Proxy:** Client-IP nur aus `X-Forwarded-For` mit der Zahl der Proxys aus `SBM_PROXY_HOPS` übernehmen; Cookies als sicher markieren, sobald `SBM_PUBLIC_URL` mit `https` beginnt, obwohl die API intern unverschlüsselt angesprochen wird (E84).
- **Audit-Log** für alle Admin-Aktionen und Statuswechsel von Bots.
- **Betrieb:** WSGI-Server (z. B. gunicorn) hinter dem Reverse Proxy; der Flask-Entwicklungsserver ist nicht für Produktion gedacht.
- **Tests:** Unit-Tests der Services, API-Tests gegen eine Test-MongoDB, Rechte-Matrix als eigener Testblock.
