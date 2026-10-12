# Code-Karte: services/store

Gemeinsamer MongoDB-Zugriff für Runner, Web-API und Werkzeuge (E75): Verbindung, Collections, Queue, Ratings, Einstellungen und Migrationen. Ort `services/store`, Paket `sbm-store`, Modul `sbm_store`, Befehl `sbm-migrate`. Das Schema der Dokumente steht in [datenmodell.md](../komponenten/datenmodell.md); diese Karte beschreibt nur den Code.

## Einstieg

| Einstieg | Ort | Zweck |
|----------|-----|-------|
| `sbm-migrate` | [`migrate.py`](../../services/store/src/sbm_store/migrate.py) `main` | Wendet alle offenen Migrationen an; liest `SBM_MONGO_URI` und `SBM_MONGO_DB` (Standard `sbm`) |
| `database_from_env` | [`connection.py`](../../services/store/src/sbm_store/connection.py) | Öffnet die Datenbank für jeden Dienst; die URI trägt den Mongo-Nutzer des Dienstes |
| pytest-Plugin `sbm_store` | [`testing.py`](../../services/store/src/sbm_store/testing.py), Entry-Point `pytest11` in `pyproject.toml` | Fixture `db` für alle Pakete, die `sbm-store` installieren (Store, Runner, API) |

Das Paket hat keine Klassen für Collections. Jedes Modul ist eine Sammlung von Funktionen auf einer Collection; der erste Parameter ist immer die `Database`, Dokumente sind einfache `dict`s wie gespeichert ([`__init__.py`](../../services/store/src/sbm_store/__init__.py)).

Lesereihenfolge:

1. `names.py` (alle Collection-Namen) und `connection.py`.
2. `jobs.py` und `matches.py`: Queue und Partien, der Kern des Pakets.
3. `bots.py`, `bot_files.py`: ein Bot je Version und seine Dateien in GridFS.
4. `ratings.py` mit `rating_values.py` und `rating_recount.py`: der heikelste Code ohne Transaktionen.
5. `settings_document.py` und ein Gruppenmodul wie `coder_settings.py`.
6. `migrate.py`, `migrations/__init__.py`, dann einzelne Migrationen.

## Module

Alle Pfade relativ zu `services/store/src/sbm_store/`.

### Grundlagen

| Modul | Aufgabe |
|-------|---------|
| `__init__.py` | Nur Docstring: Konvention „Datenbank zuerst, Dokumente als dict“ |
| `connection.py` | `connect` mit `tz_aware=True` (Zeiten kommen in UTC zurück) und 5 s Server-Auswahl; `database_from_env` aus `SBM_MONGO_URI`/`SBM_MONGO_DB` |
| `names.py` | Konstanten aller Collection-Namen, dazu der GridFS-Bucket `bot_files` und `schema_migrations` |
| `tokens.py` | Geheime Tokens (32 Zufallsbytes, 43 Zeichen) und ihr SHA-256; gespeichert wird nur der Hash (E83, E84) |
| `settings_document.py` | `load`/`store` einer Einstellungsgruppe als ein Dokument in `settings`; fehlende Felder behalten den Standard der Dataclass (E154) |
| `migrate.py` | `migrate` wendet nicht verbuchte Migrationen der Reihe nach an und trägt sie in `schema_migrations` ein; `main` für `sbm-migrate` |
| `testing.py` | pytest-Fixtures `mongo_uri` und `db` (frische Datenbank je Test) und `keep_expired`, das TTL-Indizes für Tests mit fester Uhr abschaltet |

### Bots und Verifikation

