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
| `live` | Server-Sent Events einer laufenden Partie; beantwortet der Gateway, nicht die API (E142) |

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
| `GET /account/rating` | Eigenes Rating (`value`, `games`) aus gewerteten Partien gegen Bots, seit E163 das Gesamtrating, seit E169 mit `disciplines` (Rating je Disziplin, nach Name sortiert, archivierte eingeschlossen); nur für den Inhaber, jede Rolle (E117) |
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

Upload und Bot-Seite für Python, seit E207 auch für JavaScript (`language` im Upload):

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

Neue Fehlercodes: `invalid_upload` (400, mit `path` der betroffenen Datei), `too_large` (413, über 3 MiB), `name_taken` und `upload_conflict` (409). Gültige Uploads zählen je Konto unter `upload:{user_id}`, höchstens 20 am Tag (429 `too_many_attempts`; Zahl seit E154 eine Einstellung). Die API prüft nur Form und Grenzen, den Inhalt nie; sie startet keine Prozesse (E81).

### Stand M3, Schritt 4 (E95–E98)

„Mein Bereich“, Versionen, Quellcode und Partien durch Coder:

| Route | Aufgabe |
|-------|---------|
| `GET /bots/{id}` | Zusätzlich `description` und `versions` (alle Versionen des Namens, die der Betrachter sehen darf, neueste zuerst); öffentlich sind jetzt `verified`, `disabled` und `retired` (E96) |
| `POST /bots` | Optionales Feld `description` (E95) |
| `PATCH /bots/{id}` | Nur der Besitzer: `description` ändern und/oder `status` zwischen `verified` und `retired` schalten (E95, E96); andere Übergänge ergeben 400 `invalid_parameter` mit `field` `status` |
| `GET /bots/{id}/file?path=…` | Eine Datei als Download, nur Besitzer und Admins (E97) |
| `GET /bots/{id}/source` | Alle Dateien als ZIP `Name-Version.zip`, nur Besitzer und Admins (E97) |
| `POST /matches` | Partien eines eigenen `verified` Bots gegen jeden `verified` Bot: 1–10 Partien, bis 5 min + 5 s, Priorität 50; 20 Partien je Konto und Tag unter `matches:{user_id}` (E98; alle Grenzen seit E154 Einstellungen) |
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

Seit E163 ist `rating` eines Bots oder Kontos das Gesamtrating (nach Partien gewichteter Durchschnitt über die Disziplinen, `sbm_store.rating_values`); `before` und `after` einer Partie gelten in ihrer Disziplin. Beide Ranglisten nehmen `discipline_id`: ohne die Gesamtrangliste, mit ihr die der Disziplin (`rating` dann aus der Disziplin), eine unbekannte Id ergibt eine leere Liste, eine ungültige 400 (`sbm_store.rankings`).

### Stand M4, Schritt 3 (E130–E137)

| Route | Aufgabe |
|-------|---------|
| `GET /leagues`, `GET /leagues/{id}` | Öffentlich: alle Ligen nach Name mit Zahl der Anmeldungen und letzter Saison; im Detail zusätzlich alle Saisons, neueste zuerst, und die Anmeldungen mit Stufe der laufenden Saison oder Warteliste (`routes/leagues.py`, `league_view.py`) |
| `GET /seasons/{id}` | Öffentlich: Saison mit Schnappschuss der Einstellungen und je Stufe Tabelle, Zahl der Partien und der beendeten; eine laufende Saison rechnet die Tabelle aus den Partien, eine beendete zeigt die gespeicherte Endtabelle mit Ausgang (`season_view.py`) |
| `GET /bots/{id}/leagues` | Öffentlich: aktive Anmeldungen eines Bots |
| `POST /leagues/{id}/registrations`, `DELETE /leagues/{id}/registrations/{bot_id}` | Besitzer und Admins melden einen `verified` Bot an bzw. ab; Abmelden während einer Saison wertet seine wartenden Partien kampflos (`routes/league_registrations.py`). Audit `league.register` bzw. `league.deregister`, wenn ein Admin einen fremden Bot betrifft |
| `POST /admin/leagues`, `PATCH /admin/leagues/{id}` | Liga anlegen (mit Saison 1 `planned`) bzw. Einstellungen ändern, archivieren, wiederherstellen; Prüfung in `league_request.py`; Audit `league.create`, `league.update` |
| `POST /admin/leagues/{id}/start` | Gibt die erste Saison frei (setzt `starts_after`); Audit `league.start` |
| `GET /matches` | zusätzlich `season_id` und `tier` (nur mit `season_id`, sonst 400); `kind=bots` umfasst Einzelspiele und Ligapartien |

