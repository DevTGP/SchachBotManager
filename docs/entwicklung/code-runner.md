# Code-Karte: sbm_runner

Der Runner unter `services/runner` (Paket `sbm-runner`, Modul `sbm_runner`) spielt Partien aus der Queue, verifiziert hochgeladene Bots und spielt in der Rolle `play` interaktive Partien. Befehle: `sbm-runner` und `sbm-enqueue`. Konzepte: [match-runner.md](../komponenten/match-runner.md), [sandbox.md](../komponenten/sandbox.md), [verifikation.md](../komponenten/verifikation.md), [gateway.md](../komponenten/gateway.md).

## Einstieg

| Befehl | Einstieg | Aufgabe |
|--------|----------|---------|
| `sbm-runner` | `sbm_runner.cli:main` | Liest die Umgebung, startet die Sandbox und dann `Worker` (Rolle `queue`) oder `PlayWorker` (Rolle `play`) |
| `sbm-enqueue` | `sbm_runner.enqueue_cli:main` | Reiht Partien zwischen Bots nach Namen ein (Entwicklungswerkzeug, E71) |

`cli.main` wählt die Rolle über `SBM_RUNNER_ROLE` (E111). Bei `SBM_SANDBOX=none` gibt `start_sandbox` `None` zurück; dann ist `plain_player` die Spielerfabrik und der Queue-Worker hat keinen `verifier`. Mit `nsjail` ist `Sandbox.player` die Fabrik und die `Sandbox` zugleich der `Verifier`. Ein `ValueError` oder `SandboxBroken` beim Start ergibt Exit-Code 1.

Lesereihenfolge:

1. `cli.py` – Rollen, Sandbox, Spielerfabrik.
2. `worker.py` – Hauptschleife des Queue-Runners: Wiederaufnahme, Ratings, Ligen, Abruf, Arbeit.
3. `game.py` mit `match_settings.py`, `recorder.py`, `players.py` – eine Partie.
4. `heartbeat.py`, `stopper.py`, `retries.py`, `recovery.py`, `shutdown.py` – Leases und Fehlerfälle.
5. `verification/pipeline.py` – ein Verifikationsjob.
6. `sandbox/jail.py`, dann `sandbox/jail_player.py` und `sandbox/cgroup.py` – wie ein Bot eingesperrt wird.
7. `play/worker.py`, `play/game.py`, `play/relay_connection.py` – der Play-Runner.

## Module

### Hauptpaket `sbm_runner/`

