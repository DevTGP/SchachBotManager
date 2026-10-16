# Code-Karte: C#-SDK

Das C#-SDK unter `sdk/csharp` ist die erste Sprache von M5 (E192). Schritt 1 ist umgesetzt: das Binding auf den Kern mit `Board`, `Move`, Konstanten, Fehlern, `PlacedPiece` und `Sdk.Version`. Schritt 2 ist umgesetzt: die Hauptschleife mit `Bot`, `Clock`, `Log`, `Info`, `Sdk.Run` (`stdio`, `tcp`) und `Sdk.LoadData` (E196, E197), der Referenzbot `Material` und der Kreuztest gegen die Python-Arena (E198). Schritt 3 ist umgesetzt: das NuGet-Paket mit dem Kern für alle Plattformen (E199), der Workflow `nuget.yml` (E200) und die Vorlage `templates/csharp` (E201). Serverseite und Viewer folgen in den Schritten 4 und 5. Konzepte: [sdk-api.md](../komponenten/sdk-api.md), [bot-protokoll.md](../komponenten/bot-protokoll.md), [kern-c-schnittstelle.md](../komponenten/kern-c-schnittstelle.md), Form der API in E194.

## Einstieg

| Einstieg | Ort | Zweck |
|----------|-----|-------|
| `Sbm.slnx` | [`sdk/csharp/Sbm.slnx`](../../sdk/csharp/Sbm.slnx) | Lösung mit Bibliothek, Referenzbot und Tests |
| `Directory.Build.props` | [`sdk/csharp/Directory.Build.props`](../../sdk/csharp/Directory.Build.props) | Gemeinsame Einstellungen: `net10.0`, Nullable, Warnungen als Fehler, Analyse `latest-recommended`, `SbmNativeDir`, `SbmCoreVersion` aus `sdk/core/CMakeLists.txt` |
| `Sbm.csproj` | [`src/Sbm/`](../../sdk/csharp/src/Sbm/) | Bibliothek mit Assembly und Paket-ID `SchachBotManager`, Namensraum `Sbm` (nicht `Sbm.dll`, das wäre unter Windows dieselbe Datei wie `sbm.dll`), kopiert die geteilte Bibliothek des Kerns neben die Assembly (E193); Angaben des NuGet-Pakets (E199) |
| `README.md` | [`sdk/csharp/README.md`](../../sdk/csharp/README.md) | Paketseite auf nuget.org |
| `Bot`, `Sdk.Run` | [`src/Sbm/Bot.cs`](../../sdk/csharp/src/Sbm/Bot.cs), [`src/Sbm/Sdk.Run.cs`](../../sdk/csharp/src/Sbm/Sdk.Run.cs) | Einstieg für Bot-Autoren: Unterklasse von `Bot`, in `Main` nur `Sdk.Run<MyBot>()` |
| `Board` | [`src/Sbm/Board.cs`](../../sdk/csharp/src/Sbm/Board.cs) | Brett |
| `Material` | [`bots/Material/`](../../sdk/csharp/bots/Material/) | Referenzbot wie `sbm.bots.material`: Negamax Tiefe 2 mit Material, gleich gute Züge zufällig (E198) |
| `Sbm.Tests` | [`tests/Sbm.Tests/`](../../sdk/csharp/tests/Sbm.Tests/) | xUnit v3: Vektoren, Oberfläche, Konstanten, Fehler, Objekte, Hauptschleife, Referenzbot |
| Kreuztest | [`tests/cross/`](../../sdk/csharp/tests/cross/) | pytest: `Material` in C# gegen die Python-Referenzbots in der Arena (E198), Vorlage gegen das Paket (E201) |
| Vorlage | [`templates/csharp/`](../../templates/csharp/) | Bot für Autoren mit Paket von nuget.org und Debug-Konfiguration für VS Code (E201) |
| `nuget.yml` | [`.github/workflows/nuget.yml`](../../.github/workflows/nuget.yml), [`build-core-shared.sh`](../../.github/scripts/build-core-shared.sh) | Kern je Plattform, Paket, Test der Vorlage, Veröffentlichung (E200) |