| Modul | Aufgabe |
|-------|---------|
| `bots.py` | Collection `bots`: ein Dokument je Version, Status (`uploaded` … `retired`), Linie über `lineage_id`, Name ohne Groß-/Kleinschreibung über `name_key`; Statuswechsel für Pipeline, Admin (Sperre, Override) und Besitzer (E91, E93, E96, E153) |
| `versions.py` | Versionsnummern `X.Y.Z` (je Teil 0–999): `parse`, `next_patch` (E91) |
| `bot_files.py` | Hochgeladene Dateien im GridFS-Bucket `bot_files`: speichern, lesen, löschen, `source_hash` über alle Dateien (E82, E94) |
| `bot_deletion.py` | Endgültiges Löschen einer Version samt Dateien, Berichten, Jobs und Partien in absturzsicherer Reihenfolge; fordert bei verbuchten Partien eine Neuberechnung an (E105) |
| `bot_draw.py` | Zufälliger verifizierter Gegner per `$sample` (E162) |
| `verification_reports.py` | Collection `verification_reports`: Bericht der Pipeline je Prüfung, Art `upload` oder `recheck` (E92, E153) |
| `rechecks.py` | Neuprüfung eines Bots oder aller Bots einer Sprache als Job `verification` mit `recheck: true` (E153) |

### Partien und Queue

| Modul | Aufgabe |
|-------|---------|
| `jobs.py` | Collection `jobs`: die eine Queue (A8, E20); atomares `claim` mit Lease, `extend`, `complete`, `fail`, `retry`, `release`, Wiederaufnahme abgelaufener Leases, Eingriffe der Admins (E152, E157) |
| `matches.py` | Collection `matches`: Einzelspiel anlegen (`new_match`), Listen mit `SUMMARY_PROJECTION`, Filter, Statuswechsel `queued → running → finished/aborted`, Dauer für die Schätzung |
| `enqueue.py` | `enqueue_match`: erst Partie, dann Job; genutzt von `sbm-enqueue` und der Web-API |
| `play.py` | Interaktive Partien (`human`, `remote`) mit Sitz-Hash, `origin` für die Grenzen und Job der Art `play` (E113–E116) |
| `discipline.py` | Dataclass `Discipline` als `discipline_snapshot` der Partie; `is_rated` (gespeicherte Disziplin und Grundstellung, E100) |
| `disciplines.py` | Collection `disciplines`: anlegen, ändern, archivieren, `snapshot` für Partien; `NameTaken` bei doppeltem Namen (E100); `by_name` findet eine Disziplin über `name_key` unabhängig von Groß- und Kleinschreibung, auch archiviert (E169) |
| `opponents.py` | Bilanz eines Bots gegen jeden Gegner per Aggregation; Gegner können auch Konten sein (E161, E182) |
| `competition_games.py` | Offene Liga- und Turnierpartien eines Kontos, freigegebene zuerst nach Frist (E186) |
| `bot_record.py` | Siege, Remis, Niederlagen eines Bots je Disziplin per Aggregation; `Counts` (E141) |
| `rating_history.py` | Rating vorher und nachher je verbuchter Partie eines Bots, nach Disziplin (E140) |

### Ratings

| Modul | Aufgabe |
|-------|---------|
| `rating_rule.py` | Dataclass `RatingRule` und `white_gain`: wie ein Ergebnis die Ratings bewegt (E103) |
| `rating_values.py` | Feld `ratings` je Disziplin auf Bot oder Konto; `in_discipline` und das berechnete Gesamtrating `overall` (E163) |
| `ratings.py` | `count_pending`: verbucht beendete gewertete Partien in Reihenfolge mit eindeutiger `rating.seq`; repariert vorher die zuletzt verbuchte (E103, E117) |
| `rating_recount.py` | Anforderung einer Neuberechnung als Token im Dokument `settings/ratings`; `run_if_requested` setzt alles zurück und zählt neu (E105) |
| `rankings.py` | Ranglisten der Bots und Spieler, gesamt oder je Disziplin, sortiert in Python (E103, E118, E163) |

### Ligen (E130–E137)

