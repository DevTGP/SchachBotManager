# Code-Karte: C#-SDK

Das C#-SDK unter `sdk/csharp` ist die erste Sprache von M5 (E192). Schritt 1 ist umgesetzt: das Binding auf den Kern mit `Board`, `Move`, Konstanten, Fehlern, `PlacedPiece` und `Sdk.Version`. Hauptschleife, Paket, Serverseite und Viewer folgen in den Schritten 2 bis 5. Konzepte: [sdk-api.md](../komponenten/sdk-api.md), [kern-c-schnittstelle.md](../komponenten/kern-c-schnittstelle.md), Form der API in E194.

## Einstieg

| Einstieg | Ort | Zweck |
|----------|-----|-------|
| `Sbm.slnx` | [`sdk/csharp/Sbm.slnx`](../../sdk/csharp/Sbm.slnx) | Lösung mit Bibliothek und Tests |
| `Directory.Build.props` | [`sdk/csharp/Directory.Build.props`](../../sdk/csharp/Directory.Build.props) | Gemeinsame Einstellungen: `net10.0`, Nullable, Warnungen als Fehler, Analyse `latest-recommended`, `SbmNativeDir` |
| `Sbm.csproj` | [`src/Sbm/`](../../sdk/csharp/src/Sbm/) | Bibliothek mit Assembly und Paket-ID `SchachBotManager`, Namensraum `Sbm` (nicht `Sbm.dll`, das wäre unter Windows dieselbe Datei wie `sbm.dll`), kopiert die geteilte Bibliothek des Kerns neben die Assembly (E193) |
| `Board` | [`src/Sbm/Board.cs`](../../sdk/csharp/src/Sbm/Board.cs) | Brett; Einstieg für Bot-Autoren |
| `Sbm.Tests` | [`tests/Sbm.Tests/`](../../sdk/csharp/tests/Sbm.Tests/) | xUnit v3: Vektoren, Oberfläche, Konstanten, Fehler, Objekte |

Lesereihenfolge:

1. `spec/api/*.json`: was jede Funktion tut.
2. `Native/Core.cs` und eine Datei wie `Native/Core.BoardQuery.cs`: wie die C-Funktionen eingebunden sind.
3. `Native/Status.cs`, `Native/Text.cs`, `Native/BoardHandle.cs`: Fehler, Texte, Handle.
4. `Move.cs`, dann `Board.cs` und die Teile `Board.*.cs`.
5. `tests/Sbm.Tests/VectorTests.cs` mit `VectorCodec.cs`: wie die Vektoren laufen.

## Bau

- Der Kern muss als geteilte Bibliothek gebaut sein: `cmake -S sdk/core -B build/core -DCMAKE_BUILD_TYPE=Release -DSBM_BUILD_TESTS=OFF` und `cmake --build build/core --config Release` (`SBM_SHARED` ist Standard). Ergebnis: `build/core/lib/libsbm.so` bzw. `.dylib`, unter Windows `build/core/bin/Release/sbm.dll`.
- `Sbm.csproj` nimmt diese Dateien per Platzhalter aus `$(SbmNativeDir)` und kopiert sie in die Ausgabe; nur die Datei der eigenen Plattform existiert. Ein anderer Ort: `dotnet test -p:SbmNativeDir=…`.
- `[LibraryImport("sbm")]` findet die Datei neben der Assembly. Fehlt sie, scheitert der erste Aufruf mit `DllNotFoundException`.
- Der statische Konstruktor von `Core` vergleicht `sbm_abi_version()` mit `AbiVersion` und bricht bei Abweichung ab.

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

Reflexion statt handgeschriebener Aufrufe: So prüfen die Vektoren genau die Namen aus der Spezifikation, und eine neue Funktion in `spec/api` lässt den Test scheitern, bis das Binding sie hat (E195).

## Erweitern

- **Neue Funktion in `spec/api`:** C-Funktion in `Core.<Header>.cs` deklarieren, Methode in der passenden `Board.*.cs` mit PascalCase-Namen, gleichen Parametern und Doku-Kommentar. `ApiSurfaceTests` und `VectorTests` finden sie von selbst; ein neuer Rückgabetyp braucht einen Fall in `VectorCodec.Encode`.
- **Neue Konstante:** In der Klasse unter `Constants/` ergänzen; `ConstantsTests` prüft Wert und Vollständigkeit.
- **Neuer Fehler:** Klasse unter `Errors/`, Fall in `Status.Error`; `ErrorTests` prüft die Hierarchie.
- **Format:** In `sdk/csharp` `dotnet tool restore`, dann `dotnet csharpier format .`; prüfen mit `dotnet csharpier check .` und `dotnet format Sbm.slnx --verify-no-changes`.
