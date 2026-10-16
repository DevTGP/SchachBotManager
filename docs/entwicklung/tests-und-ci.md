# Tests und CI

Welche Tests es je Paket gibt, wie sie laufen, was die CI daraus macht und wie Releases und Deploys ausgelöst werden. Die Befehle stehen gesammelt in der Tabelle „Befehle“ der [CLAUDE.md](../../CLAUDE.md); die Code-Karten nennen die Tests je Modul.

## Grundregeln

- Jede Änderung endet mit Tests, Lint und Durchsicht des Diffs (Regel in der `CLAUDE.md`). „Grün“ heißt: die Tests des geänderten Pakets und aller Pakete, die laut Bereichstabelle unten mitlaufen.
- Der Kern besteht alle Vektoren unter `spec/testvectors/`, jedes Binding die API-Vektoren unter `spec/testvectors/api/`. Neue Regeln oder API-Funktionen bekommen zuerst einen Vektor (siehe [aenderungen.md](aenderungen.md#protokoll-oder-bot-api-ändern)).
- Kein Test wird übersprungen, um grün zu werden. Tests, die einen Dienst brauchen, überspringen sich lokal ohne ihn; in der CI erzwingen Umgebungsvariablen, dass sie stattdessen scheitern.
- Tests nutzen feste Uhren statt Wartezeiten, wo der Code eine Uhr annimmt (`now=` in der API, `Clock` in den Fixtures, `keep_expired` für TTL-Indizes).

## Tests je Paket

| Paket | Art | Ort | Läuft mit |
|-------|-----|-----|-----------|
| `tools/spec-check` | Unit-Tests des Prüfers | `tools/spec-check/tests` | `pytest tools/spec-check` |
| `tools/testvector-gen` | Unit-Tests des Generators; dazu prüft `--check`, dass die eingecheckten Vektoren dem Generator entsprechen | `tools/testvector-gen/tests` | `pytest tools/testvector-gen`, `testvector-gen spec --check --perft fast` |
| Kern (`sdk/core`) | C++-Unit-Tests der Engine und der C-Schnittstelle; Vektor-Läufer über alle JSON-Vektoren; Header-Check in C11 und C++20 | `sdk/core/tests/{unit,vectors}`, `header_check.{c,cpp}` | `ctest --test-dir build/core …`, `gcc`/`g++ -fsyntax-only` |
| Python-SDK | API-Vektoren, Oberfläche, Referee, Arena, Analyse, Transporte, `sbm.play`, Viewer-Client, Vorlage, Abnahmetest | `sdk/python/tests` | `pytest sdk/python` (gegen das installierte Paket) |
| JavaScript-SDK (`sdk/javascript`) | API-Vektoren, Oberfläche gegen `spec/api/`, je Modul, `run` in eigenen Prozessen, Partien in `sbm-arena`, Vorlage | `sdk/javascript/test` | `npm test` in `sdk/javascript` (nach `npm run build:native`) |
| C#-SDK (`sdk/csharp`) | xUnit v3: alle API-Vektoren über Reflexion, Oberfläche, Konstanten, Fehler, `Move`, `Board`, Hauptschleife gegen einen geskripteten Referee, Referenzbot `Material`; Analyzer (erlaubte und verbotene APIs, Syntax, Regelwerk) und `sbm-build` (Befehlszeile, Bericht, Prüfung des Programms, Bau von Testbots, E203); Kreuztest mit pytest gegen die Python-Referenzbots in der Arena (E198) und Vorlage `templates/csharp` gegen das gepackte SDK (E201) | `sdk/csharp/tests/Sbm.Tests`, `sdk/csharp/tests/Sbm.Analyzers.Tests`, `sdk/csharp/tests/Sbm.Build.Tests`, `sdk/csharp/tests/cross` | `dotnet test sdk/csharp/Sbm.slnx` (Kern vorher als geteilte Bibliothek bauen), `pytest sdk/csharp/tests/cross` (braucht zusätzlich das installierte Python-SDK) |
| Viewer (`sdk/viewer`) | Modelltests ohne Fenster (Nachrichten, Session, Navigation, Text); das Programm selbst testet `test_viewer_program.py` über einen Screenshot | `sdk/viewer/tests` | `ctest --test-dir build/viewer …` |
| `services/store` | Funktionen je Collection, Migrationen, Ratings, Einstellungen | `services/store/tests` | `pytest services/store` |
| `services/gateway` | Gateway in einem Thread auf freien Ports, beide Enden als WebSocket- bzw. TCP-Client | `services/gateway/tests` | `pytest services/gateway` |
| `services/runner` | Echte Partien der Referenzbots ohne Sandbox, Verifikation, Abbruch, Heartbeat; `play/` mit echtem Gateway; `sandbox/` als Negativ-Suite | `services/runner/tests` | `pytest services/runner`; Sandbox nur über `run-in-docker.sh` |
| `backend` | Je Endpunkt eine Testdatei; jede Antwort gegen `spec/web/openapi.json` geprüft | `backend/tests` | `pytest backend` |
| `frontend` | Vitest mit Testing Library: Seiten, Viewer, Formulare, Socket | `frontend/src/**/*.test.ts(x)` | `npm test` in `frontend/` |
| `templates/python` | Die Vorlage startet und spielt; läuft mit dem SDK | `sdk/python/tests/test_template.py` | `pytest sdk/python` |
| `templates/javascript` | Buch, Zugwahl, Start als Programm, VS-Code-Konfiguration, Partie in der Arena; gegen eine Kopie, die das SDK aus `src/` importiert | `sdk/javascript/test/template.test.ts` | `npm test` in `sdk/javascript` |

Die Python-Pakete werden einzeln aufgerufen (`pytest services/store`, nicht `pytest services`): Jedes hat eigene `conftest.py` und Hilfsmodule mit gleichen Namen.

### Gemeinsame Fixtures und Helfer

| Fixture / Helfer | Ort | Zweck |
|------------------|-----|-------|
| `mongo_uri`, `db`, `keep_expired` | [`sbm_store/testing.py`](../../services/store/src/sbm_store/testing.py), als pytest-Plugin `sbm_store` über den Entry-Point `pytest11` | Frische Datenbank je Test für Store, Runner und API; TTL-Indizes für Tests mit fester Uhr abschalten |
| `openapi`, `app`, `client`, `login`, `clock` | [`backend/tests/conftest.py`](../../backend/tests/conftest.py) | App mit fester Uhr, deren Test-Client jede Antwort gegen die OpenAPI-Datei prüft; `login(name, role)` legt ein Konto an und meldet es an |
| `league_world.py` | `services/store/tests/` | Ligen, Bots und Ergebnisse für die Tests von Ligen und Saisons |
| `accounts.py`, `stored_games.py`, `stored_disciplines.py`, `stored_leagues.py`, `bot_uploads.py` | `backend/tests/` | Testdaten: Konten mit CSRF-Kopf, gespeicherte Partien, Disziplinen, Ligen mit Saisons, Uploads |
| `config`, `worker`, `reference_bots`, `QUICK` | [`services/runner/tests/conftest.py`](../../services/runner/tests/conftest.py) | Worker mit kurzem Lease und ohne Schlafen; Disziplin mit drei Zügen, damit eine echte Partie eine Sekunde dauert |
| Gateway im Thread, Remote-Bot, Play-Worker | [`services/runner/tests/play/conftest.py`](../../services/runner/tests/play/conftest.py) | Interaktive Partien Ende zu Ende ohne Browser |
| `RunningGateway` | [`services/gateway/tests/conftest.py`](../../services/gateway/tests/conftest.py) | Gateway auf freien Ports in eigenem Event-Loop |
| `reset_log` (autouse) | [`sdk/python/tests/conftest.py`](../../sdk/python/tests/conftest.py) | Jeder Test beginnt mit dem Standard-Logzustand |
| `arena_bots.py`, `scripted_player.py`, `remote_fakes.py`, `viewer_fakes.py`, `vector_codec.py`, `protocol_schemas.py`, `spec_files.py` | `sdk/python/tests/` | Bots für die Arena, Spieler mit festem Skript, falscher Server und falsches Viewer-Programm, Lesen der Vektoren und Schemas aus `spec/` |
| `spec.ts`, `referee.ts`, `bot-process.ts`, `capture.ts`, `arena-command.ts` | `sdk/javascript/test/` | Spezifikation lesen, Referee mit festem Skript, Bot in eigenem Node-Prozess, Log mitschneiden, `sbm-arena` aufrufen |
| `mockApi`, `renderRoute` u. a. | [`frontend/src/test/render.tsx`](../../frontend/src/test/render.tsx) | Ersetzt `fetch`; Antworten je API-Pfad als Wert oder Funktion; zeichnet jede Anfrage mit Methode, Kopf und Körper auf |
| `fixtures.ts`, `leagues.ts`, `fakeSocket.ts`, `files.ts`, `setup.ts` | `frontend/src/test/` | Typisierte Beispieldaten aus `api/types` (Ligen eigens), steuerbarer WebSocket, Dateien wie aus einer Ordnerauswahl, Englisch als Sprache und Aufräumen nach jedem Test |

### Schalter für Tests

| Variable | Wirkung |
|----------|---------|
| `SBM_TEST_MONGO_URI` | MongoDB der Tests, Standard `mongodb://localhost:27017`; ohne erreichbaren Server werden die Datenbanktests übersprungen |
| `SBM_REQUIRE_MONGO=1` | Datenbanktests scheitern statt sich zu überspringen (in der CI gesetzt) |
| `SBM_REQUIRE_VIEWER=1` | Tests des Viewer-Programms scheitern, wenn es im installierten Paket fehlt (Job `viewer`) |
| `SBM_ARENA` | Pfad zu `sbm-arena` für die Arena-Tests des JavaScript-SDK, Standard aus dem `PATH`; ohne Arena überspringen sie sich |
| `SBM_REQUIRE_ARENA=1` | Arena-Tests des JavaScript-SDK scheitern ohne `sbm-arena` (Job `javascript` unter Linux mit Node 24) |
| `SBM_REQUIRE_SANDBOX=1` | Negativ-Suite scheitert ohne nsjail und beschreibbare cgroup v2 (gesetzt von `run-in-docker.sh`) |
| `SBM_SANDBOX=none` | Runner ohne Sandbox, nur für Referenzbots; so laufen die Runner-Tests außerhalb des Images |
| `SDL_VIDEO_DRIVER=offscreen` | Viewer ohne Display, für den Screenshot-Test |

### Was nicht automatisch geprüft wird

- **Übersetzungen:** Kein Test vergleicht die Schlüssel von `frontend/src/i18n/de.json` und `en.json`. Die Frontend-Tests laufen auf Englisch; fehlende deutsche Schlüssel fallen nur beim Ansehen auf. Neue Texte daher immer in beiden Dateien anlegen.
- **Darstellung:** Layout, Farben und schmale Bildschirme prüft kein Test; dafür den Stack lokal starten (siehe [einrichtung.md](einrichtung.md#stack-lokal)).
- **Workflows:** `actionlint` und `shellcheck` laufen nur lokal, nicht in der CI.
- **Sandbox:** Die Negativ-Suite braucht Linux mit cgroup v2; unter Docker Desktop mit WSL2 läuft sie nicht. Lokal unter Windows bleibt nur die CI.

## CI (`ci.yml`)

Läuft bei jedem Push auf `master`, bei Pull Requests und von Hand. Der erste Job `changes` bestimmt, welche Bereiche sich geändert haben; jeder weitere Job läuft nur für seinen Bereich (E79).

### Basis-Commit

- **Push:** Verglichen wird mit dem letzten Commit des Branches, dessen CI-Lauf grün war (über die GitHub-API). Nach einem roten Lauf testet der nächste Push also alles seit dem letzten grünen; das Deploy bekommt nie ungetesteten Code.
- **Pull Request:** Verglichen wird mit der Basis des PR.
- **Alles läuft**, wenn es keinen gültigen Basis-Commit gibt (erster Lauf, Lauf von Hand) oder wenn sich `ci.yml` oder `.github/scripts/changed-areas.sh` selbst geändert haben.
- **Nur Doku geändert:** Kein Bereich trifft zu; außer `changes` läuft kein Job. Das ist gewollt, Links in der Doku prüft die CI nicht.

### Bereiche und Jobs

Die Bereiche stehen als reguläre Ausdrücke in [`changed-areas.sh`](../../.github/scripts/changed-areas.sh). Wer ein neues Verzeichnis anlegt, das ein Job bauen oder testen muss, trägt es dort ein.

| Job | Bereich (Pfade) | Was er tut |
|-----|-----------------|------------|
| `spec` | `spec/`, `tools/spec-check/` | Lint und Tests von spec-check, dann `spec-check spec` |
| `testvectors` | `spec/`, `tools/testvector-gen/` | Lint und Tests des Generators, dann `testvector-gen spec --check --perft fast` |
| `core-headers` | `sdk/core/include/`, `sdk/core/tests/header_check*` | Header in C11 und C++20 mit `-Wall -Wextra -Wpedantic -Werror` |
| `core` | `sdk/core/`, `spec/testvectors/` | Build und `ctest` mit langsamen Perft-Vektoren unter Linux, Windows, macOS |
| `python` | `sdk/core/`, `sdk/python/`, `templates/python/`, `spec/` | SDK ohne Viewer bauen, Ruff für SDK und Vorlage, `pytest sdk/python`; Python 3.11 und 3.14 auf drei Systemen |
| `javascript` | `sdk/core/`, `sdk/javascript/`, `templates/javascript/`, `sdk/python/src/sbm/{arena,referee,bots}/`, `spec/` | `npm ci`, Addon bauen, ESLint und Prettier für SDK und Vorlage, `tsc`, `npm test`; Node 22 und 24 auf drei Systemen, unter Linux mit Node 24 mit installiertem Python-SDK und `SBM_REQUIRE_ARENA=1` |
| `csharp` | `sdk/core/`, `sdk/csharp/`, `templates/csharp/`, `services/runner/tests/sandbox/bots/csharp*`, `sdk/python/`, `spec/api/`, `spec/protocol/`, `spec/testvectors/` | Kern als geteilte Bibliothek bauen, unter Linux CSharpier (SDK, Vorlage und C#-Testbots der Sandbox) und `dotnet format --verify-no-changes`, dann `dotnet test`; danach Python-SDK ohne Viewer installieren, unter Linux `ruff` für den Kreuztest, dann `pytest sdk/csharp/tests/cross` samt Paket und Vorlage; .NET 10 auf drei Systemen (E195, E198, E201) |
| `services` | `sdk/core/`, `sdk/python/`, `services/`, `backend/`, `spec/` | Mit MongoDB 8.0 als Dienst und `SBM_REQUIRE_MONGO=1`: Ruff, dann Tests von Store, Gateway, Runner und API |
| `sandbox` | `sandbox/`, `deploy/python.Dockerfile`, `sdk/core/`, `sdk/python/`, `sdk/csharp/`, `services/` | Baut das Runner-Image mit der C#-Laufzeit und `suite.Dockerfile` mit den C#-Testbots und führt die Negativ-Suite für Python und C# samt `sbm-build` mit den Rechten des Runners aus (E88, E205) |
| `frontend` | `frontend/`, `spec/web/` | `npm ci`, `api-types:check`, Lint, Prettier, `npm test`, `npm run build` |
| `viewer` | `sdk/core/`, `sdk/viewer/`, Viewer-Teile von `sdk/python/`, `spec/protocol/` | Modelltests, dann das SDK mit Viewer bauen und `pytest sdk/python -k viewer` mit `SBM_REQUIRE_VIEWER=1`; drei Systeme, unter Linux mit X11-Headern |
| `native-format` | `sdk/.clang-format`, Quellen in Kern, Python-Modul, JavaScript-Addon, Viewer und `sdk/csharp/server/Sbm.Host` | `clang-format --dry-run --Werror` (19.1.7) |

Alle Python-Jobs außer `python` nutzen Python 3.12. Fehlgeschlagene pytest-Tests erscheinen als Annotation des Laufs, lesbar ohne Anmeldung.

### Typische Fehler in der CI

| Meldung | Ursache und Abhilfe |
|---------|---------------------|
| `api-types:check` schlägt fehl | `spec/web/openapi.json` geändert, aber `npm run api-types` nicht ausgeführt; Ergebnis `frontend/src/api/schema.d.ts` mit einchecken |
| `testvector-gen --check` meldet Abweichungen | Vektoren von Hand geändert oder Generator geändert ohne `testvector-gen spec`; Vektoren neu erzeugen und einchecken |
| Fehler aus `openapi_core` in einem `backend`-Test | Die Antwort weicht vom Schema ab: Feld fehlt in `openapi.json`, falscher Typ oder `nullable` vergessen |
| Ruff-Format | `ruff format` im betroffenen Paket ausführen |
| clang-format | `clang-format -i` auf die Datei; Version 19.1.7 verwenden, andere Versionen formatieren anders |
| Prettier im Job `javascript` | `npm run format` in `sdk/javascript`; prüft auch `templates/javascript` |
| Test nur unter Windows rot | Häufig Pfadtrenner, Zeilenenden oder Prozessgruppen; die Arena hat dafür getrennte Module (`posix_group.py`, `windows_job.py`) |

## Deploy (`deploy.yml`)

- Läuft nach einem grünen CI-Lauf für einen Push auf `master` (`workflow_run`), nur für dieses Repository, und von Hand.
- Nach der CI baut er nur, wenn sich seit dem letzten Deploy etwas geändert hat, woraus der Stack besteht: `deploy`, `sandbox`, `sdk/core`, `sdk/python`, `sdk/csharp`, `services/*`, `backend`, `frontend` ([`needs-deploy.sh`](../../deploy/needs-deploy.sh) gegen `deploy/.deployed-commit` auf dem Server). Von Hand gestartet baut er immer, etwa nach einem geänderten Secret.
- Umgebung `production`; Secrets und Ablauf in [deployment.md](../komponenten/deployment.md).
- `deploy.sh` führt vor dem Start den Dienst `migrate` aus (`sbm-migrate` mit eigenem Mongo-Nutzer); eine neue Migration braucht also keinen eigenen Schritt.

## Release des SDK (`wheels.yml`)

- Läuft bei einem Tag `v*` und von Hand. Baut und testet die Wheels mit cibuildwheel für Linux, Windows und macOS und lädt sie als Artefakte hoch.
- Nur beim Tag veröffentlicht der Job `publish` sie auf PyPI (Umgebung `pypi`, Trusted Publishing, E70). Er prüft vorher, dass der Tag zur Version des Pakets passt.
- Ablauf: Version in `sdk/core/CMakeLists.txt` setzen, committen, `git tag vX.Y.Z`, `git push origin master vX.Y.Z`. Details in [aenderungen.md](aenderungen.md#sdk-veröffentlichen).

## Release des npm-Pakets (`npm.yml`)

- Läuft wie `wheels.yml` bei einem Tag `v*` und von Hand (E226). Baut den Addon für fünf Plattformen (Linux x64/arm64 in `manylinux_2_28`, Windows x64, macOS x64/arm64 ab macOS 11), testet ihn je Plattform, packt alle in `schachbotmanager-X.Y.Z.tgz` und installiert das Paket zur Probe in einem leeren Ordner.
- Nur beim Tag veröffentlicht der Job `publish` es auf npm (Umgebung `npm`, Trusted Publishing). Er prüft vorher, dass der Tag zur Version des Pakets passt.
- Derselbe Tag veröffentlicht also beide SDKs. Die Version kommt für beide aus `sdk/core/CMakeLists.txt`; `version.test.ts` prüft, dass `sdk/javascript/package.json` sie trägt.

## Release des C#-SDK (`nuget.yml`)

- Läuft beim selben Tag `v*` wie `wheels.yml` und von Hand (E200).
- `native` baut den Kern als geteilte Bibliothek auf fünf nativen Runnern mit [`build-core-shared.sh`](../../.github/scripts/build-core-shared.sh): Linux x64/arm64 in `manylinux_2_28` mit Prüfung auf `libstdc++` und glibc ≤ 2.28, Windows x64 mit statischer CRT, macOS x64/arm64 ab 11.
- `pack` packt sie mit `-p:SbmRuntimesDir=…` in ein Paket, prüft jede Bibliothek darin und beim Tag den Namen gegen die Version; Artefakt `nuget`.
- `test` installiert auf allen fünf Plattformen das Python-SDK aus dem Repo und läuft `test_template.py` mit `SBM_NUGET_SOURCE` auf dieses Paket.
- Nur beim Tag lädt `publish` per Trusted Publishing hoch (Umgebung `nuget`, Secret `NUGET_USER` mit dem Profilnamen auf nuget.org).

## Workflows lokal prüfen

```
pip install actionlint-py shellcheck-py
actionlint
shellcheck deploy/*.sh .github/scripts/*.sh
```

`changed-areas.sh` lässt sich lokal ausprobieren: `bash .github/scripts/changed-areas.sh $(git rev-parse origin/master)` zeigt, welche Jobs ein Push des aktuellen Stands auslösen würde.
