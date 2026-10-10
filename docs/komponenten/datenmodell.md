# Datenmodell (MongoDB)

## Collections

| Collection | Inhalt | Wichtige Felder |
|------------|--------|-----------------|
| `users` | Accounts (E83) | `username`, `username_key`, `password_hash`, `role`, `active`, `invited_by`, `failed_logins`, `locked_until`, `created_at`, `last_login_at` |
| `sessions` | Angemeldete Browser (E84) | `_id` = Hash des Tokens, `user_id`, `created_at`, `expires_at` |
| `invites` | Einladungen (E4, E83) | `token_hash`, `role`, `created_by`, `created_by_name`, `created_at`, `expires_at`, `used_by`, `used_at` |
| `password_resets` | Links für ein neues Passwort (E83) | `token_hash`, `user_id`, `created_by`, `created_at`, `expires_at` |
| `rate_limits` | Zähler für Anmeldeversuche je Client-Adresse (E84) | `_id` = Schlüssel, `count`, `expires_at` |
| `api_tokens` | Tokens für Remote-Bots | `user_id`, `token_hash`, `name`, `last_used_at`, `revoked` |
| `bots` | Ein Dokument je Bot-Version (E6) | `owner_id`, `name`, `name_key`, `version`, `language`, `lineage_id`, `parent_bot_id`, `version_no`, `status`, `sdk_version`, `runtime_version`, `source_ref`, `artifact_ref`, `entry`, `files[]`, `source_hash`, `sizes`, `report_id`, `rejection`, `created_at`, `verified_at`, `rejected_at` |
| `verification_reports` | Ergebnis der Pipeline | `bot_id`, `job_id`, `result`, `stages[]` (Status, Befunde bzw. Testpartien, Dauer), `ruleset`, `runtime` (Versionen von Python und SDK), `started_at`, `finished_at` |
| `disciplines` | Disziplin-Konfiguration | siehe [ligen-turniere.md](ligen-turniere.md) |
| `settings` | Systemweite Einstellungen (E13) | Queue-Parallelität, Pausen/Zeitfenster, Standardprioritäten, Kapazitätsgrenzen für Mensch-/Remote-Spiele |
| `leagues` | Liga-Konfiguration | `discipline_id`, `tiers[]`, `promotion`, `relegation`, `recurrence`, `tiebreaks[]` |
| `seasons` | Eine Saison einer Liga | `league_id`, `number`, `status`, `discipline_snapshot`, `starts_at`, `ends_at` |
| `standings` | Tabellenzeile je Bot, Saison, Stufe/Gruppe | `season_id`, `tier`, `group`, `bot_id`, `played`, `wins`, `draws`, `losses`, `points`, `tiebreak_values`, `forfeit_wins`, `final_rank`, `outcome` (promoted/relegated/stayed/withdrawn) |
| `tournaments` | Turnier inkl. Konfiguration und Zustand | `format`, `discipline_snapshot`, `status`, `rounds[]`, `bracket`, `recurrence_id` |
| `registrations` | Anmeldung Bot ↔ Liga/Turnier | `bot_id`, `target_type`, `target_id`, `status`, `created_at` |
| `matches` | Eine Partie | siehe unten |
| `jobs` | Queue (A8) | `type`, `payload`, `priority`, `status`, `not_before`, `lease_until`, `worker_id`, `attempts` |
| `audit_log` | Admin- und sicherheitsrelevante Aktionen | `actor_id`, `action`, `target`, `at`, `details` |

Große Binärdaten (Quelldateien, Artefakte, Bot-Logs) liegen in GridFS in derselben Datenbank (E82); die Dokumente halten nur Referenzen und Hashes.

## `matches`