| Modul | Aufgabe |
|-------|---------|
| `leagues.py` | Collection `leagues`: Einstellungen je Liga, Name eindeutig über `name_key`, archivieren statt löschen; `NameTaken` (E131) |
| `seasons.py` | Collection `seasons`: `planned → running → finished`, Freigabe, fällige Saisons, Aufstellung in `tiers`, Kopie der Einstellungen samt `discipline_snapshot`, Endtabellen in `final` (E132) |
| `registrations.py` | Collection `registrations`: höchstens eine aktive Anmeldung je Bot oder Konto und Liga bzw. Turnier (`target_type`, eindeutiger Teilindex über `bot_id` und `user_id`), Abmelden behält das Dokument als `left`, Deaktivieren eines Kontos mit Grund `deactivated` (E136, E179, E182) |
| `participants.py` | Teilnehmer als Bot (`bot_id`) oder Konto (`user_id`): `key`, `is_human`, `side_query` (E182) |
| `competition_entrants.py` | Wer von den Angemeldeten starten darf: Bots geprüft, Konten aktiv; Einträge mit `bot_id` oder `user_id`, Name und Version (E136, E179, E182) |
| `competition_readiness.py` | Partien mit Konten: `release` nach Runde und Brett (ein Konto hat höchstens eine freigegebene Partie, nur aus der aktuellen Runde nach `competition_pace`, E189), `mark_ready`, `startable` (startet die nächste Runde die Partie, E187), `start_ready` legt den Play-Job an, `expire` wertet zur Frist (`forfeit_absent`, beide abwesend 0-0), `reset` nach Infrastrukturfehlern (E183–E185) |
| `league_setup.py` | Liga mit erster Saison anlegen, eine wartende Saison von Hand starten, nach einem geänderten Kalender den Start neu berechnen (`follow_calendar`) (E131, E132, E171) |
| `league_lineup.py` | Reine Funktionen: Aufstellung in Stufen beim Start, Auf- und Abstieg am Ende (E133) |
| `league_pairing.py` | Reine Funktionen: Rundenturnier nach Berger je Stufe, wiederholt nach `games_per_pairing` (E134) |
| `league_table.py` | Reine Funktionen: Tabelle einer Stufe aus ihren Partien mit Feinwertung und Los; kampflose Siege zählen nicht für Feinwertung (E135) |
| `season_tables.py` | Tabellen einer gestarteten Saison aus ihren Partien, auf Wunsch nur einer Stufe (E135) |
| `season_schedule.py` | Runden einer Stufe mit Partien nach Brett und spielfreiem Bot (E138) |
| `bot_seasons.py` | Gestartete Saisons eines Bots mit seiner Tabellenzeile, Endtabelle oder aktuell (E139) |
| `season_start.py` | Fällige Saisons starten und Spielplan anlegen; wiederholbar nach einem Absturz (E132–E134); `hand_out` gibt den Partien der aktuellen Runde jeder Stufe Jobs (E189) |
| `competition_pace.py` | Takt in Ligen und Rundenturnieren: Gruppe einer Partie (Stufe einer Saison oder Ausgabe), aktuelle Runde, `due` für die Freigabe, `add_round_jobs` und `add_jobs` für Partie-Jobs (E189) |
| `season_end.py` | Saisons mit lauter beendeten Partien abschließen und die nächste nach dem Kalender anlegen (E132, E133, E135, E171) |
| `league_withdrawal.py` | Rückzug eines Bots: Anmeldungen beenden, wartende Partien kampflos werten, `sweep` je Runde (E136) |
| `recurrence.py` | Kalender `{first_start, interval_hours}` oder `None`: nächster Termin ab einem Zeitpunkt; ohne Kalender wartet die nächste Saison bzw. Ausgabe auf einen Admin (E171) |
| `withdrawal.py` | `withdraw_everywhere`: Rückzug aus allen Ligen und Turnieren beim Zurückziehen, Sperren oder Löschen (E136, E179) |
| `queue_order.py` | Abrufreihenfolge der Partien: Priorität, dann der Wettbewerb, der am längsten nicht dran war, dann Alter; `claim_match` für den Runner, `order` für die Queue-Ansicht (E134) |

### Turniere (E170–E180)

