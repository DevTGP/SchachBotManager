# Code-Karte: JavaScript-SDK

Das JavaScript-SDK unter `sdk/javascript` ist das npm-Paket `schachbotmanager` (E220–E226): ein Node-API-Addon `sbm.node` mit dem Kern und darüber TypeScript, ausgeliefert als ESM mit `.d.ts`. Es ist Schritt 1 von M5: lokales SDK mit `run` über `stdio` und `tcp`; Upload, `remote`, `play` und Viewer kommen später. Konzepte: [sdk-api.md](../komponenten/sdk-api.md), [bot-protokoll.md](../komponenten/bot-protokoll.md) und [`spec/api/`](../../spec/api/).

## Einstieg

| Einstieg | Ort | Zweck |
|----------|-----|-------|
| `index.ts` | [`src/index.ts`](../../sdk/javascript/src/index.ts) | Alle Exporte des Pakets |
| `run` | [`src/runtime.ts`](../../sdk/javascript/src/runtime.ts) | Einstieg jedes Bots: Optionen lesen, Kanal öffnen, Partien spielen |
| `Board` | [`src/board.ts`](../../sdk/javascript/src/board.ts) | Brett über einem `NativeBoard` des Addons |
| `module.cpp` | [`src/native/module.cpp`](../../sdk/javascript/src/native/module.cpp) | Eingang des Addons: ABI des Kerns prüfen, `NativeBoard` und Zugfunktionen exportieren |
| `build-native.mjs` | [`scripts/build-native.mjs`](../../sdk/javascript/scripts/build-native.mjs) | Baut den Addon mit CMake nach `prebuilds/<platform>-<arch>/sbm.node` |

Lesereihenfolge:

1. `spec/api/*.json`: was die API verspricht; die Namen sind dort in snake_case, hier in camelCase (E224).
2. `src/native.ts`: Schnittstelle `NativeBoard` und Laden des Addons.
3. `src/move.ts`, dann `src/board.ts`: Züge als 16-Bit-Werte mit genau einem Objekt je Wert, Brett darüber.
4. `src/bot.ts`, `src/game.ts`, `src/channel.ts`, `src/runtime.ts`: Partie aus Sicht des Bots.
5. Ein Teil des Addons wie `src/native/board_moves.cpp`.

## Module

| Modul | Aufgabe |
|-------|---------|
| `board.ts`, `move.ts` | `Board` und `Move` (spec `board*.json`, `move.json`); 64-Bit-Werte als `bigint`, mit Endung `32` als `Uint32Array` (E224) |
| `constants.ts`, `errors.ts`, `records.ts` | Konstanten als Zahlen, Fehlerklassen ab `ChessError`, eingefrorene Records (`GameInfo`, `GameResult`, `Info`) |
| `clock.ts`, `log.ts` | Uhr des aktuellen Zuges; Debug-Log auf stderr mit Zeit, Halbzug und Stufe |
| `bot.ts` | Basisklasse `Bot`; `report` merkt sich die Suchinfo, `takeReport` holt sie für die Zugnachricht ab |
| `info.ts` | Kürzt `Info` auf die Grenzen des Protokolls (E43, E63) |
| `protocol.ts`, `channel.ts`, `game.ts` | Nachrichten von Protokoll v1, Zeilenkanal über stdio oder TCP, Zustandsautomat einer Partie |
| `options.ts`, `runtime.ts` | Argumente und Umgebung wie in Python (E61); `run` lenkt `process.stdout` auf stderr um und schreibt das Protokoll direkt auf fd 1 (E225) |
| `data.ts` | `loadData` aus `SBM_DATA_DIR`, sonst `data/` neben dem Hauptmodul (E62) |
| `native.ts` | Lädt `prebuilds/<platform>-<arch>/sbm.node` und gibt ihm die Fehlerklassen |
| `src/native/*.cpp` | Addon mit `node-addon-api`: je Datei der spec ein Teil (`board_moves`, `board_query`, `board_raw`, `board_state`), dazu `status` (Statuscodes als Fehler), `arguments.hpp` und `values.hpp` (Umwandlung der Werte) |

- [`CMakeLists.txt`](../../sdk/javascript/CMakeLists.txt) bindet den Kern über `add_subdirectory(../core)` statisch ein, mit statischer C++-Laufzeit unter MSVC. Die Pfade von `node-api-headers` und `node-addon-api` setzt `build-native.mjs`; direkt mit CMake aufgerufen bricht es ab.
- `npm run build` übersetzt `src/` mit `tsconfig.build.json` nach `dist/`; das Paket enthält `dist/` und `prebuilds/`. In den Quellen und Tests importieren die Module mit Endung `.ts`, Node führt sie ab 22.18 ohne Build-Schritt aus.

