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

Eine Vorlage mit Eröffnungsbuch und Debug-Konfiguration für VS Code liegt unter [`templates/csharp`](https://github.com/DevTGP/SchachBotManager/tree/master/templates/csharp).

## Lizenz

MIT No Attribution (MIT-0).