| Modul | Aufgabe |
|-------|---------|
| `tournaments.py` | Collection `tournaments`: Einstellungen je Turnier, Name eindeutig über `name_key`, archivieren statt löschen, `settings` als Schnappschuss für eine Ausgabe (E172) |
| `editions.py` | Collection `editions`: `planned → running → finished`, fällige Ausgaben, Teilnehmer mit Setzplatz, Plan in `rounds` bzw. `duels`, `revision` für Änderungen ohne Transaktion, Endstand in `final` (E173) |
| `tournament_setup.py` | Turnier mit erster Ausgabe anlegen, eine wartende Ausgabe von Hand starten, Kalender folgen (`create`, `start`, `follow_calendar`; E171, E172) |
| `edition_start.py` | Fällige Ausgaben starten: Teilnehmer aus den Anmeldungen, gesetzt nach Rating der Disziplin, Gleichstand per Los; zu wenige Teilnehmer lassen sie warten (E173–E176) |
| `edition_round_robin.py` | Plan des Rundenturniers mit allen Partien beim Start, Runden wie bei den Ligen (`league_pairing`) (E174); Jobs je Runde nach E189 |
| `swiss_pairing.py` | Reine Funktionen: Paarung einer Schweizer Runde nach Punkten und Setzplatz, ohne Wiederholung soweit möglich, Freilos an den Schwächsten ohne Freilos (E175) |
| `swiss_rounds.py` | Nächste Schweizer Runde, sobald die laufende beendet ist; Freilos zählt einen Punkt (E175) |
| `knockout_bracket.py` | Reine Funktionen: Baumgröße als nächste Zweierpotenz, erste Runde nach Setzplätzen mit Freilosen für die Besten, Platzierungen (E176) |
| `knockout_duels.py` | Partien eines Duells, Entscheidung nach regulären Partien, Tiebreak-Paaren und Armageddon (Farbe per Los, Remis reicht Schwarz), nächste Runde (E176) |
| `edition_games.py` | Fehlende Partien des Plans samt Jobs anlegen; jede geplante Partie nennt ihre Id, damit das wiederholbar ist (E174–E178); `add_jobs` gibt im Rundenturnier nur der aktuellen Runde Jobs (E189) |
| `edition_progress.py` | `advance_running`: je laufender Ausgabe fehlende Partien anlegen, Partien zurückgezogener Bots kampflos werten, Schweizer Runden und K.-o.-Duelle weiterführen, fertige Ausgaben beenden (E174–E177) |
| `edition_tables.py` | Tabelle eines Rundenturniers oder Schweizer Systems (Feinwertung wie bei Ligen plus Buchholz), Platzierungen im K.-o., Endstand mit Sieger (E177) |
| `edition_end.py` | Ausgabe abschließen und die nächste nach dem Kalender anlegen (E171, E177) |
| `tournament_withdrawal.py` | Rückzug aus Turnieren: Anmeldungen beenden, in laufenden Ausgaben als zurückgezogen markieren, wartende Partien kampflos werten (E179) |
| `bot_editions.py` | Gestartete Ausgaben einer Bot-Version mit Setzplatz, Platz oder Punkten (E180) |

### Konten und Admin

| Modul | Aufgabe |
|-------|---------|
| `users.py` | Collection `users`: Konten mit einer Rolle (`player`, `coder`, `admin`), nie gelöscht, nur deaktiviert; Fehlversuche und Sperre beim Login (E83, E84) |
| `sessions.py` | Collection `sessions`: Sitzung je Login, `_id` ist der Hash des Cookies; TTL-Index räumt ab (E84) |
| `invites.py` | Collection `invites`: Einladungslinks; `claim` reserviert atomar, `release` gibt bei Fehlschlag frei (E83) |
| `password_resets.py` | Collection `password_resets`: höchstens ein gültiger Link je Konto, `redeem` löscht ihn (E83) |
| `api_tokens.py` | Collection `api_tokens`: persönliche Tokens mit Präfix `sbm_`, höchstens 10 je Konto, Widerruf statt Löschen (E116) |
| `rate_limits.py` | Collection `rate_limits`: Zähler je Schlüssel in festen Zeitfenstern, TTL-Index räumt ab (E84) |
| `audit.py` | Collection `audit_log`: `record`, Filter und Seiten für `/admin/audit` (E85, E151) |

### Einstellungen (Collection `settings`)