- Partien enthalten `league` (Liga, Saison mit Nummer, Stufe, Runde, Brett) oder `null` (`match_view.league_place`).
- `GET /queue` zeigt wartende Partien in der Reihenfolge, in der der Runner sie abruft (`sbm_store.queue_order.waiting`, E134).
- Zurückziehen durch den Besitzer (`routes/own_bot.py`), Sperren und Löschen durch einen Admin (`routes/admin_bots.py`) melden den Bot aus allen Ligen ab (`sbm_store.league_withdrawal`, E136).
- Neue Fehlercodes: `league_state` (409, Liga archiviert oder erste Saison schon freigegeben), `already_registered` (409, `field` `bot_id`); ein nicht verifizierter Bot ergibt `bot_state` (409).

### Stand M4, Schritt 4 (E138–E141)

| Route | Aufgabe |
|-------|---------|
| `GET /seasons/{id}/schedule?tier=n` | Öffentlich: Runden einer Stufe mit Partien nach Brett und spielfreiem Bot (`routes/season_schedule.py`, `schedule_view.py`, `sbm_store.season_schedule`). `tier` fehlt oder ist ungültig: 400; unbekannte oder geplante Saison, unbekannte Stufe: 404 |
| `GET /bots/{id}/seasons` | Öffentlich: Saisons dieser Version mit Stufe, Platz, Punkten und Ausgang, neueste zuerst (`routes/bot_history.py`, `bot_season_view.py`, `sbm_store.bot_seasons`) |
| `GET /bots/{id}/rating-history` | Öffentlich: je Disziplin die verbuchten Partien mit Rating vorher und nachher (`rating_history_view.py`, `sbm_store.rating_history`) |
| `GET /bots/{id}/record` | Öffentlich: Siege, Remis, Niederlagen gesamt und je Disziplin, freie Bedenkzeit mit `discipline_id` `null` zuletzt (`bot_record_view.py`, `sbm_store.bot_record`) |

Die drei Bot-Routen sehen Bots wie `GET /bots/{id}`: ein für den Aufrufer verborgener Bot ergibt 404.

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
| `routes/account_rating.py` | `GET /account/rating` (E117), seit E169 mit den Ratings je Disziplin |
| `routes/ratings.py` | zusätzlich `GET /ratings/players`, die Rangliste der Spieler (E118) |
| `routes/account_tokens.py`, `token_view.py` | `GET`/`POST /account/tokens`, `DELETE /account/tokens/{id}` für Coder (E116) |

- Partien der Typen `human` und `remote` sind öffentlich wie Botpartien: Liste, Detail, PGN (E119, vorher E115). `GET /matches?kind=bots` liefert nur Botpartien (`single`), `kind=players` nur die mit Spielern; ohne `kind` alle (`routes/matches.py`). Eine Seite ohne Bot zeigt `kind`, `bot_id` `null` und den Namen (Nutzername oder `Guest`); `match_view.side` gibt Konto, Sitz-Hash und Herkunft nie heraus.
- `GET /queue` hängt laufende interaktive Partien mit geschätztem Ende an `running` an (`queue_view.py`, `sbm_store.play.running_summaries`); sie belegen keinen Platz der Queue und ändern deren Schätzung nicht (E119).
- `require_coder` schützt Upload, eigene Bots, eigene Partien und Tokens; die Rolle `player` bekommt dort 403.
- Neue Fehlercodes: `no_capacity` (503), `too_many_games` (429).

### Stand M6 (E150–E169)

