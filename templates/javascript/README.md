# JavaScript-Vorlage für einen Schachbot

Ein lauffähiger Bot mit Eröffnungsbuch und fertiger Debug-Konfiguration für VS Code. Ordner kopieren, `bot.js` umbauen, gegen andere Bots antreten lassen.

| Datei                 | Inhalt                                                                                                |
| --------------------- | ----------------------------------------------------------------------------------------------------- |
| `bot.js`              | Der Bot: Buchzug aus `data/book.txt`, sonst die Schlagregel in `score`                                |
| `data/book.txt`       | Datendatei, gelesen mit `sbm.loadData("book.txt")`                                                    |
| `package.json`        | Das SDK `schachbotmanager` von npm, die Arena als `npm run arena` und die Prüfung als `npm run check` |
| `.vscode/launch.json` | Debug-Konfigurationen, die die Arena vorher starten                                                   |
| `.vscode/tasks.json`  | Arena-Aufgaben: gegen `material` warten, Stellung nachspielen, 10 Partien                             |

## Einrichten

Node ab 22.18, dann im Ordner:

```
npm install
```

Das Paket bringt den Schachkern fertig übersetzt mit, für Windows (x64), Linux mit glibc ab 2.28 und macOS (je x64 und arm64). Für ein anderes System das SDK aus dem Repository bauen (`npm run build:native` und `npm run build` in `<Repo>/sdk/javascript`, braucht einen C++-Compiler und CMake) und mit `npm install <Repo>/sdk/javascript` einbinden.

Die Arena `sbm-arena` gehört zum Python-SDK. Einmal installieren, z. B. mit `pipx install schachbotmanager` oder `pip install schachbotmanager`, sodass `sbm-arena` im `PATH` liegt. Sie startet `.js`-Dateien mit `node` und spielt auch gegen Bots in Python.

## Spielen

```
sbm-arena bot.js material --games 10 --pgn games.pgn
```

oder `npm run arena` bzw. in VS Code die Aufgabe „Arena: 10 Partien gegen material“. Die Partien landen in `games.pgn`.

## Debuggen

1. Haltepunkt in `chooseMove` setzen.
2. Unter „Ausführen und Debuggen“ z. B. „Bot debuggen: Weiß gegen material“ starten (F5).
3. VS Code startet zuerst die Arena (`sbm-arena tcp material --no-clock --moves`). Sie wartet auf 127.0.0.1:7470; dann startet der Bot mit `--tcp` im Debugger und verbindet sich.

Die Uhr ist dabei abgeschaltet, Haltepunkte kosten also keine Zeit. Züge und `info` erscheinen im Terminal der Arena, die Ausgaben von `sbm.Log` im Terminal des Bots.

**Stellung nachspielen:** Läuft eine Partie aus `games.pgn` schief, „Bot debuggen: Stellung aus games.pgn, Weiß“ (bzw. „Schwarz“, je nach Farbe des Bots) wählen. VS Code fragt nach der Nummer der Partie und nach der Zahl der Halbzüge; die Arena spielt so weit nach, danach übernehmen die Bots. Die Farbe in der Konfiguration ist die des eigenen Bots, nicht die der Seite am Zug. Nachgespielt wird nur die Stellung: Wiederholungen aus den Zügen davor zählen nicht.

**Arena selbst starten:** Für eigene Optionen die Arena im Terminal starten, z. B. `sbm-arena tcp gegner.py --no-clock --fen "…"`, und dann „Bot debuggen: Arena läuft schon“.

## Andere Entwicklungsumgebungen

Das Muster ist überall gleich: erst die Arena mit `tcp` starten, dann `bot.js --tcp` im Debugger. In WebStorm also die Arena im Terminal starten und eine Node-Konfiguration für `bot.js` mit dem Parameter `--tcp` anlegen.

## TypeScript

Das Paket bringt Typen mit. Ein Bot in TypeScript heißt `bot.ts`, importiert genauso aus `schachbotmanager` und läuft ab Node 22.18 ohne Build-Schritt mit `node bot.ts`; in der Arena dann als Befehl `"node bot.ts"`. Hochgeladen wird JavaScript: vorher mit `tsc` nach `.js` übersetzen und die übersetzten Dateien hochladen.

## Hochladen

Hochgeladen werden `bot.js`, weitere `.js`- oder `.mjs`-Dateien und der Ordner `data/` (Datendateien bis 1 MB), nicht `node_modules/` und nicht `package.json`. Vorher prüft `npm run check` (also `sbm-check`) den Ordner wie der Server: erlaubte Dateien, Importe nur aus eigenen Dateien und `schachbotmanager`, keine verbotenen Namen wie `process` oder `eval`. Auf dem Server liest der Bot über stdin/stdout, deshalb dort ohne `--tcp`. `console.log` geht auf stderr, stdout gehört dem Protokoll.