| Modul | Aufgabe |
|-------|---------|
| `queue_settings.py` | Dokument `queue`: `paused`, `parallelism` (E13, E20); älteres Muster ohne `settings_document` |
| `play_settings.py` | Dokument `play`: Grenzen interaktiver Partien für `/admin/play` (E115); älteres Muster ohne `settings_document` |
| `coder_settings.py` | Dokument `coders`: Tageslimits, Partien je Anfrage, freie Zeiten, Priorität eigener Partien (E154) |
| `account_settings.py` | Dokument `accounts`: Gültigkeit von Einladungen, Fehlversuche bis zur Sperre (E154) |
| `estimate_settings.py` | Dokument `estimate`: Grundlage der Startzeit-Schätzung der Queue (E154) |
| `rating_settings.py` | Dokument `rating_rule`: die Zahlen der `RatingRule` (E154) |

### Migrationen (`migrations/`)

`migrations/__init__.py` hält die Liste `MIGRATIONS` aus `(id, apply)` in Laufreihenfolge.

| Id | Inhalt |
|----|--------|
| `0001_indexes` | Indizes für Partienliste, Bot-Historie, Queue-Abruf und Wiederaufnahme (E75) |
| `0002_reference_bots` | Referenzbots `Random` und `Material` per Upsert mit `$setOnInsert` (E68, E72) |
| `0003_accounts` | Indizes für Konten, Sitzungen, Links, Audit-Log und Rate-Limits, TTL auf `expires_at` (E83–E85) |
| `0004_uploads` | `name_key` und `version` für alte Bots, eindeutiger Index `(name_key, version_no)`, Indizes für Berichte und GridFS (E91, E94) |
| `0005_disciplines` | Eindeutiger Index auf `disciplines.name_key` (E100) |
| `0006_ratings` | Eindeutiger dünner Index auf `rating.seq`, Index für ausstehende Wertungen (E103) |
| `0007_leagues` | Indizes für Ligen, Saisons und Anmeldungen; Partie-Jobs nennen ihren Wettbewerb (E131–E136) |
| `0008_season_bots` | Index auf `tiers.entries.bot_id` von `seasons` (E139) |
| `0110_play_origin` | Dünne Indizes auf `origin.ip_key`, `origin.user_id`, `origin.token_id` (E115) |
| `0111_api_tokens` | Eindeutiger Index auf `token_hash`, Liste je Konto (E116) |
| `0150_job_matches` | Dünner Index auf `jobs.payload.match_id` (E152) |
| `0151_job_bots` | Dünner Index auf `jobs.payload.bot_id` (E153) |
| `0152_single_games` | Dünne Indizes für Serien, `created_by` und Disziplin in `matches` (E155, E156) |
| `0153_discipline_ratings` | Entfernt Index und Einzelwerte `rating`, fordert eine Neuberechnung an, falls verbuchte Partien existieren (E163) |
| `0154_tournaments` | Indizes für Turniere, Ausgaben und Partien einer Ausgabe; rechnet `pause_minutes` der Ligen in einen Kalender um und entfernt es aus Saisons (E171–E173) |
| `0155_competition_players` | `user_id` in Anmeldungen, eindeutiger Teilindex über Bot und Konto, Indizes für Konten in Saisons, Ausgaben und Partien sowie für die Bereitschaft; `ready_hours` 48 für Ligen und Turniere (E182–E185) |

## Ablauf

**Partie aus der Queue bis zur Wertung** (Aufrufer: Web-API bzw. `sbm-enqueue`, dann `services/runner`):

