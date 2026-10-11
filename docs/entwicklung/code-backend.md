# Code-Karte: Web-API (`backend`)

Die Web-API ist eine reine JSON-API mit Flask unter `backend/` (Paket `sbm-api`, Modul `sbm_api`, Befehl `sbm-invite`). Sie liest und schreibt nur über `sbm-store` und startet nie Prozesse (E75, E81). Vertrag: [`spec/web/openapi.json`](../../spec/web/openapi.json), Präfix `/api/v1` (E73). Konzept, Routen und Rechte: [backend-api.md](../komponenten/backend-api.md).

## Einstieg

| Einstieg | Ort | Zweck |
|----------|-----|-------|
| `create_app(db=None, *, now, public_url, proxy_hops)` | [`app.py`](../../backend/src/sbm_api/app.py) | App-Factory. Ohne `db` aus `SBM_MONGO_URI`/`SBM_MONGO_DB`; `public_url` sonst aus `SBM_PUBLIC_URL`, `proxy_hops` aus `SBM_PROXY_HOPS` (dann `ProxyFix` für die Client-Adresse) |
| `sbm_api.wsgi:app` | [`wsgi.py`](../../backend/src/sbm_api/wsgi.py) | gunicorn auf dem Server, `flask --app sbm_api.wsgi run` lokal (E76) |
| `sbm-invite` | [`invite_cli.py`](../../backend/src/sbm_api/invite_cli.py) | Einladungslink von der Kommandozeile, etwa für den ersten Admin (E83) |

`create_app` legt `db`, `now` und `public_url` in `app.extensions["sbm"]` ab, setzt `app.json.sort_keys = False` (Felder in der Reihenfolge der Views), registriert jeden Blueprint aus dem Tupel `BLUEPRINTS` unter `API_PREFIX` und danach `csrf.register`, `current_user.register` und `register_error_handlers`.

Lesereihenfolge:

1. `app.py` und `context.py` – Aufbau und Zugriff auf `db`, `now`, `public_url` aus einer Anfrage.
2. `errors.py` – Fehlerformat und alle Fehlercodes.
3. `csrf.py`, `session_cookie.py`, `current_user.py` – wer die Anfrage stellt.
4. `params.py`, `body.py` – wie Eingaben geprüft werden.
5. Eine einfache Route wie `routes/matches.py` mit `match_view.py`, dann eine Admin-Route wie `routes/admin_users.py` mit `admin_audit.py`.
6. Die übrigen `*_request.py` und `*_view.py` bei Bedarf.

## Module

Alle Pfade relativ zu `backend/src/sbm_api/`.

### Anwendung

| Modul | Aufgabe |
|-------|---------|
| `__init__.py` | Paket der Web-API; nur Docstring mit Verweis auf den Vertrag (E73) |
| `app.py` | `create_app`, `utc_now`, `API_PREFIX`, `BLUEPRINTS`; Konstanten der Umgebungsvariablen |
| `wsgi.py` | `app = create_app()` für gunicorn |
| `context.py` | `db()`, `now()`, `public_url()`, `secure_cookies()` (Cookies mit `Secure`, sobald `public_url` mit `https://` beginnt) |
| `invite_cli.py` | `sbm-invite --role … --valid-days …`; Gültigkeit aus `account_settings` (E154), Audit-Eintrag mit Akteur `audit.CLI` |

### Anmeldung, Rechte, Grenzen

| Modul | Aufgabe |
|-------|---------|
| `csrf.py` | `before_request`: jede Anfrage außer `GET`/`HEAD`/`OPTIONS` auf eine bekannte Route braucht `X-SBM-CSRF: 1`, sonst 403 `csrf_failed` (E84) |
| `session_cookie.py` | Cookie `sbm_session`: HttpOnly, SameSite=Strict, Pfad `/api/`, 14 Tage; `read`, `put`, `remove` |
| `current_user.py` | Konto zur Sitzung, einmal je Anfrage in `g` geladen; Rolle und `active` jedes Mal aus der DB; `require_user`, `require_coder`, `require_admin`; verlängert die Sitzung höchstens einmal am Tag und setzt dann das Cookie neu (`after_request`) |
| `token_auth.py` | `require_token_user`: Konto und Token aus `Authorization: Bearer …`, nur für `POST /remote/matches`; 401 ohne gültigen Token, 403 für Spieler (E116) |
| `login.py` | `authenticate` (Sperre 15 min nach `login_failures` Fehlversuchen aus den Einstellungen, verrät nicht, ob der Name existiert), `open_session` |
| `passwords.py` | argon2id: `hash_password`, `verify`, `needs_rehash`, `verify_nothing` gegen Zeitmessung (E84) |
| `account_rules.py` | Regeln für Namen, Passwörter und Einmal-Tokens in Bodys (E83, E84) |
| `links.py` | `one_time_link`: Einmal-Links zur SPA, Token hinter `#` (E83) |
| `rate_limit.py` | `count_attempt` (Login, Links, Passwort: ein Zähler je Adresse, 30 in 15 min), `count_upload`, `count_games`, `give_back_games` (E84, E92, E98, E157) |
| `play_limits.py` | Grenzen interaktiver Partien: Plätze gesamt, gleichzeitig und je Tag je Adresse (als Hash), Konto und Token; gibt Zählungen bei Ablehnung zurück (E115) |