| Datei | Aufgabe |
|-------|---------|
| `routes/admin_audit_log.py`, `audit_view.py` | `GET /admin/audit`: Audit-Log neueste zuerst, Filter `actor`, `action`, `target`, `since`, `until` (UTC-Tage, einschließlich), dazu alle Akteure und Aktionen (E151); Abfrage in `sbm_store.audit`. Seit E169 je Eintrag `target_kind` und `target_label` (aktueller Name von Bot, Nutzer, Disziplin, Liga oder Partie, sonst `null`), aufgelöst in `audit_targets.py` |
| `params.py` | zusätzlich `optional_date` für Datumsfilter im Format `2026-10-10` |
| `routes/admin_match_actions.py` | `PATCH /admin/matches/{id}` (Priorität einer wartenden Partie), `POST /admin/matches/{id}/cancel`, `POST /admin/matches/{id}/repeat`, nur für Einzelspiele, je mit Eintrag im Audit-Log (E152) |
| `queue_view.py` | zusätzlich `priority` je Eintrag aus dem Job, für interaktive Partien 0 (E152) |
| `routes/admin_bot_checks.py` | `POST /admin/bots/{id}/recheck` und `POST /admin/bots/recheck` (eine Sprache) reihen Neuprüfungen ein, `POST /admin/bots/{id}/override` verifiziert einen abgelehnten Bot, je mit Eintrag im Audit-Log (E153); Logik in `sbm_store.rechecks` und `sbm_store.bots.override` |
| `bot_view.py` | zusätzlich `overridden_at`, für Besitzer und Admins `rechecks` (letzte 20 Berichte der Art `recheck`) und `recheck_pending` (E153) |
| `settings_groups.py`, `routes/admin_settings.py` | `GET /admin/settings` mit allen Gruppen und `rating_recount_pending`, `PUT /admin/settings/{coders,accounts,rating,estimate}` ersetzt eine Gruppe nach Bereichen je Feld und Regeln zwischen Feldern, je mit Eintrag im Audit-Log; geänderte Rating-Werte fordern eine Neuberechnung an (E154) |
| `routes/account_limits.py` | `GET /account/limits`: Grenzen für Uploads und eigene Partien ohne Priorität, nur Coder und Admins (E154) |
| `rating_start.py` | Startwert des Ratings einmal je Anfrage, für Bots und Konten ohne verbuchte Partie (E154) |
| `login.py`, `rate_limit.py`, `own_match_request.py`, `queue_estimate.py`, `invite_cli.py`, `routes/admin_invites.py` | lesen Sperre, Grenzen der Coder, Schätzung und Gültigkeit der Einladungen aus den Einstellungen (E154) |

- Neue Fehlercodes: `match_state` (409, Partie im falschen Zustand oder kein Einzelspiel), `not_repeatable` (409, Bot nicht mehr `verified` oder Disziplin archiviert), `bot_state` (409, Override eines nicht abgelehnten Bots).

Einzelspiele (Schritt 2, E155–E161):

| Datei | Aufgabe |
|-------|---------|
| `enqueue_request.py`, `own_match_request.py` | `rated` (Standard `true`, E158); `POST /matches` nimmt zusätzlich `start_fen` (E159) |
| `routes/admin_matches.py`, `routes/own_matches.py` | legen ab zwei Partien eine Serie an und setzen `created_by`, eigene Partien auch `counted`; Antwort mit `match_ids` und `series_id` (E155, E156) |
| `routes/admin_match_actions.py` | Wiederholen übernimmt `rated` und setzt den Admin als Ansetzer; `series_id` ist dort immer `null` (E156, E158) |
| `routes/series.py`, `series_view.py` | `GET /series/{id}`: beide Bots mit Punkten, Partien in Reihenfolge, Zahl der gezählten Partien (E155) |
| `match_view.py` | zusätzlich `series` (`id`, `index`, `games`) oder `null` je Partie (E155) |
| `routes/matches.py` | `GET /matches` filtert zusätzlich nach `discipline_id`, `opponent_id` (nur mit `bot_id`, sonst 400) und `mine=true` (Ansetzer, braucht eine Sitzung) (E156) |
| `routes/own_match_actions.py`, `rate_limit.give_back_games` | `POST /matches/{id}/withdraw`: wartende eigene Partie zurückziehen, Tageslimit im Fenster des Ansetzens zurückgeben (E157) |
| `routes/positions.py` | `POST /positions/from-pgn`: FEN aus PGN, Partie und Halbzügen über `sbm.arena.replay`, ohne Speichern und ohne Prozess (E159) |
| `routes/bot_opponents.py` | `GET /bots/{id}/opponents`: Bilanz gegen jeden Gegner-Bot aus beendeten Partien (E161); Abfrage in `sbm_store.opponents` |

