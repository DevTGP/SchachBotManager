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
| `remote` | Lokaler Bot gegen Server: Spiel anlegen; die WebSocket-Verbindung endet am Gateway, nicht an der API (E112) |
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
| `GET /account/rating` | Eigenes Rating (`value`, `games`) aus gewerteten Partien gegen Bots; nur für den Inhaber, jede Rolle (E117) |
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

### Stand M3, Schritt 3 (E91–E94)

Upload und Bot-Seite für Python:

| Route | Aufgabe |
|-------|---------|
| `POST /bots` | Upload als `multipart/form-data`, angemeldet und mit CSRF-Header; legt Dateien, Bot (`uploaded`) und Verifikationsjob an, Antwort 201 mit dem Bot |
| `GET /bots/{id}` | Ein Bot; Besitzer und Admins bekommen in `details` zusätzlich Dateiliste und Report, andere sehen nur Bots in `verified` und `disabled` |
| `GET /account/bots` | Alle eigenen Bots in jedem Status, neueste zuerst |
| `PATCH /admin/bots/{id}` | Bot sperren oder wieder freigeben (`verified` ↔ `disabled`, E93), mit Audit-Eintrag `bot.update` |

| Datei | Aufgabe |
|-------|---------|
| `upload_request.py` | Felder und Dateien des Uploads, Größe der Anfrage, Regeln aus `sbm.analysis.upload` |
| `routes/bots.py`, `routes/account_bots.py`, `routes/admin_bots.py` | Upload und Detail, eigene Bots, Sperre |
| `bot_view.py`, `report_view.py` | Ausgabeform von Bot, Dateien und Report |

Neue Fehlercodes: `invalid_upload` (400, mit `path` der betroffenen Datei), `too_large` (413, über 3 MiB), `name_taken` und `upload_conflict` (409). Gültige Uploads zählen je Konto unter `upload:{user_id}`, höchstens 20 am Tag (429 `too_many_attempts`). Die API prüft nur Form und Grenzen, den Inhalt nie; sie startet keine Prozesse (E81).

### Stand M3, Schritt 4 (E95–E98)

„Mein Bereich“, Versionen, Quellcode und Partien durch Coder:

| Route | Aufgabe |
|-------|---------|
| `GET /bots/{id}` | Zusätzlich `description` und `versions` (alle Versionen des Namens, die der Betrachter sehen darf, neueste zuerst); öffentlich sind jetzt `verified`, `disabled` und `retired` (E96) |
| `POST /bots` | Optionales Feld `description` (E95) |
| `PATCH /bots/{id}` | Nur der Besitzer: `description` ändern und/oder `status` zwischen `verified` und `retired` schalten (E95, E96); andere Übergänge ergeben 400 `invalid_parameter` mit `field` `status` |
| `GET /bots/{id}/file?path=…` | Eine Datei als Download, nur Besitzer und Admins (E97) |
| `GET /bots/{id}/source` | Alle Dateien als ZIP `Name-Version.zip`, nur Besitzer und Admins (E97) |
| `POST /matches` | Partien eines eigenen `verified` Bots gegen jeden `verified` Bot: 1–10 Partien, bis 5 min + 5 s, Priorität 50; 20 Partien je Konto und Tag unter `matches:{user_id}` (E98) |
| `PATCH /admin/bots/{id}` | Sperrt jetzt auch `retired` Bots; Freigeben setzt `verified` (E96) |

| Datei | Aufgabe |
|-------|---------|
| `bot_access.py` | Sichtbarkeit, Besitz und Zugriff auf Dateien eines Bots |
| `bot_description.py` | Prüfung der Beschreibung (reiner Text, 500 Zeichen) |
| `routes/own_bot.py` | `PATCH /bots/{id}` |
| `routes/bot_source.py` | Datei und ZIP; immer `Content-Disposition: attachment`, `nosniff` und `no-store` |
| `routes/own_matches.py`, `own_match_request.py` | `POST /matches` mit den Grenzen für Coder |

Partien halten zu jeder Seite `version` (bei älteren Partien `null`). Eine Anfrage über dem Tageslimit zählt nicht.

