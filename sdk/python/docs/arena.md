# Lokale Arena (`sbm-arena`)

Spielt Partien zwischen zwei Bots auf dem eigenen Rechner, mit demselben Schiedsrichter-Kern wie der Server. Keine Sandbox, kein Server nötig. Auch als `python -m sbm.arena` aufrufbar.

```
sbm-arena WEISS SCHWARZ [Optionen]
```

## Beispiele

```
sbm-arena bot.py random --moves
sbm-arena bot.py material --games 10 --time 10+0.1 --pgn games.pgn
sbm-arena bot.py old_bot.py --games 20 --time 5+0.05
sbm-arena bot.py material --fen "8/8/8/4k3/8/8/4P3/4K3 w - - 0 1" --moves
sbm-arena tcp material --no-clock --moves
sbm-arena tcp material --no-clock --replay games.pgn --replay-game 3 --replay-ply 41
```

## Bot-Angaben

| Angabe | Bedeutung |
|--------|-----------|
| `bot.py` | Läuft mit dem Python, in dem die Arena läuft |
| andere Datei, z. B. `engine.exe` | Wird direkt gestartet |
| Befehlszeile in Anführungszeichen, z. B. `"java -jar bot.jar"` | Wird so gestartet |
| `tcp`, `tcp:PORT` | Arena wartet auf `127.0.0.1` (Standard 7470), bis sich ein Bot mit `--tcp` verbindet; je Partie eine neue Verbindung |
| `random`, `material` | Mitgelieferte Referenzbots; eine eigene Datei dieses Namens als `./random` angeben |

| Referenzbot | Spielweise |
|-------------|-----------|
| `random` | Zufälliger legaler Zug |
| `material` | Alpha-Beta über zwei Halbzüge mit Materialbewertung; übersieht kein Matt in eins und lässt keine Figur direkt hängen |

Der Quelltext beider liegt in `sbm/bots/` und taugt als Vorlage; `material` zeigt Suche, Rohzugriff und `report`.

## Optionen

| Option | Wirkung |
|--------|---------|
| `--games N` | N Partien, Farben wechseln; am Ende eine Punktetabelle |
| `--time S+I` | Bedenkzeit in Sekunden plus Inkrement je Zug, bis zu drei Nachkommastellen; Standard `60+1` |
| `--no-clock` | Keine Zeitgrenzen, für Haltepunkte im Debugger |
| `--fen FEN` | Startstellung |
| `--replay PGN` | Startstellung aus einer aufgezeichneten Partie; nicht zusammen mit `--fen` |
| `--replay-game N` | Partie in der PGN-Datei, Standard 1 |
| `--replay-ply N` | Nachgespielte Halbzüge, Standard alle |
| `--pgn DATEI` | Partien an die Datei anhängen |
| `--moves` | Jeden Zug mit Zeit und Suchinformation ausgeben |
| `--quiet` | Log-Ausgaben der Bots verbergen (sonst auf stderr mit `[Name]` davor) |
| `--startup-ms MS` | Startbudget bis zur Bereitmeldung, Standard 10 000 |
| `--tolerance-ms MS` | Toleranz je Zug für Übertragungszeit, Standard 20 |
| `--max-moves N` | Remis nach so vielen ganzen Zügen, Standard 500 |

## Ausgabe

Mit `--moves`:

```
Game 1/1: bot (White) vs material (Black)
  1. d4            0.012 s  depth 4, score +0.35
  1... h5          0.002 s  depth 2, score +0.00
  ...
  1-0 checkmate: checkmate
```

Nach mehreren Partien:

```
Bot       Points  Won  Drawn  Lost  Unfinished
bot            2    2      0     0           0
material       0    0      0     2           0
```

## Verhalten

- **Einfrieren:** Lokal gestartete Bots werden außerhalb des eigenen Zuges angehalten, samt Kindprozessen, wie auf dem Server. Gelingt das nicht, warnt die Arena. TCP-Bots werden nie eingefroren.
- **Ende:** Nach der Partie hat ein Bot 2 s, um sich selbst zu beenden; danach beendet die Arena ihn.
- **Exit-Codes:** 0 fertig, 1 Fehler der Arena (z. B. Port belegt), 2 falsche Argumente, 130 abgebrochen.
- **Unterschiede zum Server:** Keine Sandbox, keine Speichergrenze, keine statische Analyse. Vor dem Upload deshalb zusätzlich `sbm-check` ausführen ([upload.md](upload.md)).