### Eingaben (Parsen)

| Modul | Aufgabe |
|-------|---------|
| `params.py` | Pfad- und Query-Parameter: `object_id`, `optional_object_id`, `optional_choice`, `integer`, `optional_date` |
| `body.py` | JSON-Bodys: `json_object(allowed)` lehnt unbekannte Felder ab; `string`, `boolean`, `integer`, `choice`, `identifier` mit optionalem `default` |
| `upload_request.py` | Multipart-Body von `POST /bots`: Felder, `paths[i]` zu `files[i]`, höchstens 3 MiB, Regeln aus `sbm.analysis.upload` (E92) |
| `enqueue_request.py` | Body von `POST /admin/matches`, geprüft wie im Referee; `enqueue` reiht Partien ein und legt ab zwei festen Partien eine Serie an (E85, E155, E162) |
| `own_match_request.py` | Body von `POST /matches` mit den Grenzen der Coder aus den Einstellungen; andere Startstellung macht ungewertet (E98, E154, E159) |
| `play_request.py` | Body von `POST /play`: geprüfter oder zufälliger Bot, Disziplin oder freie Zeit bis 30 min + 30 s (E114, E162) |
| `remote_request.py` | Body von `POST /remote/matches`: Gegner und Disziplin per Name (E116) |
| `discipline_request.py` | Bodys von `POST`/`PATCH /admin/disciplines`; `chosen` liest `discipline_id` einer Partie-Anfrage (E100) |
| `league_request.py` | Bodys von `POST`/`PATCH /admin/leagues` (E131); Kalender statt Pause (E171) |
| `tournament_request.py` | Bodys von `POST`/`PATCH /admin/tournaments`; Format nur beim Anlegen (E172) |
| `recurrence_request.py` | Kalender in den Bodys von Ligen und Turnieren und seine Ausgabe (Schema `Recurrence`, E171) |
| `bot_choice.py` | Bot-Wahl als Id oder `"random"`; `check_pool`, `draw`, `pairings`, `label` (E162) |
| `bot_description.py` | `check`: Beschreibung als reiner Text, Zeilenenden als LF (E95) |
| `participant_access.py` | Wer einen Teilnehmer an- oder abmeldet: einen Bot sein Besitzer oder ein Admin (nur geprüft), ein Konto es selbst in jeder Rolle oder ein Admin (nur aktiv); Admins an Fremdem ins Audit (E136, E179, E182) |
| `settings_groups.py` | Die vier Gruppen von `/admin/settings` mit Store-Modul und Typ; `PROBLEMS` für Regeln zwischen Feldern (E154) |

### Ausgaben (Views und Hilfen)

