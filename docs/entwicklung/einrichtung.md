# Einrichtung

Vom frischen Klon bis zum laufenden Stack auf dem eigenen Rechner. Wer nur einen Bot schreiben will, braucht das alles nicht: `pip install sbm` und die Vorlage `templates/python/` reichen (siehe [lokale-entwicklung.md](../komponenten/lokale-entwicklung.md)). Die einzelnen Befehle stehen auch in der Tabelle „Befehle“ der [CLAUDE.md](../../CLAUDE.md).

## Voraussetzungen

| Werkzeug | Version | Wofür |
|----------|---------|-------|
| Python | 3.12 oder neuer; das SDK läuft ab 3.11 | Werkzeuge, SDK, Dienste, API |
| C++-Compiler mit C++20 | GCC, Clang oder MSVC (Visual Studio 2022) | Kern, Python-Modul, Viewer |
| CMake | ab 3.21 | Kern und Viewer; beim Bau des SDK ergänzt scikit-build-core es bei Bedarf als Python-Paket |
| Node.js | ab 22.12 | Frontend |
| .NET SDK (optional) | 10.0 | C#-SDK (`sdk/csharp`) |
| Docker | aktuell | MongoDB für Tests, Stack lokal, Negativ-Suite der Sandbox |
| clang-format | genau 19.1.7 (`pip install clang-format==19.1.7`) | Format des nativen Codes; andere Versionen formatieren anders |
| X11-Header (nur Linux, nur für den Viewer) | `libx11-dev libxext-dev libxcursor-dev libxi-dev libxrandr-dev libxfixes-dev` | SDL3 im Viewer |
| actionlint, shellcheck (optional) | `pip install actionlint-py shellcheck-py` | Workflows und Shell-Skripte prüfen |

Ninja ist lokal empfohlen (`-G Ninja`), aber nicht nötig.

## Schritt für Schritt

Alle Befehle aus dem Wurzelverzeichnis des Repos. Unter Windows `.venv/Scripts/` statt `.venv/bin/`.

### 1. Virtuelle Umgebung und Werkzeuge

```
python -m venv .venv
.venv/bin/pip install -e "tools/spec-check[dev]" -e "tools/testvector-gen[dev]"
.venv/bin/spec-check spec
```

Damit lassen sich `spec/` prüfen und die Testvektoren erzeugen. Für alles Weitere die Umgebung aktivieren (`source .venv/bin/activate` bzw. `.venv\Scripts\activate`).

### 2. Kern (optional für sich)

Nur nötig, wer am Kern arbeitet; das SDK baut ihn selbst mit.

```
cmake -S sdk/core -B build/core -DCMAKE_BUILD_TYPE=Release -G Ninja
cmake --build build/core --config Release
ctest --test-dir build/core -C Release --output-on-failure
```

### 3. Python-SDK

```
pip install -C cmake.define.SBM_VIEWER=OFF "./sdk/python[dev]"
pytest sdk/python
```

- Ohne `SBM_VIEWER=OFF` wird der Viewer mitgebaut; das lädt SDL3 und Dear ImGui und dauert einige Minuten. Für Arbeit an Diensten, API oder Frontend ist er nicht nötig.
- Das Paket wird **nicht** editierbar installiert: Nach jeder Änderung an `sdk/python` oder `sdk/core` neu installieren, sonst testet `pytest` den alten Stand.
- Unter Windows `CMAKE_GENERATOR="Visual Studio 17 2022"` setzen, sonst greift ein MinGW aus Strawberry Perl, falls installiert.

### 4. Dienste und API

```
pip install -e services/store -e "services/runner[dev]" -e "services/gateway[dev]" -e "backend[dev]"
docker run -d --name sbm-test-mongo -p 127.0.0.1:27017:27017 mongo:8.0
pytest services/store
pytest services/runner
pytest services/gateway
pytest backend
```