```json
{
  "_id": "...",
  "type": "league | tournament | single | human | remote | verification",
  "context": { "season_id": "...", "tier": 3, "round": 4 },
  "discipline_snapshot": { "...": "..." },
  "white": { "kind": "bot | human | remote", "bot_id": "...", "user_id": null, "seat_hash": "…" },
  "black": { "kind": "bot", "bot_id": "..." },
  "status": "queued | running | finished | forfeited | aborted",
  "queue": { "priority": 100, "position": 7, "estimated_start": "..." },
  "rated": true,
  "start_fen": "startpos",
  "moves": [
    { "ply": 1, "uci": "e2e4", "san": "e4", "fen": "...", "spent_ms": 812, "clock_ms": 1799188, "info": { "depth": 6, "score_cp": 23 } }
  ],
  "result": "1-0 | 0-1 | 1/2-1/2 | *",
  "termination": "checkmate | timeout | illegal_move | forfeit_withdrawn | ...",
  "scheduled_at": "...", "started_at": "...", "finished_at": "...",
  "logs": { "white_ref": "...", "black_ref": "..." }
}
```

- Züge eingebettet: Eine Partie liegt mit wenigen hundert Halbzügen weit unter dem Dokumentlimit von 16 MB; die maximale Zugzahl der Disziplin sichert das ab.
- `fen` pro Zug macht den Viewer unabhängig von einer eigenen Regelimplementierung und erlaubt direkte Sprünge.
- **Kampflose Siege (E17)** sind eigene Match-Dokumente mit `status: forfeited`, leerer Zugliste, `rated: false` und `termination: forfeit_withdrawn`; so bleiben sie in Tabelle und Partienliste sichtbar und unterscheidbar.
- `termination` nutzt die Codes aus [bot-protokoll.md](bot-protokoll.md) (E44), ergänzt um `forfeit_withdrawn`.
- `discipline_snapshot` hält fest, unter welchen Bedingungen gespielt wurde, auch wenn die Disziplin später geändert wird.

## Indizes

| Collection | Index | Zweck |
|------------|-------|-------|
| `matches` | `white.bot_id + finished_at`, `black.bot_id + finished_at` | Bot-Historie |
| `matches` | `context.season_id + context.round`, `status + queue.priority` | Spielpläne, laufende Spiele, Queue-Ansicht |
| `standings` | `season_id + tier + group + points` (unique auf `season_id + bot_id`) | Tabellen |
| `bots` | unique `name_key + version_no`, `owner_id + created_at`, `lineage_id + version_no`, `status` | Namen und Versionen (E91), eigene Bots, Versionslisten |
| `verification_reports` | `bot_id` | Reports eines Bots |
| `jobs` | `status + priority + not_before`, `lease_until` | Queue-Abruf, Wiederaufnahme |
| `registrations` | unique `bot_id + target_type + target_id` | Keine Doppelanmeldung |
| `users` | unique `username_key` | Login, Namen ohne Rücksicht auf Groß- und Kleinschreibung eindeutig |
| `invites`, `password_resets`, `api_tokens` | unique `token_hash`; TTL auf `expires_at` | Lookup, Aufräumen |
| `sessions`, `rate_limits` | TTL auf `expires_at` | Aufräumen |
| `audit_log` | `at` absteigend | Neueste Einträge zuerst |

## Stand M2 (E75)

- Zugriff nur über das Paket `sbm-store` (`services/store`). Angelegt sind `bots`, `matches`, `jobs`, `settings` (Dokument `queue` mit `paused`, `parallelism`) und `schema_migrations`.
- Migrationen laufen mit `sbm-migrate` und sind idempotent: `0001_indexes` legt die Indizes für Partienliste, Bot-Historie, Queue-Abruf und Wiederaufnahme an, `0002_reference_bots` die Referenzbots `Random` und `Material` (E72).
- Ein Match enthält zusätzlich `termination_detail` (Erklärung des Endes, nur intern) und `schema_version`; ein Job hält die Match-ID in `payload.match_id`.
- Alle Zeitstempel sind UTC.

## Stand M3, Schritt 1 (E83–E85)