- `POST /matches/{id}/withdraw` nutzt `match_state` (409) für laufende und beendete Partien und 404 für fremde.

Zufall, Rating je Disziplin, Ersteller (E162–E164):

| Datei | Aufgabe |
|-------|---------|
| `bot_choice.py` | Liest eine Bot-Wahl: Id oder `"random"` (Schema `BotChoice`); zieht je Partie über `sbm_store.bot_draw` aus den `verified` Bots, nie den Bot der anderen Seite; zu wenige Kandidaten ergeben 400 (E162) |
| `enqueue_request.py`, `routes/admin_matches.py` | `POST /admin/matches`: beide Seiten dürfen `"random"` sein; mit Farbwechsel tauschen die Seiten vor der Ziehung; mit Zufall keine Serie (`series_id` `null`) |
| `own_match_request.py`, `routes/own_matches.py` | `POST /matches`: höchstens eine Seite `"random"`, die feste muss ein eigener Bot sein |
| `play_request.py` | `POST /play`: `bot_id` `"random"` |
| `routes/ratings.py`, `routes/account_rating.py` | Rangliste gesamt oder je Disziplin (`discipline_id`), eigenes Gesamtrating (E163) |
| `owner_names.py`, `bot_view.py` | `owner` je Bot: Nutzername des Besitzers, einmal je Anfrage für alle Bots geladen, `null` bei Referenzbots (E164) |

### Stand M6, Schritt 3 (E170–E180)

| Endpunkt | Aufgabe |
|----------|---------|
| `GET /tournaments`, `GET /tournaments/{id}` | Öffentlich: alle Turniere nach Name mit Zahl der Anmeldungen und letzter Ausgabe; im Detail alle Ausgaben, neueste zuerst, und die Anmeldungen mit Kennzeichen `playing` für Teilnehmer der laufenden Ausgabe (`routes/tournaments.py`, `tournament_view.py`) |
| `GET /editions/{id}` | Öffentlich: Ausgabe mit Schnappschuss und Disziplinen, Teilnehmern nach Setzplatz, Fortschritt (Runde, Partien, beendete), Tabelle (Rundenturnier, Schweizer System; laufend aus den Partien, beendet gespeichert) oder Turnierbaum mit den Partien je Duell und Platzierung (K.-o.) (`edition_view.py`, `edition_bracket_view.py`) |
| `GET /editions/{id}/rounds` | Öffentlich: Runden mit Partien nach Brett und Freilos bzw. spielfreiem Bot; K.-o. und geplante Ausgaben ergeben eine leere Liste (`edition_rounds_view.py`) |
| `GET /bots/{id}/tournaments`, `GET /bots/{id}/editions` | Öffentlich: aktive Anmeldungen eines Bots bzw. Ausgaben dieser Version mit Setzplatz, Platz und Punkten (`bot_edition_view.py`, `sbm_store.bot_editions`) |
| `POST /tournaments/{id}/registrations`, `DELETE /tournaments/{id}/registrations/{bot_id}` | Wie bei Ligen; Abmelden während einer Ausgabe macht den Bot zum zurückgezogenen (`routes/tournament_registrations.py`, `sbm_store.tournament_withdrawal`). Audit `tournament.register` bzw. `tournament.deregister` für fremde Bots |
| `POST /admin/tournaments`, `PATCH /admin/tournaments/{id}` | Turnier anlegen (mit Ausgabe 1 `planned`) bzw. ändern, archivieren, wiederherstellen; `format` nur beim Anlegen; Prüfung in `tournament_request.py`, Kalender in `recurrence_request.py`; Audit `tournament.create`, `tournament.update` |
| `POST /admin/tournaments/{id}/start` | Startet die geplante Ausgabe jetzt (setzt `starts_after`); Audit `tournament.start` |
| `POST /admin/leagues/{id}/start` | Seit E171 auch für weitere Saisons ohne Kalender und zum Vorziehen eines Termins |
| `GET /matches` | zusätzlich `edition_id`; `kind=bots` umfasst auch Turnierpartien |