| Modul | Aufgabe |
|-------|---------|
| `match_view.py` | `match_summary`, `match_detail`, `series_place`, `tournament_place` (E178), `side`; `termination_detail` bleibt intern |
| `bot_view.py` | `bot_view`, `bot_detail_view`; Details (Dateien, Report, Neuprüfungen) nur für Besitzer und Admins (E95, E153, E164) |
| `report_view.py` | Prüfbericht (Schema `VerificationReport`); Ids von Bot und Job bleiben intern (E92) |
| `series_view.py` | Serie mit Punkten und Partien (Schema `Series`, E155) |
| `queue_view.py` | Queue aus Jobs und Partien, dazu laufende interaktive Partien (E119) |
| `queue_estimate.py` | `schedule`: geschätzte Start- und Endzeiten; `RecentDurations` je Anfrage zwischengespeichert (E20, E154) |
| `discipline_view.py` | Disziplin (Schema `StoredDiscipline`) |
| `league_view.py` | Liga, Saisons und Anmeldungen (Schemas `League`, `LeagueDetail`, `SeasonSummary`, `LeagueRegistration`, E137) |
| `season_view.py` | Saison mit Tabellen: laufend aus den Partien berechnet, beendet aus `final` (Schema `Season`, E135, E137) |
| `schedule_view.py` | Spielplan einer Stufe nach Runden mit spielfreiem Bot (Schema `SeasonSchedule`, E138) |
| `bot_season_view.py` | Saison eines Bots mit Stufe, Platz und Ausgang (Schema `BotSeason`, E139) |
| `tournament_view.py` | Turnier, Ausgaben und Anmeldungen (Schemas `Tournament`, `TournamentDetail`, `EditionSummary`, `TournamentRegistration`, E180) |
| `edition_view.py` | Ausgabe mit Teilnehmern, Tabelle bzw. Baum und Platzierungen; laufend aus den Partien, beendet aus `final` (Schema `Edition`, E177, E180) |
| `edition_rounds_view.py` | Partien eines Rundenturniers oder Schweizer Systems nach Runde und Brett; K.-o. liefert eine leere Liste (Schema `EditionRounds`, E180) |
| `edition_bracket_view.py` | K.-o.-Baum mit Duellen, Punkten und Partien je Phase (Schemas `Duel`, `DuelSide`, `DuelGame`, E176, E180) |
| `bot_edition_view.py` | Ausgabe eines Bots mit Setzplatz, Platz oder Punkten (Schema `BotEdition`, E180) |
| `rating_history_view.py` | Rating-Verlauf je Disziplin, meistgespielte zuerst (Schema `DisciplineRatingHistory`, E140) |
| `bot_record_view.py` | Bilanz gesamt und je Disziplin, freie Bedenkzeit zuletzt (Schema `BotRecord`, E141) |
| `participant_view.py` | `participant`: Teilnehmer als Bot oder Konto mit `kind`, `bot_id`, `user_id`, Name und Version (Schema `LeagueBot`, E182) |
| `readiness_view.py` | Bereitschaft einer Wettbewerbspartie mit Frist und Stand je Konto-Seite; `null` vor der Freigabe (Schema `Readiness`, E183) |
| `user_view.py` | `current_user_view`, `session_view`, `user_view`; der Hash geht nie hinaus |
| `invite_view.py` | Einladung ohne Token-Hash |
| `token_view.py` | API-Token für die Kontoseite; der Token selbst nur einmal beim Anlegen (E116) |
| `play_view.py` | `seat_view`: Partie, Sitz-Token und Socket-Pfad nach gateway-v1 |
| `audit_view.py` | Audit-Eintrag (Schema `AuditEntry`); Ids und Zeiten in `details` als Text (E151) |
| `timestamps.py` | `timestamp`, `optional_timestamp`: RFC 3339 in UTC mit Millisekunden |
| `owner_names.py` | `owner_name`: Nutzername des Besitzers, einmal je Besitzer und Anfrage (E164) |
| `rating_start.py` | Startwert des Ratings, einmal je Anfrage gelesen (E103, E154) |
| `pgn.py` | `match_pgn`: Partie als PGN im Format der Arena |

### Fehler, Zugriff, Audit

| Modul | Aufgabe |
|-------|---------|
| `errors.py` | `ApiError(status, code, message, field, headers, path=…)`, Fehlercodes als Konstanten, Fabriken (`invalid_parameter`, `not_found`, `forbidden`, `too_many_attempts` mit `Retry-After` …), `register_error_handlers` |
| `bot_access.py` | `visible_bot` (verborgene Bots sind 404), `owned_bot`, `source_bot` (E15, E95, E97) |
| `admin_audit.py` | `record(admin, action, target, details)` über `sbm_store.audit` mit `context.now()` (E85) |

### Routen: öffentlich

Alle unter `routes/`; je Modul ein Blueprint mit dem Modulnamen.