### Stand M4, Schritt 1 (E100)

| Route | Aufgabe |
|-------|---------|
| `GET /disciplines`, `GET /disciplines/{id}` | Öffentlich: alle Disziplinen nach Name, archivierte eingeschlossen |
| `POST /admin/disciplines` | Disziplin anlegen; Audit `discipline.create` |
| `PATCH /admin/disciplines/{id}` | Felder ändern, archivieren oder wiederherstellen; Audit `discipline.update` |
| `POST /admin/matches`, `POST /matches` | Optional `discipline_id`; dann sind `initial_time_ms`, `increment_ms` und `max_moves` nicht erlaubt. Unbekannte oder archivierte Disziplinen ergeben 400 mit `field` `discipline_id` |

Ein vergebener Name ergibt 409 `name_taken` mit `field` `name`. Zusammenfassungen und Details von Partien enthalten `rated`, der Schnappschuss `discipline_id`.

| Datei | Aufgabe |
|-------|---------|
| `discipline_request.py` | Prüfung der Bodies und der in einer Partie gewählten Disziplin |
| `discipline_view.py` | Darstellung einer Disziplin |
| `routes/disciplines.py`, `routes/admin_disciplines.py` | Öffentliche und Admin-Routen |

### Stand M4, Schritt 2 (E103, E104)

| Route | Aufgabe |
|-------|---------|
| `GET /ratings` | Öffentlich: Bots mit mindestens einer verbuchten Partie, höchstes Rating zuerst, dann nach Name und Version (`routes/ratings.py`) |
| `GET /ratings/players` | Öffentlich: aktive Konten mit mindestens einer verbuchten Partie gegen Bots, nur `username` und `rating`, höchstes Rating zuerst, dann nach Namen (`routes/ratings.py`, E118) |

Jeder Bot enthält `rating` mit `value` und `games` (ohne verbuchte Partie 2500 und 0). Jede Seite einer Partie enthält `rating` mit `before` und `after`, solange die Partie nicht verbucht ist `null`.

### Endgültiges Löschen (E105)

| Route | Aufgabe |
|-------|---------|
| `DELETE /admin/bots/{id}` | Löscht die Version mit Dateien, Prüfbericht und allen ihren Partien (`routes/admin_bots.py`, `sbm_store.bot_deletion`); 204. Audit `bot.delete` mit Name, Version und Zahl der Partien. 409 `builtin_bot`, `bot_verifying` oder `bot_playing`, wenn sie nicht gelöscht werden darf |

### Stand M7 (E113–E119)

| Datei | Aufgabe |
|-------|---------|
| `routes/play.py`, `play_request.py` | `POST /play`: Partie eines Gastes oder Kontos gegen einen geprüften Bot (E114) |
| `routes/remote.py`, `remote_request.py`, `token_auth.py` | `POST /remote/matches` mit API-Token; Gegner und Disziplin per Name (E116) |
| `play_limits.py`, `play_view.py` | Plätze gesamt, gleichzeitige und tägliche Partien je Adresse (als Hash), Konto und Token; Antwort mit Sitz-Token und `socket_path` (E115) |
| `routes/admin_play.py` | `GET`/`PUT /admin/play-settings`, Audit `play.settings` |
| `routes/account_rating.py` | `GET /account/rating` (E117) |
| `routes/ratings.py` | zusätzlich `GET /ratings/players`, die Rangliste der Spieler (E118) |
| `routes/account_tokens.py`, `token_view.py` | `GET`/`POST /account/tokens`, `DELETE /account/tokens/{id}` für Coder (E116) |

- Partien der Typen `human` und `remote` sind öffentlich wie Botpartien: Liste, Detail, PGN (E119, vorher E115). `GET /matches?kind=bots` liefert nur Botpartien (`single`), `kind=players` nur die mit Spielern; ohne `kind` alle (`routes/matches.py`). Eine Seite ohne Bot zeigt `kind`, `bot_id` `null` und den Namen (Nutzername oder `Guest`); `match_view.side` gibt Konto, Sitz-Hash und Herkunft nie heraus.
- `GET /queue` hängt laufende interaktive Partien mit geschätztem Ende an `running` an (`queue_view.py`, `sbm_store.play.running_summaries`); sie belegen keinen Platz der Queue und ändern deren Schätzung nicht (E119).
- `require_coder` schützt Upload, eigene Bots, eigene Partien und Tokens; die Rolle `player` bekommt dort 403.
- Neue Fehlercodes: `no_capacity` (503), `too_many_games` (429).