| Modul | Aufgabe |
|-------|---------|
| [`__init__.py`](../../services/runner/src/sbm_runner/__init__.py) | Paketbeschreibung |
| [`cli.py`](../../services/runner/src/sbm_runner/cli.py) | `sbm-runner`: Logging, Signal-Handler, Rolle `queue`/`play`, Start der Sandbox |
| [`config.py`](../../services/runner/src/sbm_runner/config.py) | `RunnerConfig`: Abfrage-Intervall, Lease, Heartbeat, `max_attempts`, `retry_delay`, `verification_wait` (E89); `default_worker_id` |
| [`enqueue_cli.py`](../../services/runner/src/sbm_runner/enqueue_cli.py) | `sbm-enqueue`: baut eine `Discipline`, prüft sie mit `MatchSettings` des Referees und ruft `sbm_store.enqueue.enqueue_match` |
| [`worker.py`](../../services/runner/src/sbm_runner/worker.py) | `Worker`: ein Job nach dem anderen; je Runde zuerst `advance_leagues`; Abrufreihenfolge alte Verifikation → Partie (über `sbm_store.queue_order.claim_match`: höchste Priorität, Wettbewerbe abwechselnd, E134) → Verifikation (E89); Ratings nach jeder Partie (E103), Neuberechnung vor dem Abruf (E105); `utc_now` |
| [`league_tick.py`](../../services/runner/src/sbm_runner/league_tick.py) | `advance_leagues`: je Runde Spielplan nach Absturz neu anlegen, Partien zurückgezogener Bots kampflos werten, fertige Saisons beenden, fällige starten (E132–E136); ein Fehler wird geloggt und hält den Runner nicht an |
| [`game.py`](../../services/runner/src/sbm_runner/game.py) | `run_job`: spielt die Partie eines Jobs mit dem Referee und speichert das Ergebnis; `bot_player` lässt nur Bots in `verified` spielen |
| [`match_settings.py`](../../services/runner/src/sbm_runner/match_settings.py) | `MatchSettings` des Referees aus `discipline_snapshot` und `start_fen` einer gespeicherten Partie |
| [`players.py`](../../services/runner/src/sbm_runner/players.py) | `PlayerFactory`, `UnsupportedBot`, erlaubte Referenzbots (`BUILTIN_MODULES`), `plain_player`/`PlainPlayer` ohne Sandbox (E72) |
| [`recorder.py`](../../services/runner/src/sbm_runner/recorder.py) | `Recorder.on_move`: schreibt jeden Zug sofort in die Partie (`matches.append_move`) |
| [`checkout.py`](../../services/runner/src/sbm_runner/checkout.py) | Frische Kopie der Dateien eines Uploads aus GridFS unter `/tmp/sbm-bots`, mit erneuter Prüfung von Pfad, Art, Größe und SHA-256 (E94); `BotDir` |
| [`heartbeat.py`](../../services/runner/src/sbm_runner/heartbeat.py) | `Heartbeat`: verlängert die Lease im eigenen Thread; ruft `on_lost`, wenn der Job nicht mehr gehalten wird (E152) |
| [`stopper.py`](../../services/runner/src/sbm_runner/stopper.py) | `Stopper`: beendet die Spieler einer Partie aus dem Heartbeat-Thread, auch später hinzugefügte |
| [`retries.py`](../../services/runner/src/sbm_runner/retries.py) | `retry_or_abort` (Partie) und `retry_or_reject` (Verifikation) nach einem Infrastrukturfehler |
| [`recovery.py`](../../services/runner/src/sbm_runner/recovery.py) | `recover_expired`: gibt Jobs toter Worker frei oder gibt sie nach `max_attempts` auf |
| [`shutdown.py`](../../services/runner/src/sbm_runner/shutdown.py) | `Shutdown` (von `BaseException`) und `install_handlers` für SIGTERM/SIGINT |

### Sandbox `sbm_runner/sandbox/` (E86)

| Modul | Aufgabe |
|-------|---------|
| [`__init__.py`](../../services/runner/src/sbm_runner/sandbox/__init__.py) | Paketbeschreibung |
| [`settings.py`](../../services/runner/src/sbm_runner/sandbox/settings.py) | `SandboxSettings` aus `SBM_SANDBOX` (`nsjail` oder `none`); Pfade zu nsjail, Konfiguration und leerem Bot-Verzeichnis |
| [`limits.py`](../../services/runner/src/sbm_runner/sandbox/limits.py) | Feste Grenzen je Bot: 1024 MiB, 128 Prozesse, 4096 Byte stderr-Ende (A14) |
| [`cgroup_tree.py`](../../services/runner/src/sbm_runner/sandbox/cgroup_tree.py) | `CgroupTree.prepare`: cgroup-v2-Baum beschreibbar machen, Runner nach `runner/`, Controller `memory` und `pids` für `bots/`, Reste entfernen; `create` legt die cgroup eines Bots an |
| [`cgroup.py`](../../services/runner/src/sbm_runner/sandbox/cgroup.py) | `BotCgroup`: Grenzen setzen, `enter` (Shell schreibt sich in `cgroup.procs`), `freeze`/`thaw`, `kill`, `oom_killed` |
| [`jail.py`](../../services/runner/src/sbm_runner/sandbox/jail.py) | `Sandbox`: `prepare` mit Selbstprüfung (Versionen in `runtime`), `player` je Bot, `script_player`, `analyze` (`sbm.analysis` im Jail), `checkout`; `SandboxBroken` |
| [`jail_player.py`](../../services/runner/src/sbm_runner/sandbox/jail_player.py) | `JailPlayer`: Bot über nsjail in eigener cgroup, außerhalb des Zuges eingefroren; `exited_cleanly`, `stderr_bytes`; OOM ergibt `memory_limit` |
| [`run_once.py`](../../services/runner/src/sbm_runner/sandbox/run_once.py) | `run_once`: Befehl im Jail bis zum Ende mit Zeitlimit; `Completed` (`returncode` `None` bei Zeitüberschreitung) |
| [`stderr_tail.py`](../../services/runner/src/sbm_runner/sandbox/stderr_tail.py) | `StderrTail`: liest stderr in einem Thread leer, behält das Ende und zählt alle Bytes |

