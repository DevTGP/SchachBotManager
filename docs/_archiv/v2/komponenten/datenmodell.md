# Datenmodell (MongoDB)

## Collections

| Collection | Inhalt | Wichtige Felder |
|------------|--------|-----------------|
| `users` | Accounts | `username`, `email`, `password_hash`, `roles[]`, `status`, `created_at` |
| `invites` | Einladungen (E4) | `token_hash`, `role`, `created_by`, `expires_at`, `used_by`, `used_at` |
| `api_tokens` | Tokens für Remote-Bots | `user_id`, `token_hash`, `name`, `last_used_at`, `revoked` |
| `bots` | Ein Dokument je Bot-Version (E6) | `owner_id`, `name`, `language`, `lineage_id`, `parent_bot_id`, `version_no`, `status`, `sdk_version`, `runtime_version`, `source_ref`, `artifact_ref`, `source_hash`, `sizes`, `created_at` |
| `verification_reports` | Ergebnis der Pipeline | `bot_id`, `stages[]` (Status, Meldungen, Dauer), `ruleset_version` |
| `disciplines` | Disziplin-Konfiguration | siehe [ligen-turniere.md](ligen-turniere.md) |
| `settings` | Systemweite Einstellungen (E13) | Queue-Parallelität, Pausen/Zeitfenster, Standardprioritäten, Kapazitätsgrenzen für Mensch-/Remote-Spiele, Sandbox-Obergrenzen |
| `leagues` | Liga-Konfiguration | `discipline_id`, `tiers[]`, `promotion`, `relegation`, `recurrence`, `tiebreaks[]` |
| `seasons` | Eine Saison einer Liga | `league_id`, `number`, `status`, `discipline_snapshot`, `starts_at`, `ends_at` |
| `standings` | Tabellenzeile je Bot, Saison, Stufe/Gruppe | `season_id`, `tier`, `group`, `bot_id`, `played`, `wins`, `draws`, `losses`, `points`, `tiebreak_values`, `forfeit_wins`, `final_rank`, `outcome` (promoted/relegated/stayed/withdrawn) |
| `tournaments` | Turnier inkl. Konfiguration und Zustand | `format`, `discipline_snapshot`, `status`, `rounds[]`, `bracket`, `recurrence_id` |
| `registrations` | Anmeldung Bot ↔ Liga/Turnier | `bot_id`, `target_type`, `target_id`, `status`, `created_at` |
| `matches` | Eine Partie | siehe unten |
| `ratings` | Rating je Bot und Disziplin | `bot_id`, `discipline_id`, `value`, `deviation`, `games`, `history[]` (gekürzt) |
| `jobs` | Queue (A8) | `type`, `payload`, `priority`, `status`, `not_before`, `lease_until`, `worker_id`, `attempts` |
| `audit_log` | Admin- und sicherheitsrelevante Aktionen | `actor_id`, `action`, `target`, `at`, `details` |

Große Binärdaten (Quellcode-Archive, Artefakte, Bot-Logs) liegen im Artefakt-Speicher (GridFS oder Volume); die DB hält nur Referenzen und Hashes.

## `matches`

```json
{
  "_id": "...",
  "type": "league | tournament | single | human | remote | verification",
  "context": { "season_id": "...", "tier": 3, "round": 4 },
  "discipline_snapshot": { "...": "..." },
  "white": { "kind": "bot | human | remote", "bot_id": "...", "user_id": null },
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
- `discipline_snapshot` hält fest, unter welchen Bedingungen gespielt wurde, auch wenn die Disziplin später geändert wird.

## Indizes

| Collection | Index | Zweck |
|------------|-------|-------|
| `matches` | `white.bot_id + finished_at`, `black.bot_id + finished_at` | Bot-Historie |
| `matches` | `context.season_id + context.round`, `status + queue.priority` | Spielpläne, laufende Spiele, Queue-Ansicht |
| `standings` | `season_id + tier + group + points` (unique auf `season_id + bot_id`) | Tabellen |
| `bots` | `owner_id`, `lineage_id + version_no`, `status` | Verwaltung, Versionslisten |
| `jobs` | `status + priority + not_before`, `lease_until` | Queue-Abruf, Wiederaufnahme |
| `registrations` | unique `bot_id + target_type + target_id` | Keine Doppelanmeldung |
| `users` | unique `username`, unique `email` | Login |
| `invites`, `api_tokens` | unique `token_hash`; TTL auf `expires_at` | Lookup, Aufräumen |

## Zu beachten

- **Tabellen sind abgeleitete Daten.** Sie müssen jederzeit aus `matches` neu berechenbar sein (Reparaturwerkzeug für Admins).
- **Atomarität:** Job-Abruf per atomarem Update (`find_one_and_update`). Ergebnisverbuchung + Tabellenupdate entweder in einer Transaktion (erfordert Replica Set) oder idempotent über ein „verbucht“-Kennzeichen am Match.
- **Replica Set:** Auch ein Einzelknoten kann als Replica Set laufen; nötig für Transaktionen und Change Streams.
- **Schema-Versionierung:** Feld `schema_version` pro Dokument und Migrationsskripte im Repo.
- **Löschen:** Nutzer und Bots werden deaktiviert statt gelöscht, damit die Spielhistorie konsistent bleibt; personenbezogene Felder müssen separat entfernbar sein.
- **Backups:** siehe [deployment.md](deployment.md).