Lesereihenfolge:

1. `spec/api/*.json`: was jede Funktion tut.
2. `Native/Core.cs` und eine Datei wie `Native/Core.BoardQuery.cs`: wie die C-Funktionen eingebunden sind.
3. `Native/Status.cs`, `Native/Text.cs`, `Native/BoardHandle.cs`: Fehler, Texte, Handle.
4. `Move.cs`, dann `Board.cs` und die Teile `Board.*.cs`.
5. `tests/Sbm.Tests/VectorTests.cs` mit `VectorCodec.cs`: wie die Vektoren laufen.
6. `spec/protocol/v1/` und `Bot.cs`, dann `Sdk.Run.cs`, `Runtime/Runner.cs`, `Runtime/Game.cs`: wie eine Partie läuft.
7. `bots/Material/MaterialBot.cs`: ein vollständiger Bot.

## Bau

- Der Kern muss als geteilte Bibliothek gebaut sein: `cmake -S sdk/core -B build/core -DCMAKE_BUILD_TYPE=Release -DSBM_BUILD_TESTS=OFF` und `cmake --build build/core --config Release` (`SBM_SHARED` ist Standard). Ergebnis: `build/core/lib/libsbm.so` bzw. `.dylib`, unter Windows `build/core/bin/Release/sbm.dll`.
- `Sbm.csproj` nimmt diese Dateien per Platzhalter aus `$(SbmNativeDir)` und kopiert sie in die Ausgabe; nur die Datei der eigenen Plattform existiert. Ein anderer Ort: `dotnet test -p:SbmNativeDir=…`.
- `[LibraryImport("sbm")]` findet die Datei neben der Assembly. Fehlt sie, scheitert der erste Aufruf mit `DllNotFoundException`.
- Der statische Konstruktor von `Core` vergleicht `sbm_abi_version()` mit `AbiVersion` und bricht bei Abweichung ab.

## Paket

- `dotnet pack sdk/csharp/src/Sbm -c Release -o feed` packt `lib/net10.0/SchachBotManager.dll`, `README.md` und den Kern aus `SbmNativeDir` unter `runtimes/<rid>/native/` – nur für die eigene Plattform (`NETCoreSdkPortableRuntimeIdentifier`, z. B. `linux-x64`). Die Version kommt aus `sdk/core/CMakeLists.txt`.
- Mit `-p:SbmRuntimesDir=<ordner>` packt es stattdessen alles unter `<ordner>/<rid>/native/`. So baut `nuget.yml` das Paket für alle fünf Plattformen aus den Bibliotheken von `.github/scripts/build-core-shared.sh` (E199, E200).
- `build-core-shared.sh RID OUT` baut den Kern mit `SBM_SHARED=ON`: unter Linux im Container `manylinux_2_28` mit `-static-libstdc++ -static-libgcc` und prüft danach mit `readelf`/`objdump`, dass weder `libstdc++` noch ein glibc-Symbol nach 2.28 gebraucht wird; unter Windows mit `CMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded`, unter macOS mit `CMAKE_OSX_DEPLOYMENT_TARGET=11.0`. Lokal braucht der Linux-Fall Docker.
- Die Vorlage verweist auf das Paket in der Version des Kerns; nach einer neuen Version auch `templates/csharp/MyBot.csproj` anpassen, `test_template.py` prüft das.

## Module

### Öffentlich (`src/Sbm/`, Namensraum `Sbm`)