### Statische Analyse `src/analysis/` (E227, E228)

| Modul | Aufgabe |
|-------|---------|
| `upload.ts` | Upload-Regeln wie `sbm.analysis.upload` mit Sprache `javascript` |
| `project.ts` | Ordner prüfen wie beim Upload: Auswahl der Dateien, Upload-Regeln, Analyse; für `sbm-check` und den Runner |
| `analyzer.ts` | Alle Quelldateien mit acorn lesen und prüfen, ohne den Bot zu laden |
| `checker.ts`, `walk.ts` | Regeln einer Datei; den AST ohne Rekursion durchgehen |
| `rules.ts`, `javascript-rules.json` | Regelsatz `javascript-1`: Importe, verbotene Namen und Eigenschaften |
| `report.ts` | Befunde und Report, als JSON für den Runner |
| `cli.ts`, `bin.ts` | `sbm-check` mit Exit-Codes 0, 1, 2; `bin.ts` ist der Eintrag `bin` des Pakets und der Analyzer im Runner |

## Tests

`npm test` führt `node --test "test/*.test.ts"` aus. Die Tests brauchen den gebauten Addon, nicht `dist/`.

| Test | Inhalt |
|------|--------|
| `vectors.test.ts` | Alle API-Vektoren aus `spec/testvectors/api/` |
| `surface.test.ts`, `constants.test.ts`, `version.test.ts` | Exporte gegen `spec/api/`, Konstanten, Version gleich der des Kerns |
| `board.test.ts`, `move.test.ts`, `clock.test.ts`, `log.test.ts`, `info.test.ts`, `data.test.ts` | Je Modul |
| `channel.test.ts`, `game.test.ts`, `options.test.ts`, `run.test.ts` | Protokoll, Partie, Optionen, `run` in eigenen Prozessen |
| `analysis.test.ts`, `analysis-project.test.ts`, `analysis-upload.test.ts` | Regeln der Analyse, Auswahl der Dateien, Upload-Regeln |
| `arena.test.ts` | Partien gegen `random` und `material` in `sbm-arena` |
| `template.test.ts` | Vorlage `templates/javascript/`: Buch, Zugwahl, Start als Programm, Konfiguration für VS Code, Partie in der Arena |

| Helfer | Zweck |
|--------|-------|
| `spec.ts` | Liest Dateien unter `spec/` |
| `referee.ts` | Referee mit festem Skript im selben Prozess |
| `bot-process.ts` | Bot aus einem Quelltext in eigenem Node-Prozess starten und seine Antworten lesen |
| `capture.ts` | Sammelt die Zeilen von `Log` statt sie auszugeben |
| `arena-command.ts` | Ruft `sbm-arena` auf (`SBM_ARENA`, sonst aus dem `PATH`); ohne Arena überspringen sich die Tests, mit `SBM_REQUIRE_ARENA=1` scheitern sie |

Die Vorlage importiert `schachbotmanager` von npm; `template.test.ts` testet eine Kopie, die das SDK aus `src/` importiert, deshalb läuft sie ohne `npm install` in der Vorlage.

## Lint und Format

- `npm run lint`: ESLint mit `typescript-eslint` für das Paket, dazu [`scripts/lint-template.mjs`](../../sdk/javascript/scripts/lint-template.mjs) für das reine JavaScript der Vorlage (ESLint prüft nur Dateien unter dem Ordner seiner Konfiguration).
- `npm run format:check`: Prettier für Paket und Vorlage. Die C++-Quellen prüft clang-format wie den Kern (Job `native-format`).

## Erweitern

- **Neue Funktion der Bot-API:** zuerst `spec/api/` und Vektoren (siehe [aenderungen.md](aenderungen.md#protokoll-oder-bot-api-ändern)), dann die Funktion im passenden `src/native/board_*.cpp`, in `NativeBoard` (`native.ts`) und in `Board`; `surface.test.ts` und `vectors.test.ts` zeigen, was fehlt.
- **Neue Plattform:** Eintrag in der Matrix von `.github/workflows/npm.yml`; `native.ts` sucht den Ordner `<process.platform>-<process.arch>`.