- Ligen nehmen `recurrence` statt `pause_minutes`; ein geänderter Kalender berechnet den Start der geplanten Saison bzw. Ausgabe neu (`league_setup.follow_calendar`, `tournament_setup.follow_calendar`).
- Partien enthalten zusätzlich `tournament` (Turnier, Ausgabe mit Nummer, Format, Runde, Brett, Phase, Partie) oder `null` (`match_view.tournament_place`).
- Zurückziehen, Sperren und Löschen eines Bots beenden auch seine Turnier-Anmeldungen (`sbm_store.withdrawal`).
- Audit-Ziele kennen `tournament` (`audit_targets.py`).
- Neuer Fehlercode `tournament_state` (409: Turnier archiviert, keine wartende oder schon fällige Ausgabe). `league_state` bedeutet beim Start jetzt: keine wartende oder schon fällige Saison.

### Spieler in Wettbewerben (E182–E186)

| Endpunkt | Aufgabe |
|----------|---------|
| `POST /leagues/{id}/registrations`, `POST /tournaments/{id}/registrations` | Zusätzlich `user_id` statt `bot_id` (genau eines): ein Konto meldet sich selbst an, Admins jedes aktive Konto (`participant_access.py`); Audit `league.register_account` bzw. `tournament.register_account` für fremde Konten. Fehlercodes `already_registered` (Feld `user_id`) und `user_state` (409, Konto inaktiv) |
| `DELETE /leagues/{id}/registrations/{participant_id}`, ebenso für Turniere | Id eines Bots oder Kontos; ein Konto meldet sich selbst ab, Admins jedes (Audit `…deregister_account`) |
| `GET /account/competition-games` | Wartende und laufende Wettbewerbspartien des Kontos mit seiner Farbe und `estimated_start`, sobald alle Konten bereit und anwesend sind (`routes/account_competition_games.py`, `start_estimate.py`, `sbm_store.competition_games`, E187) |
| `POST /matches/{id}/ready` | Eigene Seite bereit und anwesend; Antwort `PlaySeat` (neuer Sitz, wenn der mitgeschickte nicht passt); 409, wenn nicht freigegeben oder schon gestartet (`routes/match_ready.py`) |

- Teilnehmer in Anmeldungen, Stufen, Tabellen, Spielplänen, Ausgaben und Turnierbäumen haben `kind`, `bot_id` oder `user_id` (`participant_view.py`).
- Partien zeigen `readiness` (`readiness_view.py`): Frist, Start und je menschlicher Seite `ready` und `present`, `null` für Bots.
- Ligen und Turniere nehmen `ready_hours` (1 bis 336, Standard 48). Deaktivieren eines Kontos beendet seine Anmeldungen (`routes/admin_users.py`).

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
- Passwörter mit argon2id; Rate-Limit je Client-Adresse und Sperre nach fünf Fehlversuchen (E84; Zahl seit E154 eine Einstellung).
- Passwort-Reset ohne Mailversand: durch Admin ausgelöster Einmal-Link (E83).
- CSRF-Schutz über den Header `X-SBM-CSRF: 1` bei jeder ändernden Anfrage (E84).

## Live-Kanal

Umgesetzt mit E142 ohne die API: Die Runner senden die Züge laufender Partien direkt an den Gateway, der sie unter `GET /api/v1/matches/{id}/live` als Server-Sent Events ausliefert ([gateway.md](gateway.md)). Der `frontend`-Nginx leitet nur diesen Pfad an den Gateway, alles andere unter `/api` bleibt bei der API. So braucht es weder ein Replica Set für Change Streams noch einen zusätzlichen Broker, und die API bleibt synchron. Der Endpunkt steht nicht in `spec/web/openapi.json`; `GET /matches/{id}` bleibt die maßgebliche Quelle und der Rückfall der Partieseite.

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