| Modul | Aufgabe |
|-------|---------|
| `Board.cs` | Anlegen (Konstruktor für die Grundstellung, `FromFen`, `Copy`), `Fen`, `Hash`, `MoveHistory`, `ToText`, `ToString`; hält `BoardHandle` |
| `Board.Query.cs` | Eigenschaften der Stellung (`board_query.json`): `PieceAt`, `Pieces`, `SideToMove`, `CastlingRights`, `EnPassantSquare`, Zähler, `KingSquare` |
| `Board.Moves.cs` | Züge (`board_moves.json`): `LegalMoves`, `LegalCaptures`, `AllMovesFrom`, `IsLegal`, `ParseMove`, `MakeMove`, `UndoMove`, Nullzug, `San` |
| `Board.State.cs` | Schach und Endbedingungen (`board_state.json`): `IsCheck`, `IsCheckmate`, `IsDraw`, `IsGameOver` … |
| `Board.Raw.cs` | Rohzugriff (`board_raw.json`): `Bitboard`, `Bitboards`, `Squares`, `Occupied`, `AttacksFrom`, `AttackersOf`, `Checkers`, `Pinned` … |
| `Move.cs` | `readonly struct` mit 16-Bit-Wert; Bitoperationen und Prüfungen im Binding, `Parse` und `Uci` im Kern |
| `PlacedPiece.cs` | Feld und Figur aus `Board.Pieces` (E190) |
| `Sdk.cs` | `Sdk.Version` aus `sbm_version()` |
| `Sdk.Run.cs` | `Sdk.Run<TBot>(viewer)`: eine Partie, bei einem Fehler Ende mit Exit-Code 1; Optionen `--tcp [PORT]`, `--log-level`, `--log-file` bzw. `SBM_TRANSPORT`, `SBM_PORT`, `SBM_LOG_LEVEL`, `SBM_LOG_FILE` (E61, E197); `viewer` und `--remote` melden, dass sie erst mit Schritt 5 kommen |
| `Sdk.LoadData.cs` | `Sdk.LoadData(name)`: Datei aus `SBM_DATA_DIR` bzw. `data/` neben dem Programm (E62) |
| `Bot.cs` | Basisklasse: `ChooseMove`, optional `OnGameStart` und `OnGameEnd`, `Report(Info)` für die Suchinfo des nächsten Zugs |
| `Clock.cs` | Zeit des Zugs: `RemainingMs`, `OpponentRemainingMs`, `IncrementMs`, `ElapsedMs` mit monotoner Uhr ab Empfang von `turn` |
| `Log.cs` | Debug-Log nach stderr (und Datei) mit Zeit, Halbzug und Stufe; Stufen in `Constants/LogLevel.cs` |
| `Info.cs` | Suchinfo zum Zug (E43): Tiefe, Bewertung, Knoten, PV, Text |
| `GameInfo.cs`, `GameResult.cs` | Records für `OnGameStart` und `OnGameEnd` |
| `Constants/*.cs` | Je Typ aus `constants.json` eine statische Klasse mit `const byte` (E194) |
| `Errors/*.cs` | `ChessException` und je Fehler aus `errors.json` eine versiegelte Unterklasse |

### Intern (`src/Sbm/Native/`, Namensraum `Sbm.Native`)

| Modul | Aufgabe |
|-------|---------|
| `Core.cs` | `partial class Core`: Bibliotheksname, ABI-Prüfung, `sbm_version`, `sbm_status_name` |
| `Core.<Header>.cs` | Je Header von `sdk/core/include/sbm/` die `LibraryImport`-Deklarationen |
| `BoardHandle.cs` | `SafeHandle` um `sbm_board*`, gibt mit `sbm_board_free` frei |
| `Status.cs` | Statuscode → Ausnahme mit Funktionsnamen in der Meldung (E52, E194) |
| `Text.cs` | Puffergrößen, ASCII hin und zurück, Prüfung auf NUL im Text |

### Intern (`src/Sbm/Runtime/`, Namensraum `Sbm.Runtime`)