1. `enqueue.enqueue_match` baut die Partie mit `matches.new_match` (`rated` über `discipline.is_rated`) und speichert sie, danach den Job aus `jobs.new_match_job`.
2. Der Runner prüft `queue_settings.get(...).paused` und holt mit `queue_order.claim_match` die nächste Partie: Priorität absteigend, bei gleicher Priorität der Wettbewerb (Liga, Turnier oder alle Einzelspiele), der am längsten nicht dran war, darin die älteste (E134). Der Abruf selbst ist `jobs.claim`; er setzt `running`, Lease und `attempts + 1`.
3. `matches.start` setzt die Partie auf `running`; während des Spiels schreibt `matches.append_move` jeden Zug, `jobs.extend` verlängert die Lease. `extend` gibt `False`, wenn der Job abgebrochen wurde (E152).
4. Ende: `matches.finish`, dann `jobs.complete`. Bei Infrastrukturfehlern `matches.requeue` und `jobs.retry`, nach zu vielen Versuchen `matches.abort` und `jobs.fail`. Abgelaufene Leases räumen `jobs.expired`, `requeue_expired` und `fail_expired` auf.
5. Vor dem nächsten Job: `rating_recount.run_if_requested`, sonst `ratings.count_pending`. Dieses liest die Regel (`rating_settings.get`), repariert die zuletzt verbuchte Partie, beansprucht für die nächste die Nummer `seq` (eindeutiger Index aus `0006`) und schreibt danach beide Seiten über `rating_values`.

**Upload und Verifikation** (Aufrufer: `backend` `routes/bots.py`, dann `services/runner/.../verification`):

1. `bot_files.store_files` legt die Dateien unter der neuen `bot_id` in GridFS ab.
2. `bots.new_uploaded_bot` baut das Dokument mit `bot_files.source_hash`; `bots.insert` gibt `False`, wenn ein paralleler Upload die Versionsnummer bekam. Dann löscht `bot_files.delete_files` die Dateien wieder.
3. `jobs.new_verification_job` reiht die Prüfung ein.
4. Der Runner schaltet mit `bots.advance` durch `analyzing` und `testing`, speichert den Bericht (`verification_reports.new_report`, `insert`) und schließt mit `bots.finish_verification` ab.

## Konventionen

- **Datenbank zuerst, dict-Dokumente:** Jede Funktion nimmt `db: Database` als ersten Parameter. Collection-Namen nur über `sbm_store.names`.
- **Zeit wird übergeben:** Funktionen, die Zeit schreiben oder vergleichen, nehmen `now: datetime` als Parameter, bei Bau-Funktionen keyword-only (`new_match(..., *, now)`); der Store ruft `datetime.now` nur in `migrate.py` und in Migrationen auf. Zeiten sind timezone-aware UTC.
- **Bauen und Speichern getrennt:** `new_*` erzeugt das Dokument mit `_id`, `schema_version` und allen Feldern (ungesetzt als `None`); `insert` speichert. Optionale Felder für dünne Indizes werden weggelassen statt `None` (`matches.new_match`: `series`, `created_by`, `counted`).
- **Rückgaben statt Ausnahmen:** Ein eindeutiger Index entscheidet Wettläufe. `insert` fängt `DuplicateKeyError` und gibt `False` (`bots`, `users`, `disciplines`); Ausnahme ist `disciplines.update` mit `NameTaken`. Bedingte Updates geben `bool` aus `matched_count`/`modified_count`, `find_one_and_update` mit `ReturnDocument.AFTER` gibt das Dokument oder `None`.
- **Status im Filter:** Statuswechsel nennen den erlaubten Ausgangsstatus im Filter (`{"status": RUNNING, "worker_id": …}`), damit nur der Halter schreibt. Status und Arten sind Modulkonstanten (`jobs.QUEUED`, `bots.VERIFIED`).
- **Keine Transaktionen:** Mehrere Schreibvorgänge stehen in einer Reihenfolge, deren Zwischenstand harmlos ist oder beim nächsten Lauf repariert wird; der Docstring erklärt warum (`enqueue`, `play.create`, `bot_deletion`, `ratings`).
- **Geheimnisse nur als Hash:** Tokens über `tokens.new_token`/`token_hash`; der Klartext wird einmal zurückgegeben und nie gespeichert.
- **Namen ohne Groß-/Kleinschreibung:** eigenes Feld `*_key` (`name.lower()`) mit eindeutigem Index.
- **Unabhängig vom SDK:** Der Store hängt nur an `pymongo` (z. B. eigene `discipline.STANDARD_FEN`).
- **Docstrings:** Modul-Docstring mit Collection, Zweck und Entscheidungsnummer; Funktions-Docstrings nennen die Bedeutung von `None`/`False`.