- Neu sind `users`, `sessions`, `invites`, `password_resets`, `rate_limits` und `audit_log`, je mit einem Modul in `sbm-store`; Tokens hasht `sbm_store.tokens` (SHA-256).
- `0003_accounts` legt ihre Indizes an, darunter die TTL-Indizes, die abgelaufene Sitzungen, Links und Zähler löschen.
- Ein Konto hat genau eine Rolle (`coder` oder `admin`) statt einer Liste und kein E-Mail-Feld (E83).
- `settings` bekommt das Dokument `queue` beim ersten Pausieren über die Website, falls es fehlt.

## Stand M3, Schritt 3 (E89–E94)

- Ein hochgeladener Bot hat `name_key` (Name in Kleinbuchstaben), `version` (`X.Y.Z` des Besitzers, E91), `entry`, `files[]` (`path`, `kind` `source` oder `data`, `size`, `sha256`, `file_id`), `source_hash` und `sizes` je Art. `source_ref` ist `gridfs`; die Dateien liegen im Bucket `bot_files` (`sbm_store.bot_files`, E94).
- Nach der Verifikation verweist `report_id` auf den Report, `rejection` hält Stufe und Grund einer Ablehnung; `sdk_version` und `runtime_version` kommen aus der Selbstprüfung des Runners.
- `verification_reports` (`sbm_store.verification_reports`) mit `result` `passed` oder `failed`; je Stufe die Befunde der Analyse oder die Testpartien.
- Ein Job hat `type` `match` (`payload.match_id`) oder `verification` (`payload.bot_id`, E89).
- `0004_uploads` setzt bei vorhandenen Bots `name_key` und `version` `1.0.0`, legt die Indizes von `bots` und `verification_reports` an und die von GridFS für `bot_files`, weil die API sie nicht anlegen darf.
- Die Versionsnummern prüft und vergleicht `sbm_store.versions`.

## Stand M3, Schritt 4 (E95–E98)

- Ein Bot hat `description` (reiner Text, höchstens 500 Zeichen; bei älteren Bots fehlt das Feld und gilt als leer) und kann den Status `retired` haben (E96).
- Eine Seite einer Partie hält `version` des Bots (E95); ältere Partien haben dort nichts, die API liefert `null`.
- `rate_limits` zählt Partien durch Coder unter `matches:{user_id}` je Tag (E98); `sbm_store.rate_limits.hit` zählt dafür mehrere auf einmal, `give_back` nimmt eine abgelehnte Anfrage zurück.
- Keine Migration nötig: Die neuen Felder sind optional.

## Stand M4, Schritt 1 (E100)

- Neu ist `disciplines` (`sbm_store.disciplines`) mit `name`, `name_key` (Name in Kleinbuchstaben), `initial_time_ms`, `increment_ms`, `startup_ms`, `tolerance_ms`, `max_moves`, `archived`, `created_by`, `created_at`, `updated_at` und `schema_version`.
- `0005_disciplines` legt den eindeutigen Index auf `name_key` an.
- `discipline_snapshot` einer Partie hält zusätzlich `discipline_id` (`null` bei freien Zeiten), die Partie `rated`. Ältere Partien haben beides nicht; die API liefert `null` und `false`.

## Stand M4, Schritt 2 (E103, E104)

- Keine eigene Sammlung für Ratings. Ein Bot hält `rating` mit `value`, `games` und `seq` der zuletzt übernommenen Partie; ohne das Feld steht er bei 2500 und 0 Partien. Konten (`users`) halten dasselbe Feld für ihre gewerteten Partien gegen Bots (E117); die Rangliste der Spieler liest es ohne eigenen Index, weil es nur wenige Konten gibt (E118).
- Eine verbuchte Partie hält `rating` mit `seq` und je Seite `before`, `after` und `games`; darin steckt der Verlauf (`sbm_store.ratings`, Regel in `sbm_store.rating_rule`).
- `0006_ratings` legt den eindeutigen Teilindex auf `rating.seq`, einen Index für die offenen Partien (`status`, `rated`, `finished_at`) und einen auf `rating.value` der Bots an.
- Eine Partie eines Bots gegen sich selbst ist nie `rated`.

