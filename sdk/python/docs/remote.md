# Gegen Bots auf dem Server spielen (`--remote`)

Ein Bot auf dem eigenen Rechner spielt gegen einen geprüften Bot auf dem Server, ohne Upload. Das ist zum Testen gegen echte Gegner gedacht; die Partien werden nie gewertet und erscheinen in keiner öffentlichen Liste.

## Voraussetzungen

| Was | Wo |
|-----|-----|
| Konto mit der Rolle Coder | Einladung durch einen Admin |
| API-Token | Website → Konto → „API-Tokens“ → Token anlegen; es wird nur einmal angezeigt |
| Python-SDK | `pip install schachbotmanager` |

Das Token gehört in die Umgebungsvariable `SBM_TOKEN`, nicht auf die Befehlszeile (dort landet es in der Shell-Historie). Ein verlorenes Token auf der Kontoseite widerrufen.

## Starten

```
export SBM_TOKEN=sbm_…                 (Windows: set SBM_TOKEN=sbm_…)
python bot.py --remote https://schachbotmanager.devtgp.net --opponent Material
python bot.py --remote https://schachbotmanager.devtgp.net --opponent Material --color black --time 300+3
python bot.py --remote https://schachbotmanager.devtgp.net --opponent Material --discipline Blitz
```

Der Bot-Code bleibt unverändert; `sbm.run` erkennt den Transport an `--remote`.

| Argument | Umgebungsvariable | Bedeutung |
|----------|-------------------|-----------|
| `--remote URL` | `SBM_TRANSPORT=remote`, `SBM_REMOTE_URL` | Adresse der Website |
| `--token TOKEN` | `SBM_TOKEN` | API-Token (besser über die Umgebung) |
| `--opponent NAME` | `SBM_OPPONENT` | Name eines geprüften Bots; es spielt seine neueste Version |
| `--color FARBE` | `SBM_COLOR` | `white`, `black` oder `random` (Standard) |
| `--discipline NAME` | `SBM_DISCIPLINE` | Eine Disziplin der Website per Name |
| `--time S+I` | `SBM_TIME` | Freie Bedenkzeit ohne Disziplin, Standard `60+1`; höchstens 30 min + 30 s |

`--log-level` und `--log-file` wirken wie sonst ([log.md](log.md)). Die Argumente `--opponent`, `--color`, `--discipline` und `--time` liest das SDK nur bei `--remote`; ohne bleiben sie dem Bot.

## Ablauf

1. Das SDK fragt die Website nach einer Partie (`POST /api/v1/remote/matches` mit dem Token).
2. Es verbindet sich per WebSocket mit dem Server und nimmt seinen Platz in der Partie ein.
3. Der Server startet den Gegner in der Sandbox; danach läuft die Partie wie in der Arena: `on_game_start`, `choose_move` je Zug, `on_game_end`.
4. Am Ende kehrt `sbm.run` zurück.

## Unterschiede zur Partie auf dem Server

| Punkt | Remote |
|-------|--------|
| Bedenkzeit | Misst der Server. Die Netzlaufzeit hin und zurück zählt zur eigenen Zeit; einen Ausgleich gibt es nicht. Bei langsamer Verbindung eine Zeitkontrolle mit Inkrement wählen |
| Einfrieren | Der eigene Bot wird nicht eingefroren und hat keine Speichergrenze |
| Wertung | Nie gewertet, nicht öffentlich |
| Verbindung | Bricht sie ab, wartet der Server 60 s; danach endet die Partie ohne Ergebnis |
| Grenzen | Eine Partie gleichzeitig und höchstens 50 am Tag, je Token, Konto und Adresse (Admins können das ändern) |

## Fehlermeldungen

| Meldung enthält | Bedeutung |
|-----------------|-----------|
| `a remote game needs SBM_TOKEN` | Token fehlt |
| `unauthenticated` | Token falsch oder widerrufen |
| `forbidden` | Das Konto ist kein Coder (mehr) |
| `invalid_parameter` | Gegner oder Disziplin unbekannt, Zeit außerhalb der Grenzen |
| `too_many_games` | Es läuft noch eine Partie mit diesem Token, Konto oder dieser Adresse |
| `too_many_attempts` | Tageslimit erreicht |
| `no_capacity` | Alle Plätze für interaktive Partien sind belegt; später erneut versuchen |
| `the server refused the seat` | Die Partie wartet nicht mehr, etwa nach einem Neustart des Servers |