| Modul | Aufgabe |
|-------|---------|
| `Runner.cs` | `Sdk.Run` ohne Prozess: Optionen, Log, Transport, eine Partie, Exit-Code 0 oder 1; testbar mit eingespeister Umgebung und eingespeistem Kanal |
| `Options.cs`, `OptionsParser.cs` | Startoptionen wie `argparse` im Python-SDK; unbekannte Argumente gehören dem Bot |
| `Transports.cs` | `stdio` (stdin/stdout für das Protokoll, `Console.Out` nach stderr umgelenkt) und `tcp` auf `127.0.0.1` (E197) |
| `Channel.cs`, `LineReader.cs` | NDJSON-Zeilen mit Längengrenze |
| `Protocol.cs`, `ProtocolException.cs` | Nachrichten von `spec/protocol/v1/`: Lesen und Prüfen der Referee-Nachrichten, Schreiben von `ready`, `move`, `error` |
| `Game.cs` | Zustandsautomat einer Partie: `init`, `turn`, `game_over` |
| `InfoFields.cs` | `Info` als `info`-Objekt innerhalb der Grenzen des Protokolls, Kürzen und Weglassen mit Warnung (E63) |
| `Guard.cs`, `BotFailureException.cs` | Ausnahmen aus Bot-Code mit Stacktrace ins Log, dann Ende des Prozesses (E49) |
| `DataFiles.cs` | Ort und Namensprüfung der Datendateien |

### Referenzbot (`bots/Material/`, Namensraum `Sbm.Bots`)

| Modul | Aufgabe |
|-------|---------|
| `Program.cs` | `Sdk.Run<MaterialBot>();` |
| `MaterialBot.cs` | Negamax Tiefe 2 mit Materialbewertung über `Bitboards` und `PopCount`, Matt vor Material, gleich gute Züge zufällig; meldet Tiefe, Bewertung und Knoten über `Report` |

Starten: `dotnet run --project sdk/csharp/bots/Material` (stdio) bzw. mit `-- --tcp 7470` gegen `sbm-arena tcp …`.

## Tests

| Datei | Prüft |
|-------|-------|
| `SpecFiles.cs` | Findet `spec/` von der Ausgabe aufwärts, liest Funktionen, Konstanten und alle API-Vektoren (ohne Schemas und `perft.json`) |
| `Names.cs` | `snake_case`/`UPPER_CASE` → PascalCase |
| `VectorCodec.cs` | JSON der Vektoren ↔ C#-Werte (`Move`, `Board` als FEN, `PlacedPiece`, Bitboards als `0x…`) |
| `VectorTests.cs` | Jeder Vektor als eigener Fall: Brett aufbauen, Methode per Reflexion nach dem Namen der Spezifikation aufrufen, Ergebnis, Fehlerklasse und `board_after` vergleichen |
| `ApiSurfaceTests.cs` | Jede Funktion von `spec/api` existiert als Konstruktor, statische oder Instanzmethode mit passender Parameterzahl |
| `ConstantsTests.cs` | Werte gleich `constants.json`, keine zusätzlichen Konstanten |
| `ErrorTests.cs`, `MoveTests.cs`, `BoardTests.cs` | Was kein Vektor abdeckt: Hierarchie, `null` und NUL in Texten, Meldungen, Gleichheit, `ToString`, unabhängige Kopien, langer Verlauf, viele Bretter mit GC |
| `Runtime/RuntimeSurfaceTests.cs` | `Clock`, `Log`, `Bot`, `Run`, `LoadData` und die Records aus `spec/api/runtime.json` existieren mit ihren Parametern (`Play` folgt mit Schritt 5) |
| `Runtime/Referee.cs` | Geskripteter Referee aus den Beispielen von `spec/protocol/v1/examples` |
| `Runtime/GameTests.cs`, `ChannelTests.cs`, `InfoFieldsTests.cs` | Partie gegen den geskripteten Referee, Zeilenrahmen, Grenzen der Suchinfo |
| `Runtime/RunnerTests.cs`, `OptionsParserTests.cs` | Exit-Code, Optionen, Log-Datei, Viewer-Hinweis, TCP |
| `Runtime/ClockTests.cs`, `LogTests.cs`, `DataFilesTests.cs` | Uhr, Log-Format und Stufen, Datendateien |
| `Bots/MaterialBotTests.cs` | Referenzbot auf denselben Stellungen wie die Python-Tests: hängende Dame, gedeckter Bauer, Matt in eins, Matt vermeiden, Zufall bei gleich guten Zügen |
| `../cross/conftest.py` | Fixtures der Sitzung: `core_version`, `dotnet`, `csharp_material` (baut `Material`), `nuget_feed` (`SBM_NUGET_SOURCE` oder `dotnet pack` in ein temporäres Verzeichnis) |
| `../cross/test_cross.py` | Kreuztest mit `Series` und strengem Referee: gegen Python-`material` über stdio, gegen `random` über TCP; jede Partie endet regulär, `ready` meldet `csharp` und die Version des Kerns, jeder C#-Zug trägt `info` |
| `../cross/test_template.py` | Version im Projekt der Vorlage, Assembly und Kern der eigenen Plattform im Paket, Vorlage kopiert, gegen das Paket mit eigenem Paketordner und `-warnaserror` gebaut, zwei Partien gegen Python-`material`, erster Zug aus dem Buch (E201) |