Zur Sandbox gehören außerhalb des Pakets [`sandbox/python.cfg`](../../sandbox/python.cfg) (nsjail-Konfiguration) und [`sandbox/python.policy`](../../sandbox/python.policy) (seccomp-Whitelist in kafel-Syntax). Das Runner-Image kopiert sie nach `/opt/sbm/sandbox` (`deploy/python.Dockerfile`, Ziel `runner`).

### Verifikation `sbm_runner/verification/` (E92)

| Modul | Aufgabe |
|-------|---------|
| [`__init__.py`](../../services/runner/src/sbm_runner/verification/__init__.py) | Paketbeschreibung |
| [`pipeline.py`](../../services/runner/src/sbm_runner/verification/pipeline.py) | `run_verification`: Checkout, Stufe Analyse, Stufe Mindesttests, Report, `verified`/`rejected`; Neuprüfung schreibt nur einen Report (E153); Protokoll `Verifier` |
| [`analysis_stage.py`](../../services/runner/src/sbm_runner/verification/analysis_stage.py) | Prüft die Ausgabe des Analysators streng und macht daraus die Stufe `analysis` (60 s, höchstens 1 MiB) |
| [`minimum_tests.py`](../../services/runner/src/sbm_runner/verification/minimum_tests.py) | `TEST_GAMES` gegen den eingesperrten Random-Bot (Stellungen, zwei Partien, Zeitnot); `play_test` bewertet Schuld, sauberes Ende und stderr-Menge |
| [`rejection.py`](../../services/runner/src/sbm_runner/verification/rejection.py) | `reject_internal`: Report mit Stufe `internal` und Ablehnung, wenn der Server nicht prüfen konnte |

### Play-Runner `sbm_runner/play/` (E111–E116)

| Modul | Aufgabe |
|-------|---------|
| [`__init__.py`](../../services/runner/src/sbm_runner/play/__init__.py) | Paketbeschreibung |
| [`config.py`](../../services/runner/src/sbm_runner/play/config.py) | `PlayConfig` aus `SBM_RELAY_ADDRESS`, `SBM_PLAY_SLOTS`, `SBM_WORKER_ID`; Wartezeiten für Sitze, Abwesenheit, Relay und Stopp |
| [`worker.py`](../../services/runner/src/sbm_runner/play/worker.py) | `PlayWorker`: bis `min(slots, max_games)` Partien in eigenen Threads mit eigenem Heartbeat; `recover_expired_play`, `count_ratings` |
| [`game.py`](../../services/runner/src/sbm_runner/play/game.py) | `InteractiveGame`: Seiten aufbauen, auf Sitze warten, spielen, speichern; jeder Fehler bricht ab statt zu wiederholen (E113) |
| [`relay_connection.py`](../../services/runner/src/sbm_runner/play/relay_connection.py) | `RelayConnection`: TCP-Verbindung eines Sitzes zum Gateway (relay-v1), Lesethread, `present`/`absent`; `RelayClosed`, `SeatAbandoned` |
| [`relay_player.py`](../../services/runner/src/sbm_runner/play/relay_player.py) | `RelayPlayer`: Remote-Bot, Zeilen des Bot-Protokolls v1 unverändert (E116) |
| [`human_player.py`](../../services/runner/src/sbm_runner/play/human_player.py) | `HumanPlayer`: übersetzt zwischen Referee und Browser (play-v1), legale Züge aus dem Kern, Stand erneut nach Neuladen (E114) |