| Modul | Aufgabe |
|-------|---------|
| `routes/__init__.py` | Paket; ein Blueprint je Ressource des Vertrags |
| `routes/health.py` | `GET /health`: API und Datenbank erreichbar |
| `routes/matches.py` | `GET /matches` (Filter, `kind`, `mine`), `/matches/{id}`, `/matches/{id}/pgn` (E119, E156) |
| `routes/series.py` | `GET /series/{id}` (E155) |
| `routes/positions.py` | `POST /positions/from-pgn` über `sbm.arena.replay`, ohne Speichern (E159) |
| `routes/bots.py` | `GET /bots`, `GET /bots/{id}`, `POST /bots` (Upload für Coder, E91, E92) |
| `routes/bot_opponents.py` | `GET /bots/{id}/opponents` (E161) |
| `routes/bot_history.py` | `GET /bots/{id}/seasons`, `/rating-history` und `/record` (E139–E141) |
| `routes/season_schedule.py` | `GET /seasons/{id}/schedule?tier=n` (E138) |
| `routes/bot_source.py` | `GET /bots/{id}/file` und `/source`, nur Besitzer und Admins, immer als Download (E97) |
| `routes/queue.py` | `GET /queue` mit Schätzung (E20) |
| `routes/disciplines.py` | `GET /disciplines`, `/disciplines/{id}` (E100) |
| `routes/ratings.py` | `GET /ratings`, `/ratings/players`, gesamt oder je Disziplin (E103, E118, E163) |
| `routes/leagues.py` | `GET /leagues`, `/leagues/{id}`, `/seasons/{id}`, `/bots/{id}/leagues` (E137) |
| `routes/tournaments.py` | `GET /tournaments`, `/tournaments/{id}`, `/editions/{id}`, `/editions/{id}/rounds`, `/bots/{id}/tournaments`, `/bots/{id}/editions` (E180) |

### Routen: Sitzung und eigenes Konto

| Modul | Aufgabe |
|-------|---------|
| `routes/session.py` | `GET`/`POST`/`DELETE /session` (E84) |
| `routes/invites.py` | `POST /invites/redeem`: Konto anlegen und anmelden (E83) |
| `routes/password_resets.py` | `POST /password-resets/redeem`: neues Passwort, andere Sitzungen enden (E83) |
| `routes/account.py` | `PUT /account/password` (E84) |
| `routes/account_rating.py` | `GET /account/rating` (E117, E163) |
| `routes/account_bots.py` | `GET /account/bots`: eigene Bots in jedem Status (E91) |
| `routes/account_limits.py` | `GET /account/limits` für Coder (E154) |
| `routes/account_tokens.py` | `GET`/`POST /account/tokens`, `DELETE /account/tokens/{id}` (E116) |
| `routes/own_bot.py` | `PATCH /bots/{id}`: Beschreibung, Zurückziehen (E95, E96) |
| `routes/own_matches.py` | `POST /matches` für Coder (E98) |
| `routes/own_match_actions.py` | `POST /matches/{id}/withdraw` (E157) |
| `routes/league_registrations.py` | `POST /leagues/{id}/registrations` mit `bot_id` oder `user_id`, `DELETE …/registrations/{participant_id}` nach `participant_access.py`; Abmelden in laufender Saison ist ein Rückzug (E136, E182) |
| `routes/tournament_registrations.py` | `POST /tournaments/{id}/registrations` mit `bot_id` oder `user_id`, `DELETE …/registrations/{participant_id}` nach `participant_access.py`; Abmelden in laufender Ausgabe ist ein Rückzug; Admins an fremden Bots und Konten ins Audit (`tournament.register`, `tournament.deregister`, `…_account`) (E179, E182) |
| `routes/account_competition_games.py` | `GET /account/competition-games`: offene Liga- und Turnierpartien des eigenen Kontos, freigegebene zuerst nach Frist (E183) |
| `routes/match_ready.py` | `POST /matches/{id}/ready`: Konto einer Seite ist bereit und anwesend, Antwort mit Sitz nach gateway-v1; die Seite wiederholt das, solange sie wartet (E183) |
| `routes/play.py` | `POST /play`: Gast oder Konto gegen einen geprüften Bot (E114) |
| `routes/remote.py` | `POST /remote/matches` mit API-Token (E116) |

### Routen: Admin

Jede Route beginnt mit `require_admin()`; jede ändernde schreibt mit `admin_audit.record` (Aktion in Klammern).