Tests, die Log oder Konsole umlenken, liegen in der Collection `SharedLog` und laufen nicht parallel. Der Kreuztest braucht `dotnet` im `PATH`, das installierte Python-SDK und den Kern unter `build/core`; er baut `Material` und das Paket einmal je Sitzung in ein temporäres Verzeichnis.

Reflexion statt handgeschriebener Aufrufe: So prüfen die Vektoren genau die Namen aus der Spezifikation, und eine neue Funktion in `spec/api` lässt den Test scheitern, bis das Binding sie hat (E195).

## Erweitern

- **Neue Funktion in `spec/api`:** C-Funktion in `Core.<Header>.cs` deklarieren, Methode in der passenden `Board.*.cs` mit PascalCase-Namen, gleichen Parametern und Doku-Kommentar. `ApiSurfaceTests` und `VectorTests` finden sie von selbst; ein neuer Rückgabetyp braucht einen Fall in `VectorCodec.Encode`.
- **Neue Konstante:** In der Klasse unter `Constants/` ergänzen; `ConstantsTests` prüft Wert und Vollständigkeit.
- **Neuer Fehler:** Klasse unter `Errors/`, Fall in `Status.Error`; `ErrorTests` prüft die Hierarchie.
- **Neue Option von `Run`:** zuerst `spec/api/runtime.json`, dann `Options.cs` und `OptionsParser.cs`; `OptionsParserTests` spiegeln `sdk/python/tests/test_options.py`.
- **Neue Nachricht oder neues Feld im Protokoll:** zuerst `spec/protocol/v1/`, dann `Protocol.cs`; `GameTests` laufen über die Beispiele der Spezifikation.
- **Neue Version:** Version in `sdk/core/CMakeLists.txt` und in `templates/csharp/MyBot.csproj`; der Tag `vX.Y.Z` veröffentlicht das Python- und das NuGet-Paket (E70, E200).
- **Neue Plattform:** Zeile in der Matrix von `nuget.yml` (`native` und `test`), Fall in `build-core-shared.sh`, Bibliothek in der Prüfung des Jobs `pack`.
- **Format:** In `sdk/csharp` `dotnet tool restore`, dann `dotnet csharpier format . ../../templates/csharp`; prüfen mit `dotnet csharpier check . ../../templates/csharp` und `dotnet format Sbm.slnx --verify-no-changes`. Der Kreuztest: `ruff check sdk/csharp/tests/cross` und `ruff format --check sdk/csharp/tests/cross`.
