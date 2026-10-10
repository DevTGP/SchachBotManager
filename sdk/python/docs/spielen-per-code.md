# Partien aus dem Code starten (`sbm.play`)

`sbm.play` spielt Partien des eigenen Bots aus einem gewöhnlichen Python-Skript – lokal gegen einen Referenzbot oder eine Bot-Datei, oder gegen einen Bot auf dem Server. Das Skript braucht keine Argumente und keine Umgebungsvariablen (E120).

```python
# start.py, neben bot.py
import sbm
from bot import MyBot

sbm.play(MyBot, "material", games=4)
```

```
python start.py
```

## Parameter

```python
sbm.play(
    bot, opponent, server=None, token=None, color="random", time=None, discipline=None, games=1
)
```

| Parameter | Bedeutung |
|-----------|-----------|
| `bot` | Die Bot-Klasse (nicht eine Instanz); je Partie entsteht eine neue Instanz |
| `opponent` | Ohne `server`: `random`, `material`, eine Bot-Datei (`gegner.py`) oder ein Befehl. Mit `server`: Name eines geprüften Bots auf der Website |
| `server` | Adresse der Website, z. B. `https://schachbotmanager.devtgp.net`; ohne wird lokal gespielt |
| `token` | API-Token von der Kontoseite; fehlt es, gilt `SBM_TOKEN` |
| `color` | Eigene Farbe in der ersten Partie: `white`, `black` oder `random`; danach wechseln die Farben |
| `time` | Bedenkzeit `SEKUNDEN+INKREMENT`, Standard `60+1` |
| `discipline` | Nur mit `server`: Disziplin der Website per Name statt `time` |
| `games` | Zahl der Partien, Standard 1 |

Rückgabe ist eine Liste von `sbm.PlayedGame` in Spielreihenfolge, aus Sicht des eigenen Bots:

| Feld | Inhalt |
|------|--------|
| `game_id` | Lokal `local-1`, `local-2`, …; auf dem Server die ID der Partie |
| `color` | `sbm.WHITE` oder `sbm.BLACK` |
| `opponent_name` | Name des Gegners |
| `result` | `1-0`, `0-1`, `1/2-1/2` oder `*` ohne Ergebnis |
| `termination` | Grund, z. B. `checkmate`, `timeout`; `aborted`, wenn die Verbindung vorher endete |

Nach jeder Partie und am Ende schreibt `play` eine Zeile ins Log, z. B. `score 2.5/4: 2 won, 1 drawn, 1 lost, 0 without result`.

## Lokal

```python
sbm.play(MyBot, "material", color="white", time="10+0.1", games=10)
sbm.play(MyBot, "gegner.py", games=2)
```

- Der eigene Bot läuft in einem Thread des Skripts. Haltepunkte in `choose_move` funktionieren also direkt, etwa mit F5 auf `start.py` in VS Code. Die Uhr läuft dabei weiter; zum Debuggen ohne Uhr bleibt die Arena mit `--no-clock` ([debugging.md](debugging.md)).
- Der eigene Bot wird zwischen den Zügen nicht eingefroren, anders als in der Arena und auf dem Server.
- Der Gegner läuft als eigener Prozess; seine Log-Ausgaben werden nicht angezeigt.
- Ein TCP-Gegner und Disziplinen gehen lokal nicht; dafür `sbm-arena` ([arena.md](arena.md)).

## Gegen Bots auf dem Server

```python
sbm.play(
    MyBot,
    "Material",
    server="https://schachbotmanager.devtgp.net",
    token="sbm_…",
    color="black",
    discipline="Blitz",
    games=2,
)
```

Voraussetzungen, Grenzen und Fehlermeldungen wie bei `--remote` ([remote.md](remote.md)). Der Server erlaubt eine laufende Partie je Token; meldet er `too_many_games`, weil die vorige Partie noch endet, wartet `play` bis zu 30 Sekunden und fragt erneut.

**Das Token ist ein Passwort.** Ein Skript mit Token nicht einchecken und nicht hochladen. Wer das Skript teilen will, lässt `token` weg und setzt `SBM_TOKEN`.

## Fehler

| Fall | Verhalten |
|------|-----------|
| Falsches Argument (Farbe, Zeit, `games`, Disziplin lokal, fehlendes Token) | `InvalidArgumentError` bzw. `TypeError` vor der ersten Partie |
| Ausnahme im Bot | Wird mit Traceback auf `ERROR` geloggt, das Skript endet mit Exit-Code 1 – wie bei `sbm.run` |
| Partie vom Server abgelehnt, Verbindung verloren | Meldung auf `ERROR`, Exit-Code 1 |

## Hochladen

Hochgeladen werden nur `bot.py` und `data/`. `bot.py` endet weiterhin mit `sbm.run(MyBot)`, damit der Bot auf dem Server läuft; `start.py` bleibt auf dem eigenen Rechner.