## Endgültiges Löschen (E105)

- `sbm_store.bot_deletion` entfernt eine Version mit Dateien (`bot_files`), Prüfberichten, Verifikationsjobs und allen ihren Partien samt deren Jobs; der Bot-Eintrag geht zuletzt.
- `settings` mit `_id` `ratings` hält `recount_request` (eine frische `ObjectId` je Anforderung, sonst `null`) und `requested_at`. `sbm_store.rating_recount` entfernt `rating` von allen Partien, Bots und Konten und verbucht neu; die Anforderung wird nur gelöscht, wenn keine neue dazukam.

## Stand M7 (E113–E116)

- Interaktive Partien: Typ `human` oder `remote`, `queue` ist `null`, `rated` nur für einen Menschen mit Konto unter einer gespeicherten Disziplin aus der Grundstellung (E117). Eine Seite ohne Bot hat `kind` `human` oder `remote`, `bot_id` `null`, `user_id` (bei Gästen `null`), `name` und `seat_hash` (SHA-256 des Sitz-Tokens; der Token selbst wird nie gespeichert). `origin` hält `ip_key` (Hash der Adresse), `user_id` und `token_id` für die Grenzen; dünn besetzte Indizes darauf (Migration `0110_play_origin`). Ihr Job hat die Art `play` (`sbm_store.play`). Öffentlich sind sie wie Botpartien (E119); die Liste der laufenden nutzt den vorhandenen Index auf `status`.
- `settings`: Dokument `play` mit `max_games`, `games_per_client`, `games_per_day` (`sbm_store.play_settings`, E115).
- `api_tokens`: `user_id`, `name`, `token_hash` (eindeutig), `created_at`, `last_used_at`, `revoked_at` (`sbm_store.api_tokens`, Migration `0111_api_tokens`, E116).
- `users.role` kennt zusätzlich `player` (E103, E115).

## Stand M6 (E150–E169)

- `jobs.status` kennt zusätzlich `cancelled`: Ein Admin hat die Partie abgebrochen (E152). `lease_until` wird geleert, `finished_at` gesetzt; ein Runner, der den Job hielt, kann ihn nicht mehr verlängern.
- Migration `0150_job_matches` legt einen dünn besetzten Index auf `payload.match_id` von `jobs` an, für Abbrechen und Ändern der Priorität (`sbm_store.jobs.cancel_match`, `set_match_priority`); `sbm_store.matches.set_priority` hält `queue.priority` der Partie gleich.
- Neuprüfung und Override (E153): Ein Job der Art `verification` mit `payload.recheck: true` prüft einen Bot erneut (`sbm_store.rechecks`). `verification_reports.kind` ist `upload` oder `recheck`; Berichte ohne `kind` stammen aus Uploads. `bots.overridden_at` hält fest, wann ein Admin einen abgelehnten Bot verifiziert hat. Migration `0151_job_bots` legt einen dünn besetzten Index auf `payload.bot_id` von `jobs` an.

## Zu beachten

- **Tabellen sind abgeleitete Daten.** Sie müssen jederzeit aus `matches` neu berechenbar sein (Reparaturwerkzeug für Admins).
- **Atomarität:** Job-Abruf per atomarem Update (`find_one_and_update`). Ergebnisverbuchung + Tabellenupdate entweder in einer Transaktion (erfordert Replica Set) oder idempotent über ein „verbucht“-Kennzeichen am Match.
- **Replica Set:** Auch ein Einzelknoten kann als Replica Set laufen; nötig für Transaktionen und Change Streams.
- **Schema-Versionierung:** Feld `schema_version` pro Dokument und Migrationsskripte im Repo.
- **Löschen:** Nutzer und Bots werden deaktiviert statt gelöscht, damit die Spielhistorie konsistent bleibt; personenbezogene Felder müssen separat entfernbar sein.
- **Backups:** siehe [deployment.md](deployment.md).