| Modul | Aufgabe |
|-------|---------|
| `routes/admin_users.py` | Konten auflisten, Rolle/Aktiv ändern (`user.update`; Deaktivieren beendet die Anmeldungen des Kontos, E182), Reset-Link (`password_reset.create`) (E83, E85) |
| `routes/admin_invites.py` | Einladungen auflisten, anlegen (`invite.create`), zurückziehen (`invite.revoke`) |
| `routes/admin_bots.py` | Sperren/Freigeben (`bot.update`), endgültig löschen (`bot.delete`) (E93, E105) |
| `routes/admin_bot_checks.py` | Neuprüfung eines Bots (`bot.recheck`) oder einer Sprache (`bot.recheck_language`), Override (`bot.override`) (E153) |
| `routes/admin_disciplines.py` | Disziplinen anlegen (`discipline.create`), ändern und archivieren (`discipline.update`) (E100) |
| `routes/admin_leagues.py` | Ligen anlegen (`league.create`), ändern und archivieren (`league.update`), wartende Saison starten (`league.start`); nie löschen (E131, E132, E171) |
| `routes/admin_tournaments.py` | Turniere anlegen (`tournament.create`), ändern und archivieren (`tournament.update`), wartende Ausgabe starten (`tournament.start`); nie löschen (E171, E172) |
| `routes/admin_matches.py` | `POST /admin/matches` (`match.enqueue`) (E71, E85) |
| `routes/admin_match_actions.py` | Priorität (`match.priority`), Abbrechen (`match.cancel`), Wiederholen (`match.repeat`) (E152) |
| `routes/admin_play.py` | Grenzen interaktiver Partien (`play.settings`) (E115) |
| `routes/admin_queue.py` | Queue pausieren/fortsetzen (`queue.pause`) |
| `routes/admin_audit_log.py` | `GET /admin/audit` mit Filtern (E151) |
| `routes/admin_settings.py` | `GET /admin/settings`, `PUT /admin/settings/{gruppe}` (`settings.<gruppe>`); geänderte Rating-Regel fordert eine Neuberechnung an (E154, E105) |

## Ablauf

Eine ändernde Anfrage, am Beispiel `POST /api/v1/admin/matches`:

1. `csrf.check_header` (`before_request`) prüft `X-SBM-CSRF: 1`.
2. `routes/admin_matches.enqueue_matches` ruft `require_admin()`. `current_user` liest das Cookie (`session_cookie.read`), sucht die Sitzung über `sbm_store.sessions` und das Konto über `sbm_store.users`; ohne Sitzung 401 `unauthenticated`, mit falscher Rolle 403 `forbidden`.
3. `enqueue_request.parse(db)` liest den Body mit `body.json_object` und den Feldfunktionen, wählt Bots über `bot_choice` und die Disziplin über `discipline_request.chosen`, prüft wie der Referee. Fehler werden als `ApiError` geworfen.
4. `enqueue_request.enqueue` schreibt Partien, Jobs und gegebenenfalls die Serie über `sbm_store`.
5. `admin_audit.record(admin, "match.enqueue", None, details)` schreibt den Audit-Eintrag.
6. Die Route gibt `(enqueued.response(), 201)` zurück; Flask macht daraus JSON.
7. `current_user.refresh_cookie` (`after_request`) setzt das Cookie neu, falls die Sitzung verlängert wurde.
8. Jede geworfene `ApiError` wandelt `errors.api_error` in `{code, message, field?, path?}` mit Status und Headern; unbekannte Pfade werden 404 `not_found`, zu große Uploads 413 `too_large`, ein Ausfall der DB 503 `unavailable`, alles andere 500 `internal`.

Eine lesende Anfrage, am Beispiel `GET /api/v1/matches?bot_id=…`:

```
routes/matches.list_matches
  ├─ params.optional_object_id / optional_choice / integer   → 400 invalid_parameter mit field
  ├─ sbm_store.matches.match_filter + page                   (Abfrage im Store)
  └─ match_view.match_summary je Partie                      → {"items": [...], "total": n}
```

## Konventionen