## Erweitern

### Neue Collection oder neues Feld

1. Schema in [datenmodell.md](../komponenten/datenmodell.md) beschreiben, Entscheidung in `docs/00_entscheidungen.md` eintragen.
2. Neue Collection: Namen in `names.py` ergänzen, eigenes Modul `<thema>.py` mit `SCHEMA_VERSION`, `new_*`, `insert` und den Abfragen nach den Konventionen oben.
3. Neues Feld: in `new_*` aufnehmen. Ein optionales Feld, das Leser mit `.get` oder `$exists` behandeln, braucht keine Migration; ein Feld, nach dem gefiltert oder sortiert wird, braucht einen Index (nächster Abschnitt).
4. Lesende Projektionen prüfen, etwa `matches.SUMMARY_FIELDS` für Listen.
5. Tests unter `services/store/tests/test_<thema>.py`, danach die Aufrufer in `backend` und `services/runner` und gegebenenfalls `spec/web/openapi.json` (Spezifikation vor Code).
6. Schreibt die Web-API in die Collection, die Rechte in `deploy/mongo/users.js` ergänzen (unten).

### Neue Migration

1. Nummer wählen: M6 zählt ab `0150` (E150), als Nächstes `0154`; M7 hat `0110` ff. belegt (E110), M4 zählt unterhalb von `0110` weiter (zuletzt `0006`).
2. Datei `migrations/m0154_<thema>.py` mit Modul-Docstring (was und warum, Entscheidung) und `apply(db: Database) -> None`.
3. In `migrations/__init__.py` importieren und als `("0154_<thema>", m0154_<thema>.apply)` an die passende Stelle von `MIGRATIONS` setzen. Die Id ohne `m` wird in `schema_migrations` als `_id` gespeichert und darf sich nie ändern.
4. Reihenfolge: `migrate` überspringt nur verbuchte Ids und läuft sonst in Listenreihenfolge. Eine neu eingefügte Migration läuft auf bestehenden Datenbanken also auch dann, wenn spätere Ids schon verbucht sind. Sie darf daher nicht voraussetzen, dass spätere Migrationen noch nicht gelaufen sind.
5. Idempotent schreiben: Eine fehlgeschlagene Migration bleibt unverbucht und läuft beim nächsten `sbm-migrate` erneut. Muster: `create_indexes` mit unveränderter Definition; Upsert mit `$setOnInsert` (`0002`); Daten nur dort ändern, wo das Ziel noch fehlt (`{"name_key": {"$exists": False}}` in `0004`); Index nur löschen, wenn er existiert (`0153`). Eine geänderte Indexdefinition unter gleichem Namen erst löschen.
6. Neue Datenbanken bedenken: `0153` fordert eine Neuberechnung nur an, wenn es verbuchte Partien gibt.
7. Tests: `test_all_migrations_run_once` in `test_migrate.py` deckt die neue Id automatisch ab. Für Datenänderungen eine eigene Datei wie `test_discipline_ratings_migration.py`, die `dict(MIGRATIONS)["0154_<thema>"]` auf vorbereitete Altdaten und ein zweites Mal anwendet.
8. Migration in [datenmodell.md](../komponenten/datenmodell.md) beim passenden Stand nennen.

Auf dem Server führt `deploy/deploy.sh` nacheinander `mongo-users` und `migrate` (Nutzer `sbm_migrate`) aus, bevor die Dienste starten.

### Rechte der Mongo-Nutzer (`deploy/mongo/users.js`)

Das Skript läuft bei jedem Deploy mit dem Root-Nutzer und setzt Rollen und Passwörter neu.

| Nutzer | Rechte | Folge für Änderungen |
|--------|--------|----------------------|
| `sbm_migrate` | `readWrite`, `dbAdmin` | Darf Indizes anlegen und löschen; nichts zu tun |
| `sbm_runner` | `readWrite` | Nichts zu tun |
| `sbm_api` | `read` plus Rolle `sbm_api_writes` mit Aktionen je Collection | Neue Collection oder neue Aktion (`insert`, `update`, `remove`) in `apiWrites` eintragen, sonst scheitert die API zur Laufzeit |