## Ablauf

### Partie aus der Queue

1. `Worker.step` ruft `recover_expired` (`recovery.py`), `_recount_ratings` und `advance_leagues` (`league_tick.py`); ist die Queue pausiert (`queue_settings`), endet der Schritt.
2. `Worker._claim` holt eine Partie per `sbm_store.queue_order.claim_match` (höchste Priorität; bei Gleichstand der Wettbewerb mit dem ältesten `claimed_at`, darin die älteste Partie, E134), eine Verifikation per `sbm_store.jobs.claim`. Um ihn laufen `Heartbeat` und `Stopper`.
3. `game.run_job` lädt die Partie, setzt eine von einem toten Worker hinterlassene `running`-Partie zurück und baut beide Spieler über `bot_player` und die `PlayerFactory`.
4. Für einen hochgeladenen Bot ruft `Sandbox.player` beim Start des `JailPlayer` `checkout.checkout`: frische Kopie aus GridFS, die nsjail als `/bot` einhängt. Referenzbots bekommen das leere Verzeichnis `no_files`.
5. `JailPlayer.start` legt über `CgroupTree.create` die cgroup an und startet `sh` → nsjail → `python3` mit `SBM_BOT_DIR`.
6. `matches.start` setzt die Partie auf `running`; dann spielt `sbm.referee.Match` mit `match_settings(match)`. `suspend`/`resume` des `JailPlayer` frieren die cgroup ein und tauen sie auf.
7. `Recorder.on_move` schreibt jeden Zug sofort.
8. `_store_result` ruft `matches.finish`, danach `jobs.complete`. `JailPlayer.close` beendet die cgroup und löscht die Kopie.
9. `Worker._count_ratings` verbucht alle offenen gewerteten Partien (`ratings.count_pending`).

Fehler: Eine Ausnahme aus `run_job` geht an `retry_or_abort`. `UnsupportedBot` bricht sofort ab. Verliert der Heartbeat den Job, stoppt der `Stopper` die Bots und `run_job` speichert nichts. `Shutdown` setzt Partie und Job zurück (`jobs.release`), ohne den Versuch zu zählen.

### Verifikationsjob

1. `Worker._claim` nimmt einen Job `verification`, wenn ein `verifier` da ist.
2. `pipeline.run_verification` lädt den Bot; ein nicht neu zu prüfender Bot außerhalb von `bots.PIPELINE` schließt nur den Job.
3. `Verifier.checkout` kopiert die Dateien einmal für alle Stufen.
4. `_stages`: `bots.advance(ANALYZING)`, `Sandbox.analyze` (`run_once` mit `python -I -m sbm.analysis --json`), `analysis_stage` bewertet die Ausgabe.
5. Bei Erfolg `bots.advance(TESTING)` und `_tests_stage`: je Testpartie ein neuer `script_player` gegen `RANDOM`, Abbruch beim ersten Fehlschlag.
6. `verification_reports.insert` speichert den Report; `bots.finish_verification` setzt `verified` oder `rejected` (E93). Bei einer Neuprüfung nur der Report (E153).

Fehler: `retry_or_reject`; nach `max_attempts` `reject_internal`. Bei `Shutdown` gibt der Worker den Job frei.

### Interaktive Partie (Rolle `play`)