Diese Pakete sind editierbar installiert. Ohne laufende MongoDB überspringen sich die Datenbanktests; mit `SBM_REQUIRE_MONGO=1` scheitern sie, wie in der CI (siehe [tests-und-ci.md](tests-und-ci.md#schalter-für-tests)).

### 5. Frontend

```
cd frontend
npm ci
npm test
npm run build
```

### 6. C#-SDK (optional)

Braucht das .NET-10-SDK und den Kern als geteilte Bibliothek unter `build/core` (E193).

```
cmake -S sdk/core -B build/core -DCMAKE_BUILD_TYPE=Release -DSBM_BUILD_TESTS=OFF
cmake --build build/core --config Release
dotnet test sdk/csharp/Sbm.slnx
```

Format und Lint aus `sdk/csharp`: `dotnet tool restore`, `dotnet csharpier check .`, `dotnet format Sbm.slnx --verify-no-changes`. Mehr in [code-csharp-sdk.md](code-csharp-sdk.md).

## Stack lokal

Zwei Wege, je nachdem, was geprüft werden soll.

### Ohne Docker, zum Entwickeln

Jeder Dienst in einem eigenen Terminal, alle gegen die Test-MongoDB. Bot-Code läuft hier **ohne Sandbox**; das ist nur für die Referenzbots vorgesehen (E86). Hochgeladene Bots lassen sich so nicht prüfen und nicht spielen.

| Terminal | Befehl | Adresse |
|----------|--------|---------|
| 1 | `SBM_MONGO_URI=mongodb://localhost:27017 sbm-migrate` (einmal und nach jeder neuen Migration) | – |
| 2 | `SBM_MONGO_URI=mongodb://localhost:27017 SBM_PUBLIC_URL=http://localhost:5173 flask --app sbm_api.wsgi run` | `127.0.0.1:5000` |
| 3 | `SBM_MONGO_URI=mongodb://localhost:27017 SBM_SANDBOX=none sbm-runner` | – |
| 4 (für `/play` und Remote-Bots) | `sbm-gateway` | WebSocket `127.0.0.1:8001`, Relay `127.0.0.1:9000` |
| 5 (für `/play` und Remote-Bots) | `SBM_MONGO_URI=mongodb://localhost:27017 SBM_RUNNER_ROLE=play SBM_SANDBOX=none sbm-runner` | – |
| 6 | `npm run dev` in `frontend/` | `http://localhost:5173` |

- Vite reicht `/api` an `SBM_API_URL` (Standard `http://127.0.0.1:5000`) und `/api/v1/play/socket` an `SBM_GATEWAY_URL` (Standard `ws://127.0.0.1:8001`) weiter.
- Erstes Konto: `SBM_MONGO_URI=… SBM_PUBLIC_URL=http://localhost:5173 sbm-invite --role admin` gibt einen Einladungslink aus; im Browser öffnen und Konto anlegen.
- Partien ohne Website ansetzen: `sbm-enqueue Random Material --games 2 --alternate`.
- `SBM_PUBLIC_URL` bestimmt die Links in Einladungen und ob die API Cookies mit `Secure` setzt (nur bei `https://`).
- Eine andere Datenbank als `sbm` wählt `SBM_MONGO_DB`; so bleiben Testdaten und Entwicklungsdaten getrennt.

### Mit Docker, wie auf dem Server

Baut alle Images und startet den Stack mit Sandbox; nötig für Uploads, Verifikation und die Negativ-Suite. Braucht Linux mit cgroup v2 für den Runner (nicht Docker Desktop unter WSL2).

```
docker network create local-web
cp deploy/.env.example deploy/.env      # Passwörter und SBM_PUBLIC_URL eintragen
bash deploy/deploy.sh
docker compose -f deploy/compose.yaml run --rm api sbm-invite --role admin
```

Der Stack veröffentlicht keine Ports; erreichbar ist er über das Netz `local-web`, an dem nur der Container `frontend` hängt (Port 8080 im Container). Lokal entweder einen eigenen Proxy an dieses Netz hängen oder für Versuche in einer nicht eingecheckten Compose-Override-Datei einen Port des `frontend` freigeben. Ablauf und Dienste: [deployment.md](../komponenten/deployment.md).

## Editor

- **Python:** Ruff als Linter und Formatierer, Zeilenlänge 100 (in jeder `pyproject.toml`).
- **C++:** `compile_commands.json` erzeugen mit `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON`; clangd findet dann Kern und Viewer. Format nach `sdk/.clang-format`.
- **TypeScript:** ESLint und Prettier nach `frontend/eslint.config.js` und `frontend/.prettierrc.json`; die API-Typen kommen aus `src/api/schema.d.ts` und werden nie von Hand bearbeitet.
- **Bots:** Die Vorlage `templates/python/` bringt Start- und Debug-Konfigurationen für VS Code mit (E69).

## Häufige Probleme

| Problem | Ursache und Abhilfe |
|---------|---------------------|
| Tests sehen eine Änderung am SDK nicht | Das SDK ist nicht editierbar installiert; neu installieren |
| Unter Windows Linkerfehler beim SDK | MinGW statt MSVC gegriffen; `CMAKE_GENERATOR="Visual Studio 17 2022"` setzen |
| Viewer-Build unter Linux scheitert an SDL | X11-Header fehlen (Liste oben) |
| Alle Datenbanktests „skipped“ | MongoDB läuft nicht oder `SBM_TEST_MONGO_URI` zeigt woanders hin |
| Partie scheitert mit „needs the sandbox, and this runner has none“ | Ohne Sandbox laufen nur Referenzbots; für hochgeladene Bots den Docker-Stack nehmen |
| `sbm-invite` meldet „SBM_PUBLIC_URL is not set“ | Variable setzen, lokal `http://localhost:5173` |
| `npm run build` meldet Typfehler nach API-Änderung | `npm run api-types` vergessen |