- **Ein Blueprint je Modul:** `blueprint = Blueprint("<modulname>", __name__)`, Routen mit `@blueprint.get/post/patch/put/delete` und Pfad ohne Präfix. Der Docstring nennt Methoden, Pfade und Entscheidungen.
- **Reihenfolge in einer Route:** zuerst die Rechteprüfung (`require_*`), dann Parsen, dann Store, dann Audit, dann View. Rate-Limits zählen erst, wenn die Anfrage gültig ist („a mistake costs nothing“, `routes/bots.py`, `routes/own_matches.py`).
- **Kontext statt Globals:** Datenbank und Zeit nur über `context.db()` und `context.now()`. Die Uhr wird in `create_app(now=…)` injiziert; nur `app.utc_now` und `invite_cli` lesen die echte Zeit.
- **Datenbank über `sbm_store`:** Abfragen und Schreibzugriffe liegen in Store-Modulen (E75); neue Abfragen gehören dorthin, nicht in die Route.
- **Fehler werfen, nicht zurückgeben:** `ApiError` oder eine Fabrik aus `errors.py`. `field` nennt den Parameter bzw. das Body-Feld, `path` die Datei eines Uploads. Neue Codes sind Konstanten in `errors.py`; das Frontend übersetzt den Code (E32).
- **Verborgenes ist 404:** Wer einen Bot nicht sehen darf, bekommt `not_found`, nicht `forbidden` (`bot_access.visible_bot`).
- **`*_request` parst, `*_view` formt:** Request-Module lesen Body oder Formular und geben ein `@dataclass(frozen=True)` oder geprüfte Werte zurück. View-Module wählen die Felder des Schemas ausdrücklich aus; interne Felder (Hashes, `termination_detail`, Job-Ids) gehen nie hinaus.
- **Ausgabeform:** Ids als Text (`str(ObjectId)`), Zeiten über `timestamps.timestamp`, Listen als `{"items": [...]}` bzw. mit `total` bei Paging. Status 201 als Tupel `(body, 201)`, 204 über `make_response("", 204)`.
- **Werte je Anfrage zwischenspeichern:** Was mehrere Views brauchen (Besitzernamen, Startwert des Ratings, Partiedauern), wird einmal je Anfrage gelesen (`owner_names`, `rating_start`, `queue_estimate.RecentDurations`).
- **Audit:** Jede ändernde Admin-Aktion ruft `admin_audit.record`. Aktion als `objekt.verb` (`user.update`, `match.cancel`), Ziel als Id oder `None`, Details als kleines JSON-Objekt.

## Erweitern

### Neuer Endpunkt

1. Pfad, Parameter, Body und Antworten in `spec/web/openapi.json` eintragen, auch Fehlerantworten mit dem Schema `Error`. Neue Fehlercodes in dessen `enum` aufnehmen.
2. Braucht es neue Abfragen, diese zuerst in `services/store` anlegen und dort testen.
3. Eingaben: einfache Parameter direkt mit `params`/`body`; ein Body mit mehreren Regeln bekommt ein Modul `<thema>_request.py` mit `parse(...)`.
4. Ausgabe: ein Modul `<thema>_view.py`, das genau die Felder des Schemas liefert.
5. Route in `routes/<ressource>.py` mit eigenem Blueprint anlegen (oder in das passende Modul derselben Ressource einfügen).
6. Ein neues Modul in `app.py` importieren und in `BLUEPRINTS` aufnehmen.
7. Ein neuer Fehlercode: Konstante in `errors.py` und Übersetzungen unter `error` in `frontend/src/i18n/de.json` und `en.json`.
8. Tests in `backend/tests/test_<thema>.py` mit den Fixtures `client`, `login` oder `admin`; jede Antwort wird dabei gegen den Vertrag geprüft. Nicht angemeldet, falsche Rolle und ungültige Eingaben mittesten.
9. In `frontend/` `npm run api-types` ausführen und `src/api/schema.d.ts` mitliefern; `npm run api-types:check` läuft in CI.
10. Tabelle in [backend-api.md](../komponenten/backend-api.md) und gegebenenfalls eine Entscheidung in `docs/00_entscheidungen.md` nachführen.

### Neue Admin-Aktion mit Audit-Eintrag

1. Route im Vertrag unter `/admin/…` beschreiben, mit 401 und 403.
2. In `routes/admin_<thema>.py`: `admin = require_admin()` als erste Zeile, dann Parsen und Store.
3. Nach erfolgreicher Änderung `admin_audit.record(admin, "<objekt>.<verb>", target, details)`; nur bei Erfolg, damit abgelehnte Anfragen keinen Eintrag erzeugen.
4. Route in `ADMIN_ROUTES` in `backend/tests/test_admin_access.py` aufnehmen: Gäste bekommen 401, Coder 403.
5. Test, dass der Eintrag mit Aktion, Ziel und Details im Audit-Log steht; `test_admin_match_actions.py` liest ihn dafür mit `db[AUDIT_LOG].find_one({"action": …})`.
6. Die Aktion erscheint ohne weitere Änderung in den Filtern von `/admin/audit`, da `GET /admin/audit` Akteure und Aktionen aus der Datenbank liest (E151); in backend-api.md die Aktion nennen.