1. `PlayWorker.step` räumt beendete Threads ab, gibt abgelaufene Play-Jobs auf (`recover_expired_play`, Abbruch der Partie) und prüft die freien Plätze.
2. `jobs.claim` mit `play.PLAY_JOB`; je Job ein Thread mit `Heartbeat` um `InteractiveGame.run`.
3. `InteractiveGame.run` bricht eine Partie ab, die nicht mehr `queued` ist. Je Seite: Bot über `bot_player`, sonst `RelayConnection.open` (`attach`) und `RelayPlayer` (Art `remote`) oder `HumanPlayer` (Art `human`).
4. `_wait_for_seats` wartet bis `connect_wait` auf `present` jeder Verbindung (`SeatNotTaken`).
5. `Match.play` mit `on_move`, das `Recorder` und `HumanPlayer.observe` bedient.
6. `_store` speichert das Ergebnis; ein Mensch hat kein `sdk`/`lang`. Danach `count_ratings`, außer eine Neuberechnung steht an.

Jeder Fehler endet mit `_abort` (`matches.abort`, `jobs.fail`). `PlayWorker.stop` schließt bei SIGTERM alle Sitze und bricht hängende Partien nach `stop_wait` ab.

## Konventionen

- **Uhr und Warten injiziert:** `Worker`, `PlayWorker`, `Heartbeat`, `run_job` und `run_verification` nehmen `now: Callable[[], datetime]` (Standard `utc_now`, UTC). Die Worker nehmen `sleep`; Tests geben `sleep=lambda _seconds: None`. `HumanPlayer` nimmt `monotonic`.
- **Ausnahmen sind Infrastrukturfehler:** Was `run_job`, `run_verification` oder `InteractiveGame` nicht selbst abfängt, behandelt der Aufrufer als Fehler des Servers (Wiederholen, Abbrechen, Ablehnen mit `internal`). Fehler eines Bots sind kein Ausnahmefall, sondern Ende und Grund im `MatchRecord`.
- **`UnsupportedBot`** heißt: Partie abbrechen, nicht wiederholen.
- **`Shutdown` erbt von `BaseException`**, damit kein `except Exception` es schluckt. Wer einen Job hält, gibt ihn im `except Shutdown` frei und wirft weiter.
- **Nur der Halter eines Jobs ändert seine Partie.** `recovery.py` lässt die Partie stehen; der nächste Halter setzt sie in `run_job` zurück.
- **Interaktive Partien wiederholen nie** (E113): Abbruch statt `retry`.
- **Datenbank nur über `sbm_store`:** Kein Modul greift direkt auf Collections zu. Konstanten wie `jobs.MATCH`, `bots.VERIFIED`, `play.PLAY_JOB` kommen von dort.
- **Konfiguration:** eingefrorene Dataclasses mit Standardwerten; `from_env(environ)` liest nur die Umgebungsvariablen und wirft `ValueError` mit Variablenname und Wert.
- **Bot-Prozesse:** Umgebung nur `SBM_BOT_DIR` für nsjail, `close_fds=True`. Jede cgroup wird in `finally` beendet (`kill`) und entfernt; Checkouts räumt `BotDir.remove` auf.
- **Ausgaben eingesperrter Programme sind feindlich:** Längen, Felder und Exit-Code werden geprüft, bevor etwas in einen Report kommt (`analysis_stage._report`, `jail._versions`).
- **Logging:** `log = logging.getLogger(__name__)` je Modul; Meldungen auf Englisch mit Partie- oder Job-Id.
- **Docstrings** sagen das Warum in ganzen Sätzen; Konstanten tragen einen Kommentar zu ihrer Herkunft.

## Erweitern

### Neue Job-Art

1. Konzept klären und in `docs/00_entscheidungen.md` eintragen.
2. In `services/store/src/sbm_store/jobs.py` die Konstante und eine Fabrik `new_<art>_job` anlegen (Vorbild `new_verification_job`); das Anlegen bleibt in `sbm_store` bzw. in der Web-API.
3. Eine Funktion für einen Job in einem eigenen Modul schreiben (Vorbild `verification/pipeline.run_verification`): Signatur `(db, job, *, …, now)`, Ausnahmen gelten als Infrastrukturfehler, am Ende `jobs.complete`.
4. In `worker.py` `_claim` (Reihenfolge) und `_work` (Verteilung) ergänzen, mit `except Shutdown` (Job freigeben) und `except Exception` (Wiederholen oder Aufgeben).
5. In `retries.py` eine Funktion für das Aufgeben nach `max_attempts`, in `recovery.py` die Art in die Schleife von `recover_expired` und in `_give_up` aufnehmen.
6. Tests in `services/runner/tests/` (Vorbild `test_verification.py`, `test_failures.py`).
7. [match-runner.md](../komponenten/match-runner.md) und bei neuen Feldern [datenmodell.md](../komponenten/datenmodell.md) nachführen.

