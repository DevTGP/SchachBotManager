# schachbotmanager

Python-SDK für [SchachBotManager](https://github.com/DevTGP/SchachBotManager): Schachbrett, Züge und Hauptschleife für eigene Schachbots, dazu die lokale Arena `sbm-arena` und zwei Referenzbots.

```
pip install schachbotmanager
```

Vorkompilierte Wheels für Windows x64, Linux x64/arm64 und macOS x64/arm64, Python 3.11 bis 3.14. Keine weiteren Abhängigkeiten.

## Ein Bot

```python
import sbm


class MyBot(sbm.Bot):
    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        return board.legal_moves()[0]


if __name__ == "__main__":
    sbm.run(MyBot)
```

## Lokal spielen

```
sbm-arena my_bot.py material --games 10 --pgn games.pgn
```

`random` und `material` sind die mitgelieferten Referenzbots; `sbm-arena --help` zeigt alle Optionen. Ein Vorlagenprojekt mit Eröffnungsbuch und Debug-Konfiguration für VS Code liegt unter [`templates/python`](https://github.com/DevTGP/SchachBotManager/tree/master/templates/python).

## Anleitung

Die vollständige Anleitung für Bot-Autoren – Partieablauf, Brett- und Zug-API, Uhr, Log, Datendateien, Arena, Debugging und Upload – liegt unter [`sdk/python/docs`](https://github.com/DevTGP/SchachBotManager/tree/master/sdk/python/docs).