## Rollen und Rechte

| Rolle | Darf |
|-------|------|
| Gast | Alles lesen: Partien, Tabellen, Bot-Profile, Queue (E10); gegen Bots spielen (E11). Kein Zugriff auf Quellcode, Reports, Logs |
| Spieler (ab M7, E103, E115) | Angemeldet gegen Bots spielen (gewertet mit Disziplin, eigenes Rating auf der Kontoseite und in der Rangliste, E117, E118); sonst wie Gast, ohne eigene Bots und Tokens |
| Coder | Eigene Bots hochladen, bearbeiten (Metadaten), an-/abmelden, eigene Reports/Logs sehen, Einzelspiele eigener Bots ansetzen, API-Tokens verwalten |
| Admin | Alles: Nutzer/Invites, sämtliche Bots, Disziplinen, Ligen, Turniere, Jobs, Neuprüfungen, Overrides |

Jede Route prüft Rolle **und** Besitz (eigene Ressource vs. fremde).

## Authentifizierung

| Client | Verfahren |
|--------|-----------|
| SPA | Server-Session per HttpOnly-/Secure-/SameSite-Cookie, CSRF-Schutz für schreibende Requests |
| Lokaler Bot | Persönliches API-Token als `Authorization: Bearer sbm_…` (nur gehasht gespeichert, widerrufbar, nur für `POST /remote/matches`, E116) |

- Konto aus Nutzername und Passwort, ohne E-Mail (E83).
- Invite: einmalig, mit Ablaufdatum, legt Rolle fest; nur der Hash wird gespeichert (E83).
- Passwörter mit argon2id; Rate-Limit je Client-Adresse und Sperre nach fünf Fehlversuchen (E84).
- Passwort-Reset ohne Mailversand: durch Admin ausgelöster Einmal-Link (E83).
- CSRF-Schutz über den Header `X-SBM-CSRF: 1` bei jeder ändernden Anfrage (E84).

## Live-Kanal

| Option | Eigenschaft |
|--------|-------------|
| WebSocket | Bidirektional; für Mensch-gegen-Bot und Remote-Bots im eigenen Dienst `gateway` umgesetzt (E112, [gateway.md](gateway.md)), die API bleibt synchron |
| Server-Sent Events | Einfach, nur Server → Client; reicht für Zuschauen und Tabellen |

Quelle der Ereignisse (Runner → API):

| Option | Eigenschaft |
|--------|-------------|
| MongoDB Change Streams | Keine Zusatzkomponente; erfordert Replica Set |
| Pub/Sub-Broker (z. B. Redis) | Zusätzlicher Dienst; entkoppelt, geringe Latenz |
| Polling der DB | Einfachste Variante, höhere Latenz und Last |

Züge von Menschen und Remote-Bots laufen nicht über die API: Der Gateway reicht sie über das Relay an den Play-Runner, der sie wie jeden anderen Zug prüft (E112). Die API legt interaktive Partien nur an und gibt den Sitz-Token aus (E113).

## Upload

- Größen- und Typprüfung vor dem Speichern; die Anfrage ist auf 3 MiB begrenzt (E92).
- Hochgeladen werden einzelne Dateien statt Archiven, die API entpackt nichts; die Dateien liegen in GridFS (E82, E94).
- Upload erzeugt `bot` + Verifikationsjob; die Antwort enthält den Bot samt ID zur Statusabfrage.
- Scheitert das Einreihen des Jobs nach dem Speichern des Bots, bleibt der Bot in `uploaded` (bekannte Lücke ohne Transaktionen, siehe Replica Set in [datenmodell.md](datenmodell.md)).

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