Für eine Art, die nicht in der Queue läuft, eine eigene Rolle wie `play/` anlegen und in `cli.py` neben `QUEUE` und `PLAY` aufnehmen.

### Neue Stufe der Verifikation

1. Stufe in [verifikation.md](../komponenten/verifikation.md) beschreiben und die Entscheidung eintragen.
2. Den Namen in `services/store/src/sbm_store/verification_reports.py` ergänzen und, falls der Bot einen eigenen Status bekommt, in `bots.py` (`PIPELINE`).
3. `spec/web/openapi.json` (`VerificationStageName`, `VerificationStage`) anpassen, `npm run api-types` in `frontend/` und die Texte unter `report.stage` in `frontend/src/i18n/de.json` und `en.json` ergänzen.
4. Ein Modul unter `verification/` anlegen, das ein Stufen-Dict mit `stage`, `status`, `duration_ms`, `problem` liefert (Vorbild `analysis_stage.py`). Läuft dabei Code oder liest es hochgeladene Dateien, dann nur über die Sandbox: eine Methode in `sandbox/jail.py` (Vorbild `analyze` mit `run_once`) und im Protokoll `Verifier` in `pipeline.py`.
5. In `pipeline._stages` an der richtigen Stelle einhängen, mit `bots.advance` nur bei `advance`.
6. `FakeVerifier` in `tests/uploads.py` erweitern, Tests in `test_verification.py` und `test_recheck.py`; läuft die Stufe im Jail, auch `tests/sandbox/test_sandbox_verification.py`.

### Neue Umgebungsvariable oder Einstellung

1. Zur passenden Dataclass gehen: `sandbox/settings.py` (`SandboxSettings`), `play/config.py` (`PlayConfig`) oder `config.py` (`RunnerConfig`, hat noch kein `from_env`; Werte setzt `cli.py`).
2. Feld mit Standardwert und Kommentar anlegen, in `from_env` lesen und prüfen, bei falschem Wert `ValueError` mit Name und Wert.
3. Test wie `play/test_play_config.py` oder `test_sandbox_setup.py`.
4. In `deploy/compose.yaml` und `deploy/.env.example` (ohne Werte, die geheim sind) eintragen, Tabelle „Betrieb“ in [gateway.md](../komponenten/gateway.md) bzw. die Liste in [match-runner.md](../komponenten/match-runner.md) nachführen.

Einstellungen, die Admins ändern, gehören nicht in die Umgebung, sondern in die Datenbank (`sbm_store.*_settings`, E154); der Runner liest sie pro Schritt, wie `queue_settings.get` und `play_settings.get`.

### Änderung der Sandbox-Policy

1. Änderung in [sandbox.md](../komponenten/sandbox.md) begründen; Grenzen sind fest und für alle Sprachen gleich (A14), konfigurierbare Limits sind zurückgestellt.
2. nsjail-Optionen (Mounts, Namespaces, Umgebung, rlimits) in `sandbox/python.cfg`, Systemaufrufe in `sandbox/python.policy`, cgroup-Grenzen in `sandbox/limits.py`.
3. Einen Testbot unter `services/runner/tests/sandbox/bots/<name>/bot.py` anlegen, der den Fall versucht (Fluchtversuche enden mit Exit-Code 42, wenn sie etwas erreichen), und einen Test in `test_sandbox_escape.py`, `test_sandbox_limits.py` oder `test_sandbox_freeze.py`.
4. Die Negativ-Suite mit `bash services/runner/tests/sandbox/run-in-docker.sh` laufen lassen. Ändern sich Rechte des Containers, die Optionen dort und beim Dienst `runner` in `deploy/compose.yaml` gleich halten.
5. Neue Sprache: eigene `sandbox/<sprache>.cfg` und Whitelist, Laufzeitverzeichnis im Image, Sprachprüfung in `Sandbox.player` (`LANGUAGE`).

