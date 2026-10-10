# Python-Vorlage für einen Schachbot

Ein lauffähiger Bot mit Eröffnungsbuch und fertiger Debug-Konfiguration für VS Code. Ordner kopieren, `bot.py` umbauen, hochladen.

| Datei | Inhalt |
|-------|--------|
| `bot.py` | Der Bot: Buchzug aus `data/book.txt`, sonst die Schlagregel in `score` |
| `start.py` | Startet Partien per Code mit `sbm.play`, lokal oder gegen Bots auf dem Server |
| `data/book.txt` | Datendatei, gelesen mit `sbm.load_data("book.txt")`; wird mit hochgeladen |
| `.vscode/launch.json` | Debug-Konfigurationen, die die Arena vorher starten |
| `.vscode/tasks.json` | Arena-Aufgaben: gegen `material` warten, Stellung nachspielen, 10 Partien |
| `requirements.txt` | Das SDK `schachbotmanager` |

## Einrichten

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt      (Linux/macOS: .venv/bin/pip)
```

Für ein System ohne vorkompiliertes Wheel (z. B. Alpine oder 32 Bit) das SDK aus dem Repository bauen: `pip install <Repo>/sdk/python`. Das braucht einen C++-Compiler und CMake.

In VS Code den Ordner öffnen, die empfohlenen Erweiterungen installieren und mit „Python: Select Interpreter“ das `.venv` wählen. Die Aufgaben starten die Arena mit diesem Interpreter.

## Spielen

```
python -m sbm.arena bot.py material --games 10 --pgn games.pgn
```

oder in VS Code die Aufgabe „Arena: 10 Partien gegen material“. Die Partien landen in `games.pgn`.

Ohne Argumente geht es mit `python start.py`: Das Skript importiert `TemplateBot` aus `bot.py` und ruft `sbm.play(TemplateBot, "material", games=2)` auf. Gegner, Farbe, Zeit und Zahl der Partien stehen im Code ([Anleitung](../../sdk/python/docs/spielen-per-code.md)). In VS Code startet „Partien aus start.py“ dasselbe im Debugger; die Uhr läuft dabei weiter.

**Gegen Bots auf dem Server:** In `start.py` den auskommentierten Aufruf mit `server` und dem API-Token von der Kontoseite verwenden. Das Token ist ein Passwort: `start.py` mit Token nicht einchecken und nicht hochladen, oder `token` weglassen und `SBM_TOKEN` setzen.

## Debuggen

1. Haltepunkt in `choose_move` setzen.
2. Unter „Ausführen und Debuggen“ z. B. „Bot debuggen: Weiß gegen material“ starten (F5).
3. VS Code startet zuerst die Arena (`sbm-arena tcp material --no-clock --moves`). Sie wartet auf 127.0.0.1:7470; dann startet der Bot mit `--tcp` im Debugger und verbindet sich.

Die Uhr ist dabei abgeschaltet, Haltepunkte kosten also keine Zeit. Züge und `info` erscheinen im Terminal der Arena, die Ausgaben von `sbm.Log` im Terminal des Bots.

**Stellung nachspielen:** Läuft eine Partie aus `games.pgn` schief, „Bot debuggen: Stellung aus games.pgn, Weiß“ (bzw. „Schwarz“, je nach Farbe des Bots) wählen. VS Code fragt nach der Nummer der Partie und nach der Zahl der Halbzüge; die Arena spielt so weit nach, danach übernehmen die Bots. Die Farbe in der Konfiguration ist die des eigenen Bots, nicht die der Seite am Zug. Nachgespielt wird nur die Stellung: Wiederholungen aus den Zügen davor zählen nicht.

**Arena selbst starten:** Für eigene Optionen die Arena im Terminal starten, z. B. `python -m sbm.arena tcp gegner.py --no-clock --fen "…"`, und dann „Bot debuggen: Arena läuft schon“.

## Andere Entwicklungsumgebungen

Das Muster ist überall gleich: erst die Arena mit `tcp` starten, dann `bot.py --tcp` im Debugger. In PyCharm also die Arena im Terminal starten und eine Run-Konfiguration für `bot.py` mit dem Parameter `--tcp` anlegen.

## Hochladen

Hochgeladen werden `bot.py` und der Ordner `data/` (Datendateien bis 1 MB), nicht `start.py`. Auf dem Server liest der Bot über stdin/stdout, deshalb dort ohne `--tcp`. `print` geht auf stderr, stdout gehört dem Protokoll.
