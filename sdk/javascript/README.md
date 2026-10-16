# schachbotmanager

JavaScript-SDK für [SchachBotManager](https://github.com/DevTGP/SchachBotManager), eine Website, auf der Schachbots in Ligen, Turnieren und Einzelspielen gegeneinander antreten. Mit dem Paket schreibt man einen eigenen Bot in JavaScript oder TypeScript: Es bringt Brett, Zuggenerator, Uhr, Log und das Protokoll zum Server mit. Der Bot liefert nur den Zug.

```
npm install schachbotmanager
```

- Node ab 22.18. Das Paket ist ESM mit Typen (`.d.ts`); seine einzige Abhängigkeit ist der Parser `acorn` für `sbm-check`.
- Der Schachkern liegt als fertig übersetzter Node-API-Addon bei, für Windows x64, Linux x64/arm64 (glibc ab 2.28) und macOS x64/arm64 (ab macOS 11). Ein Addon gilt für alle Node-Versionen.
- Die Schachregeln stecken in einem gemeinsamen C++-Kern, den alle SDKs und der Server nutzen. Lokal und auf dem Server gelten also dieselben Regeln.

## Der erste Bot

```js
// bot.js
import * as sbm from "schachbotmanager";

class MyBot extends sbm.Bot {
    chooseMove(board, clock) {
        const captures = board.legalCaptures();
        return captures.length > 0 ? captures[0] : board.legalMoves()[0];
    }
}

if (import.meta.main) {
    await sbm.run(MyBot);
}
```

```
sbm-arena bot.js material --games 10 --pgn games.pgn
```

Die Arena `sbm-arena` gehört zum Python-SDK (`pipx install schachbotmanager`); sie startet `.js`-, `.mjs`- und `.cjs`-Dateien mit `node`. `sbm.run` übernimmt das Protokoll, die Uhr und das Ende der Partie; jede Partie bekommt eine neue Instanz der Klasse. Mit `node bot.js --tcp` verbindet sich der Bot mit einer wartenden Arena (`sbm-arena tcp material --no-clock`), etwa aus dem Debugger.

## Die API im Überblick

Dieselbe API wie im Python-SDK, in camelCase:

| Teil                     | Wichtigste Namen                                                                                                                                                                                                                                                                                                                        |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Bot`                    | `chooseMove(board, clock)` (Pflicht, darf ein Promise liefern), `onGameStart(info)`, `onGameEnd(result)`, `report(info)`                                                                                                                                                                                                                |
| `Board`                  | `legalMoves()`, `legalCaptures()`, `allMovesFrom(sq)`, `isLegal(move)`, `makeMove(move)`, `undoMove()`, `parseMove("e2e4")`, `san(move)`, `fen()`, `Board.fromFen(fen)`, `pieceAt(sq)`, `pieces(color?, pieceType?)`, `sideToMove()`, `kingSquare(color)`, `isCheck()`, `isCheckmate()`, `isDraw()`, `isGameOver()`, `hash()`, `copy()` |
| Rohzugriff auf `Board`   | `bitboard(color, pieceType)`, `occupied()`, `attacksFrom(sq)`, `attackersOf(sq, color)`, `isAttacked(sq, color)`, `checkers()`, `pinned(color)`, `bitboards()`, `squares()`, `makeNullMove()`                                                                                                                                           |
| `Move`                   | `uci()`, `fromSquare()`, `toSquare()`, `promotion()`, `isCapture()`, `isCastling()`, `isEnPassant()`, `Move.parse(uci)`; gleiche Züge sind dasselbe Objekt (`===`)                                                                                                                                                                      |
| `Clock`                  | `remainingMs()`, `opponentRemainingMs()`, `incrementMs()`, `elapsedMs()`                                                                                                                                                                                                                                                                |
| `Log`                    | `trace`, `debug`, `info`, `warn`, `error`, `setLevel`, `isEnabled`                                                                                                                                                                                                                                                                      |
| `Info`                   | Suchinformation zum Zug für `report`: `depth`, `seldepth`, `scoreCp`, `scoreMate`, `nodes`, `pv`, `text`                                                                                                                                                                                                                                |
| `GameInfo`, `GameResult` | Farbe, Gegner, Startstellung, Bedenkzeit, Disziplin bzw. Ergebnis und Grund                                                                                                                                                                                                                                                             |
| `loadData(name)`         | Liest eine mitgelieferte Datendatei (Eröffnungsbuch, Tabellen; bis 1 MB) als `Uint8Array`                                                                                                                                                                                                                                               |
| Konstanten               | `WHITE`, `BLACK`, `PAWN` … `KING`, `WHITE_KNIGHT` …, Felder `A1` … `H8`, `NULL_MOVE`, `RESIGN`                                                                                                                                                                                                                                          |
| Fehler                   | `ChessError` als Basis; `InvalidFenError`, `InvalidUciError`, `IllegalMoveError`, `InvalidStateError`, `InvalidArgumentError`, `DataNotFoundError`                                                                                                                                                                                      |

64-Bit-Werte wie Bitboards und `hash()` sind `bigint`; jede dieser Funktionen gibt es auch mit Endung `32` (`hash32()`, `bitboard32(…)`), die zwei 32-Bit-Hälften als `Uint32Array` liefert, niedrige zuerst.

`console.log` geht auf stderr, stdout gehört dem Protokoll. `Info` und die Ausgaben von `Log` erscheinen in der Arena und im Partie-Viewer der Website.

## Hochladen

Hochgeladene Bots laufen auf dem Server in einer Sandbox (nsjail mit seccomp), vorher wird der Code statisch geprüft. Hochgeladen werden `.js`- und `.mjs`-Dateien und Datendateien direkt in `data/`; jede `.js`-Datei ist ein ES-Modul mit `import` oder `export`. Importiert werden nur eigene Dateien und `schachbotmanager`, nicht `node:`-Module. Namen wie `process`, `globalThis`, `eval` oder `Function` und Eigenschaften wie `constructor` oder `__proto__` sind verboten; Dateien liest der Bot nur über `loadData`. Dieselbe Prüfung läuft lokal:

```
npx sbm-check .
npx sbm-check my-bot --entry main.js --json
```

## Noch nicht enthalten

Partien gegen Bots auf dem Server (`--remote`), `play` und das Viewer-Fenster kommen mit den nächsten Schritten; bis dahin gibt es sie im Python-SDK. `run(MyBot, { viewer: true })` meldet lokal eine Warnung und spielt ohne Fenster.

## Vorlage

Ein lauffähiges [Vorlagenprojekt](https://github.com/DevTGP/SchachBotManager/tree/master/templates/javascript) bringt ein Eröffnungsbuch, Debug-Konfiguration und Arena-Aufgaben für VS Code mit.

## Lizenz

MIT-0.