Die API darf keine Indizes anlegen; deshalb legt `0004_uploads` auch die Indizes des GridFS-Buckets an. Jeder Index gehört in eine Migration. Nach einer Änderung an `users.js` die Zeile dazu in [deployment.md](../komponenten/deployment.md) nachführen.

### Neue Einstellungsgruppe

Ein Dokument in `settings` je Gruppe (E154); keine Migration und keine neuen Rechte nötig (`settings` hat für die API `insert` und `update`).

1. Entscheidung eintragen bzw. E154 erweitern; Bereiche und Standards festlegen.
2. Spezifikation zuerst: `spec/web/openapi.json` um `PUT /admin/settings/<name>` und die Gruppe im Schema `AdminSettings` erweitern; in `frontend/` `npm run api-types`.
3. Modul `sbm_store/<name>_settings.py` nach dem Muster von `estimate_settings.py`: `DOCUMENT_ID`, `LIMITS` (inklusive Bereiche je Feld), `@dataclass(frozen=True)` mit Ganzzahlen und Standards, `get` und `save` über `settings_document`, `problem` für Regeln zwischen Feldern (`None` wenn alles passt).
4. Gruppe in `GROUPS` von `services/store/tests/test_settings_groups.py` aufnehmen; die Tests prüfen Standards ohne Dokument, Standards innerhalb von `LIMITS` und gleiche Felder in `LIMITS` und Dataclass.
5. Web-API: Gruppe in `GROUPS` von `backend/src/sbm_api/settings_groups.py` eintragen, Meldungen für `problem` in `PROBLEMS`.
6. Frontend: Felder in `frontend/src/pages/admin/settingsFields.ts`, Texte in den Übersetzungsdateien.
7. Doku: Zeile `settings` in [datenmodell.md](../komponenten/datenmodell.md).

Ein neues Feld in einer bestehenden Gruppe braucht das Feld in der Dataclass, einen Eintrag in `LIMITS`, die Spezifikation (Schritt 2), das Frontend (Schritt 6) und die Doku (Schritt 7); eine neue Regel zwischen Feldern zusätzlich `problem` und `PROBLEMS`. Alte Dokumente liefern für das Feld den Standard.

`/admin/play` und die Queue nutzen das ältere Muster (`play_settings`, `queue_settings`) ohne `settings_document`; neue Gruppen folgen dem Muster oben.

## Tests

| Was | Wo |
|-----|----|
| Tests | `services/store/tests/test_<modul>.py`, meist eine Datei je Modul; dazu `test_match_interventions.py` (E152), `test_account_ratings.py`, `test_settings_groups.py`, `test_discipline_ratings_migration.py` |
| Fixture `db` | `sbm_store.testing`, als pytest-Plugin automatisch geladen: eine Datenbank `sbm_test_<zufall>` je Test, danach gelöscht |
| Fixture `reference_bots` | `tests/conftest.py`: migriert und gibt `Random` und `Material`; dort auch `START_FEN`, `BLITZ` und die feste Uhr `T0` |
| `keep_expired` | `sbm_store.testing`: setzt TTL-Indizes auf den Höchstwert, damit MongoDB Dokumente mit Zeiten der festen Testuhr nicht löscht; genutzt in `backend/tests/conftest.py` |

Ausführen aus dem Repo-Wurzelverzeichnis:

- Test-MongoDB: `docker run -d --name sbm-test-mongo -p 127.0.0.1:27017:27017 mongo:8.0`
- `pytest services/store`; Lint `ruff check services/store` und `ruff format --check services/store`

Ohne erreichbaren Server (`SBM_TEST_MONGO_URI`, Standard `mongodb://localhost:27017`) überspringt `mongo_uri` alle Tests mit `db`; mit `SBM_REQUIRE_MONGO=1` scheitern sie, so in CI im Job `services`. Reine Logik wie `rating_rule`, `versions` oder die `LIMITS`-Prüfung läuft ohne Datenbank. Tests nutzen eine feste Uhr und übergeben sie als `now`.