### Neue Rollenprüfung

1. Bestehende Prüfungen nutzen: `require_user`, `require_coder`, `require_admin` aus `current_user.py`; für API-Tokens `token_auth.require_token_user`; Besitz über `bot_access`.
2. Eine neue Prüfung als `require_<name>()` in `current_user.py`: `user = require_user()`, Rolle gegen die Konstanten aus `sbm_store.users` vergleichen, sonst `forbidden("…")`, das Konto zurückgeben.
3. Gilt sie für eine neue Rolle, zuerst `ROLES` in `sbm_store.users` und das Schema `Role` in `spec/web/openapi.json` erweitern, Entscheidung eintragen; das Frontend übersetzt Rollennamen.
4. Tests nach dem Muster von `test_player_role.py`: Konten jeder Rolle über `login(name, role)` und je Route den erwarteten Status (401, 403 oder Erfolg).
5. Rollentabelle in [backend-api.md](../komponenten/backend-api.md) anpassen.

### Neue Einstellungsgruppe

1. Modul mit `LIMITS`, `get`, `save` und `problem` in `sbm_store` anlegen (Muster `coder_settings`).
2. In `settings_groups.GROUPS` einen `Group` eintragen und Fehlertexte in `PROBLEMS`; die Route `PUT /admin/settings/<name>` und der Audit-Eintrag `settings.<name>` entstehen in `routes/admin_settings.py` von selbst.
3. Vertrag (`AdminSettings`, neuer Pfad) und `test_admin_access.py` ergänzen.

## Tests

Die Tests liegen in `backend/tests/`, eine Datei `test_<thema>.py` je Route bzw. Thema. Hilfsmodule sind über `pythonpath = ["tests"]` importierbar.

| Datei | Inhalt |
|-------|--------|
| `conftest.py` | Fixtures: `openapi` (Vertrag einmal je Sitzung geladen, PGN als Text, Dateien und ZIP als Bytes), `app` (migrierte DB, `keep_expired`, `create_app` mit Testuhr und `SITE`; Test-Client prüft **jede** Antwort mit openapi-core gegen `spec/web/openapi.json`), `client`, `login(username, role)` (neues Konto, angemeldeter Client und Konto), `admin` (angemeldeter Admin-Client), `clock`, `reference_bots` (Random und Material), `enqueue` (eine Partie zwischen den Referenzbots) |
| `accounts.py` | `CSRF`-Header, `PASSWORD`, `Clock` mit `now()` und `advance()`, `add_user(db, name, role, active=…)` |
| `bot_uploads.py` | `upload_form` und `post_upload` für Multipart-Bodys von `POST /bots`; `store_bot` legt einen Bot an wie der Upload, `verify` beendet die Prüfung wie der Runner |
| `stored_games.py` | `NOW`, `BLITZ`, `SITE`, Eröffnung; `start_with_opening`, `finish_by_resignation`: Partien in den Zuständen, die der Runner hinterlässt |
| `stored_disciplines.py` | `store_discipline`: Disziplin direkt in der DB |
| `test_admin_access.py` | Rechte-Matrix: jede Admin-Route mit Gast (401) und Coder (403) |

- Die Fixture `db` kommt aus `sbm_store.testing` (pytest-Plugin von `sbm-store`): je Test eine frische Datenbank auf `SBM_TEST_MONGO_URI` (Standard `mongodb://localhost:27017`). Ohne erreichbaren Server werden die Tests übersprungen, mit `SBM_REQUIRE_MONGO=1` scheitern sie (so in CI).
- Ändernde Anfragen in Tests brauchen `headers=CSRF`, sonst 403 `csrf_failed`.
- Zeit vorstellen mit `clock.advance(timedelta(...))`, etwa für Ablauf von Links und Sitzungen.
- Eine Antwort, die nicht zum Vertrag passt, lässt den Test scheitern; Vertrag und Code also gemeinsam ändern.

Befehle aus dem Repo-Wurzelverzeichnis (Pakete wie in `CLAUDE.md` installiert, MongoDB laufend):

```
pytest backend
ruff check backend
ruff format --check backend
```

`sbm-invite` hat eigene Tests in `test_invite_cli.py`, die `main(argv, environ)` direkt aufrufen.