## Tests

| Ort | Inhalt |
|-----|--------|
| `services/runner/tests/` | Queue-Worker, Partie, Fehlerfälle, Abbruch, Heartbeat, Checkout, Verifikation, Neuprüfung, Ligen je Runde, cgroup-Dateien, Start der Sandbox ohne nsjail, `sbm-enqueue` |
| `services/runner/tests/play/` | Play-Runner gegen den echten Gateway; braucht `sbm-gateway` installiert (sonst übersprungen) |
| `services/runner/tests/sandbox/` | Negativ-Suite im Runner-Image |

Fixtures und Hilfsmodule:

| Datei | Zweck |
|-------|-------|
| `sbm_store.testing` (Plugin über `pytest11`) | `db`: frische Datenbank je Test; ohne MongoDB übersprungen, mit `SBM_REQUIRE_MONGO=1` Fehler; Adresse aus `SBM_TEST_MONGO_URI` |
| `tests/conftest.py` | `config` (`RunnerConfig`), `reference_bots` (migriert, gibt Random und Material), `worker` (ohne Warten), `enqueue` (Partie in der Vergangenheit), `foreign_bot`; Disziplin `QUICK` mit drei Zügen |
| `tests/uploads.py` | `upload` legt einen Bot mit Dateien und Verifikationsjob an; Dateisätze `GOOD`, `CRASHING`; Berichte `CLEAN`, `DIRTY`; `FakeVerifier` (echter Checkout, Analyse nach Vorgabe, Bots als Prozesse ohne nsjail); `CheckedPlayer` |
| `tests/play/conftest.py` | `RunningGateway` im eigenen Thread, `RemoteBot` (Bot-Protokoll v1 über WebSocket), `Person` (Browser mit play-v1); Fixtures `gateway`, `play_config`, `play_worker`, `create_remote` |
| `tests/sandbox/conftest.py` | `sandbox` (überspringt ohne `SBM_SANDBOX=nsjail`, scheitert mit `SBM_REQUIRE_SANDBOX=1`), `no_leftovers` (nach jedem Test keine cgroup unter `bots/`), `jailed`, `play`; Fehler als GitHub-Annotation |
| `tests/sandbox/sandbox_suite.py` | `BOTS`, `RANDOM`, `QUICK`, `REGULAR` (reguläre Endgründe) |
| `tests/sandbox/bots/` | Testbots: Endlosschleife, Dateien, verbotene Aufrufe, fork, lange Zeile, Speicher, Netz, Spinner, stderr-Flut, Threads, ein Upload mit Datendatei |

Befehle aus dem Repo-Wurzelverzeichnis:

| Zweck | Befehl |
|-------|--------|
| Tests ohne Sandbox | `pytest services/runner` (Standard `SBM_SANDBOX=none`; die Negativ-Suite wird übersprungen) |
| Negativ-Suite | `bash services/runner/tests/sandbox/run-in-docker.sh` (Linux mit cgroup v2; `SBM_RUNNER_IMAGE=…` nimmt ein vorhandenes Image, E88) |
| Lint/Format | `ruff check services/runner` und `ruff format --check services/runner` |

Besonderheiten:

- Ohne Sandbox spielen nur die Referenzbots (`plain_player`); hochgeladene Bots testet `FakeVerifier` als gewöhnliche Prozesse.
- Die Tests brauchen das installierte Python-SDK und `sbm-store` (`pip install -e services/store -e "services/runner[dev]"`), die Play-Tests zusätzlich `services/gateway`.
- Die Negativ-Suite läuft nicht unter Docker Desktop mit WSL2 (nur cgroup v1). In CI ist sie der Job `sandbox`.
