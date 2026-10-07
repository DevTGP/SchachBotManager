# SchachBotManager

Website, auf der Schachbots (Python, C++, Java, C#, JavaScript) in Ligen, Turnieren und Einzelspielen gegeneinander antreten. Partien werden gespeichert und sind öffentlich ansehbar. Eingeladene Nutzer laden Bots hoch; diese werden geprüft und laufen isoliert auf dem Server.

## Stand

**M0** laut `docs/roadmap.md` ist abgeschlossen: Festlegungen E34–E55, Repo-Gerüst, CI mit `tools/spec-check`, Protokoll-Schema v1 (`spec/protocol/v1/`), kanonische Bot-API (`spec/api/`), C-Schnittstelle des Kerns (`sdk/core/include/sbm/`), Testvektoren (`spec/testvectors/`, erzeugt mit `tools/testvector-gen`). **M1** ist fertig: C++-Kern unter `sdk/core/` (CMake, besteht alle Vektoren, E56–E57); Python-SDK unter `sdk/python/` (nanobind, besteht alle API-Vektoren, E58–E60): `Board`, `Move`, `Clock`, `Log`, `Bot`, `run` mit `stdio`/`tcp`, `load_data` (E61–E63). Wheels für Windows, Linux und macOS über CI (E64), veröffentlicht auf PyPI per Versions-Tag (E70). Referee-Kern als `sbm.referee` im Python-Paket (E65, strenge Prüfung der Bot-Nachrichten E66). Lokale Arena als `sbm.arena` mit dem Befehl `sbm-arena` (E67). Referenzbots `random` und `material` als `sbm.bots`, in der Arena per Kurzname (E68). Debug-Workflow: Arena-Start aus einer PGN-Stellung (`--replay`) und Vorlagenprojekt `templates/python/` mit VS-Code-Konfiguration (E69). Abnahmetest in `sdk/python/tests/test_acceptance.py`. **M2** ist fertig: Store mit Migrationen und Runner unter `services/` (E75), lesende Web-API unter `backend/` (E76), SPA unter `frontend/` (E77), Deployment mit Docker Compose unter `deploy/` und Workflow `deploy.yml` (E78); abgenommen auf dem Server am 7. Oktober 2026. Als Nächstes folgt **M3**.

## Zuerst lesen

| Datei | Wofür |
|-------|-------|
| `docs/00_entscheidungen.md` | Alle Entscheidungen (E…), Annahmen (A…), offene Punkte (O…), Risiken (R…). Maßgeblich bei Widersprüchen |
| `docs/roadmap.md` | Meilensteine, Reihenfolge, Abnahmekriterien |
| `docs/architektur/systemuebersicht.md` | Komponenten, Vertrauensgrenzen, Repo-Struktur |
| `docs/architektur/ablaeufe.md` | Zusammenspiel der Komponenten |
| `docs/komponenten/*.md` | Eine Datei je Komponente; vor Arbeit an einer Komponente die passende Datei lesen |

`docs/_archiv/` enthält überholte Stände und ist nicht maßgeblich.

## Kernentscheidungen in Kurzform

- **Stack:** Flask als reine API, React + TypeScript + Vite als SPA, MongoDB, Deployment über GitHub Actions.
- **Schachregeln:** Ein gemeinsamer C++-Kern mit flacher C-Schnittstelle. Referee, Arena und alle fünf SDKs nutzen ihn; die SDKs sind dünne Bindings. Keine zweite Regelimplementierung anlegen.
- **Bot-API:** Callback-Modell (`choose_move(board, clock)`), hohe Ebene plus Rohzugriff aufs Brett, gleiche Wörter in idiomatischer Schreibweise je Sprache. Jeder Bot hat sein eigenes Brett im eigenen Prozess.
- **Bot ↔ Server:** Zeilenweises JSON über stdin/stdout. Bots sprechen nie direkt miteinander. Der Referee ist allein maßgeblich für Legalität, Zeit und Ergebnis.
- **Zeit:** Wanduhrzeit. Außerhalb des eigenen Zuges ist der Bot-Prozess eingefroren.
- **Fairness:** Keine Sprachfaktoren; alle Sprachen haben identische Bedingungen.
- **Sicherheit:** nsjail als Sandbox plus statische Analyse je Sprache. Die Sandbox muss allein ausreichen; die Analyse ist die zweite Schicht.
- **Bots:** Upload als Quellcode (mehrere Dateien, Datendateien bis 1 MB über `load_data`). Neue Version = neuer Bot. Quellcode nur für Besitzer und Admin sichtbar.
- **Wettbewerbe:** Ligen mit Saisons, Tabellen, Auf-/Abstieg; Turniere; eine gemeinsame Spiel-Queue ohne feste Startzeiten. Alles über die Website konfigurierbar, Konfiguration in der DB.
- **Zugang:** Lesen und Spielen gegen Bots ohne Account; Upload nur für eingeladene Nutzer.
- **Oberfläche:** Deutsch und Englisch, Texte von Beginn an in Übersetzungsdateien.
- **Zurückgestellt:** Konfigurierbare Ressourcenlimits (Speicher, CPU, Dateigröße). Nicht einbauen.

## Betrieb

- Server: Ubuntu x86-64, nicht dediziert, schwach. Standard ist ein Spiel gleichzeitig.
- Ein Docker-Compose-Stack. Nur der `frontend`-Container hängt am externen Netz `local-web`; der vorhandene Nginx Proxy Manager zeigt darauf. Der Stack veröffentlicht keine Ports.
- Adresse: `schachbotmanager.devtgp.net` (als Konfigurationswert, nicht fest im Code).
- Deploy: GitHub Actions per SSH, Stack setzen, Container bauen auf dem Server.
- `runner` und `verifier` laufen als Container mit erweiterten Rechten (für nsjail) und hängen nicht am Proxy-Netz.

## Regeln für die Arbeit im Repo

- **Öffentliches Repo:** Keine Secrets, SSH-Zugangsdaten oder Serverpfade einchecken. Dafür GitHub-Secrets bzw. Umgebungsdateien auf dem Server; im Repo nur eine Beispiel-Umgebungsdatei.
- **Kleine, thematisch getrennte Dateien:** Eine Datei, eine Verantwortung. Keine Sammeldateien. Struktur laut `docs/architektur/systemuebersicht.md`.
- **Tests vor Abschluss:** Jede Änderung mit Tests, Linting und Diff-Durchsicht abschließen. Der Kern muss die Vektoren unter `spec/testvectors/` bestehen, jedes Binding die API-Vektoren.
- **Spezifikation zuerst:** Protokoll und Bot-API werden unter `spec/` definiert und sind die Quelle für Referee, SDKs und Doku. Änderungen dort zuerst, dann im Code.
- **Bot-Code ist nicht vertrauenswürdig**, auch beim Kompilieren. Er läuft ausschließlich in der Sandbox. Die Web-API startet nie Prozesse.
- **Entscheidungen nachführen:** Neue oder geänderte Entscheidungen in `docs/00_entscheidungen.md` eintragen und die betroffene Komponenten-Datei anpassen.
- **Rückfragen:** Bei Konzept- und Designentscheidungen nachfragen statt annehmen. Triviale Details pragmatisch entscheiden und kurz benennen.
- **Doku-Sprache:** Deutsch. Code, Bezeichner und Commit-Nachrichten auf Englisch.

## Befehle

Build-, Test- und Lint-Befehle hier eintragen, sobald sie entstehen.

| Zweck | Befehl (aus dem Repo-Wurzelverzeichnis) |
|-------|------------------------------------------|
| Werkzeuge einrichten | `python -m venv .venv` und dann `.venv/Scripts/pip install -e "tools/spec-check[dev]" -e "tools/testvector-gen[dev]"` (Linux: `.venv/bin/`) |
| Spezifikation prüfen | `spec-check spec` |
| Tests spec-check | `pytest tools/spec-check` |
| Lint/Format spec-check | `ruff check tools/spec-check` und `ruff format --check tools/spec-check` |
| Testvektoren erzeugen | `testvector-gen spec` |
| Testvektoren prüfen | `testvector-gen spec --check --perft fast` (CI); alle Perft-Vektoren nachzählen mit `--perft all` (einige Minuten) |
| Tests testvector-gen | `pytest tools/testvector-gen` |
| Lint/Format testvector-gen | `ruff check tools/testvector-gen` und `ruff format --check tools/testvector-gen` |
| Kern konfigurieren | `cmake -S sdk/core -B build/core -DCMAKE_BUILD_TYPE=Release` (lokal mit `-G Ninja`; `-DSBM_SLOW_TESTS=ON` nimmt die langsamen Perft-Vektoren dazu) |
| Kern bauen | `cmake --build build/core --config Release` |
| Kern testen | `ctest --test-dir build/core -C Release --output-on-failure` |
| Format nativer Code | `clang-format --dry-run --Werror` über alle `.h/.c/.hpp/.cpp` in `sdk/core/{include,src,tests}` und `sdk/python/src/native` (clang-format 19.1.7: `pip install clang-format==19.1.7`) |
| Python-SDK bauen und installieren | `.venv/Scripts/pip install "./sdk/python[dev]"`; unter Windows mit `CMAKE_GENERATOR="Visual Studio 17 2022"`, sonst greift Strawberrys MinGW |
| Tests Python-SDK | `pytest sdk/python` (gegen das installierte Paket; nach Änderungen neu installieren) |
| Lint/Format Python-SDK | `ruff check sdk/python` und `ruff format --check sdk/python` |
| Wheel lokal bauen und testen | `pip install cibuildwheel==4.3.0`, dann `cibuildwheel --only cp312-win_amd64 sdk/python` (Windows mit `CMAKE_GENERATOR` wie oben; Linux-Wheels brauchen Docker); Ausgabe in `wheelhouse/` |
| Version veröffentlichen | Version in `sdk/core/CMakeLists.txt` setzen und committen, dann `git tag vX.Y.Z` und `git push origin master vX.Y.Z`; `wheels.yml` baut, testet und lädt auf PyPI hoch (E70) |
| Lokale Arena | `sbm-arena weiss.py schwarz.py --games 2 --moves` bzw. `python -m sbm.arena …` (nach Installation des Python-SDK; Optionen mit `--help`, E67) |
| Referenzbot starten | `python -m sbm.bots.random_mover` bzw. `python -m sbm.bots.material`; in der Arena als `random`/`material` (E68) |
| Stellung aus einer Partie | `sbm-arena tcp material --no-clock --replay partien.pgn --replay-ply 40` (E69) |
| Lint/Format Vorlage | `ruff check templates/python` und `ruff format --check templates/python`; ihre Tests laufen mit `pytest sdk/python` |
| Dienste installieren | `.venv/Scripts/pip install -e services/store -e "services/runner[dev]" -e "backend[dev]"` (braucht das installierte Python-SDK) |
| Test-MongoDB | `docker run -d --name sbm-test-mongo -p 127.0.0.1:27017:27017 mongo:8.0`; Tests lesen `SBM_TEST_MONGO_URI` (Standard `mongodb://localhost:27017`) und werden ohne Server übersprungen, mit `SBM_REQUIRE_MONGO=1` scheitern sie |
| Tests Store/Runner/API | `pytest services/store`, `pytest services/runner` bzw. `pytest backend` (je Paket einzeln aufrufen; die API-Tests prüfen jede Antwort gegen `spec/web/openapi.json`) |
| Lint/Format Store/Runner/API | `ruff check services/store services/runner backend` und `ruff format --check services/store services/runner backend` |
| Datenbank migrieren | `sbm-migrate` (liest `SBM_MONGO_URI`, `SBM_MONGO_DB`) |
| Web-API lokal | `flask --app sbm_api.wsgi run` mit `SBM_MONGO_URI` (und optional `SBM_MONGO_DB`, `SBM_PUBLIC_URL`); auf dem Server gunicorn mit `sbm_api.wsgi:app` (E76) |
| Partien einreihen und spielen | `sbm-enqueue Random Material --games 2 --alternate`, dann `sbm-runner` (E75) |
| Frontend einrichten | `npm ci` in `frontend/` (Node ab 22.12) |
| Frontend lokal | `npm run dev` in `frontend/`; reicht `/api` an `SBM_API_URL` weiter (Standard `http://127.0.0.1:5000`) |
| Tests Frontend | `npm test` in `frontend/` |
| Lint/Format/Typen Frontend | `npm run lint`, `npm run format:check` und `npm run build` (tsc und Vite) in `frontend/` |
| API-Typen erzeugen | `npm run api-types` in `frontend/` nach Änderungen an `spec/web/openapi.json`; `npm run api-types:check` prüft |
| Stack lokal starten | Netz `docker network create local-web`, `deploy/.env.example` nach `deploy/.env` kopieren und ausfüllen, dann `bash deploy/deploy.sh` |
| Stack bedienen | `docker compose -f deploy/compose.yaml logs -f runner`; Partien ansetzen mit `docker compose -f deploy/compose.yaml run --rm runner sbm-enqueue Random Material` |
| Workflows prüfen | `actionlint` (mit `shellcheck` im `PATH`; beide per `pip install actionlint-py shellcheck-py`) und `shellcheck deploy/*.sh .github/scripts/*.sh` |
| Header des Kerns prüfen | `gcc -std=c11 -Wall -Wextra -Wpedantic -Werror -fsyntax-only -Isdk/core/include sdk/core/tests/header_check.c`, ebenso `g++ -std=c++20 … header_check.cpp` |

CI: `.github/workflows/ci.yml` (Job `changes` bestimmt die geänderten Bereiche, jeder weitere Job läuft nur für seinen Bereich, E79; Job `spec` für spec-check, Job `testvectors` für den Generator und die erzeugten Dateien, Job `core-headers` für die Header, Job `core` für Build und Tests des Kerns unter Linux, Windows und macOS, Job `python` für Build, Lint und Tests des Python-SDK samt Vorlage `templates/python` mit Python 3.11 und 3.14 unter Linux, Windows und macOS, Job `native-format` für clang-format, Job `services` für Lint und Tests von `services/store`, `services/runner` und `backend` gegen einen MongoDB-Dienstcontainer, Job `frontend` für API-Typen, Lint, Tests und Build der SPA); `.github/workflows/wheels.yml` baut und testet die Wheels aller Plattformen und lädt sie als Artefakte hoch, nur bei einem Tag `v*` oder von Hand (E79); beim Tag veröffentlicht der Job `publish` sie auf PyPI (Umgebung `pypi`). `.github/workflows/deploy.yml` bringt `master` nach grüner CI auf den Server, baut aber nur bei Änderungen am Stack; von Hand gestartet baut er immer (Umgebung `production`, Secrets in `docs/komponenten/deployment.md`).

## Offen

Offene Punkte stehen in `docs/00_entscheidungen.md` (O…).
