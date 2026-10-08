# Erste Schritte

## Installation

```
python -m venv .venv
.venv/bin/pip install schachbotmanager          (Windows: .venv\Scripts\pip)
```

| Voraussetzung | Wert |
|---------------|------|
| Python | 3.11 bis 3.14 |
| Vorkompilierte Wheels | Windows x64, Linux x64/arm64, macOS x64/arm64 |
| Abhängigkeiten | keine |

Für Systeme ohne Wheel (z. B. Alpine/musl oder 32 Bit) wird das SDK aus dem Repository gebaut: `pip install <Repo>/sdk/python`. Das braucht einen C++-Compiler und CMake.

Prüfen:

```
python -c "import sbm; print(sbm.__version__)"
```

Das Paket bringt zwei Befehle mit: `sbm-arena` (lokale Partien, [arena.md](arena.md)) und `sbm-check` (Prüfung vor dem Upload, [upload.md](upload.md)).

## Der kürzeste Bot

`bot.py`:

```python
import random

import sbm


class RandomBot(sbm.Bot):
    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        return random.choice(board.legal_moves())


if __name__ == "__main__":
    sbm.run(RandomBot)
```

- `sbm.Bot` ist die Basisklasse; Pflicht ist nur `choose_move`.
- `sbm.run(RandomBot)` erzeugt eine Instanz, spricht das Protokoll mit dem Schiedsrichter und kehrt nach Partieende zurück.
- `choose_move` erhält die aktuelle Stellung und die Uhr und gibt einen `Move` zurück.

## Erste Partie

```
sbm-arena bot.py random --moves
sbm-arena bot.py material --games 10 --pgn games.pgn
```

`random` und `material` sind die mitgelieferten Referenzbots. Nach mehreren Partien gibt die Arena eine Tabelle aus:

```
Bot       Points  Won  Drawn  Lost  Unfinished
bot            2    2      0     0           0
material       0    0      0     2           0
```

Der Bot direkt mit `python bot.py` gestartet wartet auf Nachrichten des Schiedsrichters über stdin; allein gestartet passiert deshalb nichts. Gespielt wird immer über die Arena oder den Server.

## Ein Bot mit eigener Logik

```python
import sbm

PIECE_VALUES = (100, 300, 300, 500, 900, 0)  # PAWN … KING


class GreedyBot(sbm.Bot):
    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        best_move, best_gain = None, -1
        for move in board.legal_moves():
            board.make_move(move)
            if board.is_checkmate():
                board.undo_move()
                return move
            board.undo_move()
            victim = board.piece_at(move.to_square())
            gain = 0 if victim == sbm.NO_PIECE else PIECE_VALUES[victim % 6]
            if gain > best_gain:
                best_move, best_gain = move, gain
        return best_move


if __name__ == "__main__":
    sbm.run(GreedyBot)
```

Das Brett in `choose_move` gehört dem Bot: Züge dürfen ausgeführt und zurückgenommen werden. Das SDK führt die Partiestellung getrennt, ein vergessenes `undo_move` schadet nicht.

## Nächste Schritte

- Ablauf einer Partie und Callbacks: [bot.md](bot.md)
- Vollständige Brett-API: [brett.md](brett.md)
- Zeiteinteilung: [uhr.md](uhr.md)
- Vorlagenprojekt mit Eröffnungsbuch und Debug-Konfiguration: [`templates/python/`](../../../templates/python/README.md)
