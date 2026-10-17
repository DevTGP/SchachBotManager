# SchachBotManager

C#-SDK für [SchachBotManager](https://github.com/DevTGP/SchachBotManager), eine Website, auf der Schachbots in Ligen, Turnieren und Einzelspielen gegeneinander antreten. Mit dem Paket schreibt man einen eigenen Bot: Es bringt Brett, Zuggenerator, Uhr, Log und das Protokoll zum Server mit. Der Bot liefert nur den Zug.

```
dotnet add package SchachBotManager
```

- .NET 10. Der Namensraum ist `Sbm`.
- Der Kern für Windows x64, Linux x64/arm64 (glibc ab 2.28) und macOS x64/arm64 (ab macOS 11) liegt im Paket.
- Die Schachregeln stecken in einem gemeinsamen C++-Kern, den alle SDKs und der Server nutzen. Lokal und auf dem Server gelten also dieselben Regeln.

## Der erste Bot

```csharp
using Sbm;

Sdk.Run<MyBot>();

sealed class MyBot : Bot
{
    public override Move ChooseMove(Board board, Clock clock)
    {
        var captures = board.LegalCaptures();
        return captures.Length > 0 ? captures[0] : board.LegalMoves()[0];
    }
}
```

`Sdk.Run` spricht über stdin/stdout mit dem Schiedsrichter, wie auf dem Server; mit `--tcp` verbindet sich der Bot mit einer wartenden Arena. Die Arena ist Teil des Python-SDK:

```
pip install schachbotmanager
sbm-arena tcp material --no-clock
dotnet run -- --tcp
```

## Partien per Code

`Sdk.Play` spielt Partien ohne Arena und ohne Python; den Schiedsrichter stellt das Programm selbst, die Referenzbots `random` und `material` sind eingebaut:

```csharp
foreach (var game in Sdk.Play<MyBot>("material", games: 2, viewer: true))
{
    Console.Error.WriteLine($"{game.Color} {game.Result} {game.Termination}");
}
```

Gegner kann auch eine Bot-Datei (`.py`, `.dll`, Programm) oder eine Befehlszeile sein. Mit `server` und dem API-Token eines Coders (`token` oder `SBM_TOKEN`) spielt der Bot gegen einen Bot der Website; dasselbe geht mit `--remote URL --opponent NAME` beim Start eines Programms mit `Sdk.Run`. `viewer: true` (bei `Sdk.Run` ebenso) öffnet ein Fenster, in dem die Partien live mitlaufen; das Viewer-Programm liegt im Paket.

Eine Vorlage mit Eröffnungsbuch und Debug-Konfiguration für VS Code liegt unter [`templates/csharp`](https://github.com/DevTGP/SchachBotManager/tree/master/templates/csharp).

## Lizenz

MIT No Attribution (MIT-0).
