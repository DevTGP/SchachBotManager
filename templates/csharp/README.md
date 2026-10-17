# C#-Vorlage für einen Schachbot

Ein lauffähiger Bot mit Eröffnungsbuch und fertiger Debug-Konfiguration für VS Code. Ordner kopieren, `TemplateBot.cs` umbauen, hochladen.

| Datei | Inhalt |
|-------|--------|
| `TemplateBot.cs` | Der Bot: Buchzug aus `data/book.txt`, sonst die Schlagregel in `Score` |
| `Program.cs` | Startet den Bot mit `Sdk.Run<TemplateBot>()` |
| `MyBot.csproj` | Projekt für .NET 10 mit dem Paket `SchachBotManager`; kopiert `data/` neben das Programm |
| `data/book.txt` | Datendatei, gelesen mit `Sdk.LoadData("book.txt")`; wird mit hochgeladen |
| `.vscode/launch.json` | Debug-Konfigurationen, die vorher bauen und die Arena starten |
| `.vscode/tasks.json` | Bauen und Arena-Aufgaben: gegen `material` warten, Stellung nachspielen, 10 Partien |

## Einrichten

Gebraucht werden das [.NET 10 SDK](https://dotnet.microsoft.com/download) und für die Arena Python ab 3.11.

```
dotnet build
python -m venv .venv
.venv\Scripts\pip install schachbotmanager      (Linux/macOS: .venv/bin/pip)
```

`dotnet build` holt das Paket `SchachBotManager` von nuget.org; es bringt den Kern für Windows, Linux und macOS auf x64 und Arm64 mit. Die Version im `.csproj` ist die des Servers, beide Pakete (NuGet und PyPI) haben dieselbe Nummer. Die Arena kommt aus dem Python-Paket; die Aufgaben in VS Code rufen sie über das `.venv` in diesem Ordner auf. Ein selbst gepacktes SDK (`dotnet pack sdk/csharp/src/Sbm -c Release -o feed` im Repository) nimmt `dotnet restore --source <pfad>/feed`.

In VS Code den Ordner öffnen und die empfohlenen Erweiterungen installieren.

## Spielen

```
dotnet build -c Release
python -m sbm.arena "dotnet bin/Release/net10.0/MyBot.dll" material --games 10 --pgn games.pgn
```

oder in VS Code die Aufgabe „Arena: 10 Partien gegen material“. Die Partien landen in `games.pgn`.

**Partien per Code, ohne Python:** In `Program.cs` statt `Sdk.Run` z. B. `Sbm.Sdk.Play<MyBot.TemplateBot>("material", games: 2, viewer: true);` aufrufen und `dotnet run` starten. Gegner sind die eingebauten Referenzbots `random` und `material`, eine Bot-Datei (`.py`, `.dll`, Programm) oder eine Befehlszeile; den Schiedsrichter spielt das Programm selbst. Mit `viewer: true` laufen die Partien live in einem Fenster mit. Gegen einen Bot der Website gehen `server` und das API-Token von der Kontoseite mit (`token` oder `SBM_TOKEN`); das Token ist ein Passwort, also nicht einchecken. Für das Debuggen mit der Arena wieder `Sdk.Run` eintragen.

**Gegen Bots auf dem Server über die Kommandozeile:** `SBM_TOKEN=sbm_… dotnet bin/Release/net10.0/MyBot.dll --remote URL --opponent NAME` (optional `--color`, `--time 60+1` oder `--discipline NAME`).

## Debuggen

1. Haltepunkt in `ChooseMove` setzen.
2. Unter „Ausführen und Debuggen“ z. B. „Bot debuggen: Weiß gegen material“ starten (F5).
3. VS Code baut den Bot und startet die Arena (`sbm-arena tcp material --no-clock --moves`). Sie wartet auf 127.0.0.1:7470; dann startet der Bot mit `--tcp` im Debugger und verbindet sich.

Die Uhr ist dabei abgeschaltet, Haltepunkte kosten also keine Zeit. Züge und `Info` erscheinen im Terminal der Arena, die Ausgaben von `Log` im Terminal des Bots.

**Stellung nachspielen:** Läuft eine Partie aus `games.pgn` schief, „Bot debuggen: Stellung aus games.pgn, Weiß“ (bzw. „Schwarz“, je nach Farbe des Bots) wählen. VS Code fragt nach der Nummer der Partie und nach der Zahl der Halbzüge; die Arena spielt so weit nach, danach übernehmen die Bots. Die Farbe in der Konfiguration ist die des eigenen Bots, nicht die der Seite am Zug. Nachgespielt wird nur die Stellung: Wiederholungen aus den Zügen davor zählen nicht.

**Arena selbst starten:** Für eigene Optionen die Arena im Terminal starten, z. B. `python -m sbm.arena tcp gegner.py --no-clock --fen "…"`, und dann „Bot debuggen: Arena läuft schon“.

## Andere Entwicklungsumgebungen

Das Muster ist überall gleich: erst die Arena mit `tcp` starten, dann den Bot mit dem Argument `--tcp` im Debugger. In Visual Studio oder Rider also die Arena im Terminal starten und in den Startoptionen des Projekts `--tcp` eintragen; ohne IDE geht es mit `dotnet run -- --tcp`.

## Hochladen

Hochgeladen werden die `.cs`-Dateien außerhalb von `data/` und der Ordner `data/` (Datendateien bis 1 MB), nicht `Program.cs`, `MyBot.csproj`, `bin/` und `obj/`. Auf `/bots/new` die Bot-Klasse angeben, hier `MyBot.TemplateBot`; den Einstieg mit `Sdk.Run` schreibt der Server selbst. Dort liest der Bot über stdin/stdout. `Console.WriteLine` geht auf stderr, stdout gehört dem Protokoll. Erlaubt sind nur die Teile von .NET, die der Analyzer im Paket zulässt; die IDE meldet Verstöße schon beim Bauen.
