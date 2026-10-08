# Beispiel: Suche mit Zeitgrenze

Ein vollständiger Bot mit Alpha-Beta-Suche, iterativer Vertiefung, einfacher Zugsortierung und Zeitbudget. Er besteht `sbm-check` und schlägt den Referenzbot `material`. Grundlage für eigene Erweiterungen (Transpositionstabelle, Ruhesuche, Stellungsbewertung).

```python
"""Iterative deepening with a time budget per move."""

import sbm

PIECE_VALUES = (100, 320, 330, 500, 900, 0)
MATE = 100_000


class Timeout(Exception):
    pass


def evaluate(board: sbm.Board) -> int:
    """Material from the view of the side to move."""
    bitboards = board.bitboards()
    score = 0
    for piece_type, value in enumerate(PIECE_VALUES):
        score += value * bitboards[piece_type].bit_count()
        score -= value * bitboards[6 + piece_type].bit_count()
    return score if board.side_to_move() == sbm.WHITE else -score


def ordered(board: sbm.Board, moves: list[sbm.Move]) -> list[sbm.Move]:
    """Captures of valuable pieces first."""

    def key(move: sbm.Move) -> int:
        victim = board.piece_at(move.to_square())
        return 0 if victim == sbm.NO_PIECE else -PIECE_VALUES[victim % 6]

    return sorted(moves, key=key)


class DeepeningBot(sbm.Bot):
    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        # A share of the remaining time plus most of the increment, with a margin.
        self.clock = clock
        self.budget_ms = clock.remaining_ms() // 30 + clock.increment_ms() * 3 // 4 - 50
        moves = ordered(board, board.legal_moves())
        best = moves[0]
        for depth in range(1, 64):
            try:
                score, move = self.root(board, moves, depth)
            except Timeout:
                break
            best = move
            moves.remove(move)
            moves.insert(0, move)
            self.report(sbm.Info(depth=depth, score_cp=score, nodes=self.nodes, pv=[move]))
            if clock.elapsed_ms() * 2 > self.budget_ms:
                break
        return best

    def root(self, board: sbm.Board, moves: list[sbm.Move], depth: int) -> tuple[int, sbm.Move]:
        self.nodes = 0
        best_score, best_move = -MATE - 1, moves[0]
        for move in moves:
            board.make_move(move)
            score = -self.search(board, depth - 1, -MATE - 1, -best_score)
            board.undo_move()
            if score > best_score:
                best_score, best_move = score, move
        return best_score, best_move

    def search(self, board: sbm.Board, depth: int, alpha: int, beta: int) -> int:
        self.nodes += 1
        if self.nodes % 1024 == 0 and self.clock.elapsed_ms() > self.budget_ms:
            raise Timeout
        if board.is_checkmate():
            return -MATE
        if board.is_draw():
            return 0
        if depth == 0:
            return evaluate(board)
        for move in ordered(board, board.legal_moves()):
            board.make_move(move)
            score = -self.search(board, depth - 1, -beta, -alpha)
            board.undo_move()
            if score >= beta:
                return beta
            alpha = max(alpha, score)
        return alpha


if __name__ == "__main__":
    sbm.run(DeepeningBot)
```

## Aufbau

| Teil | Zweck |
|------|-------|
| `budget_ms` | Zeit für diesen Zug: ein Dreißigstel der Restzeit plus drei Viertel des Inkrements, minus 50 ms Abstand ([uhr.md](uhr.md)) |
| Schleife über `depth` | Iterative Vertiefung; das Ergebnis der letzten vollständigen Tiefe gilt |
| `Timeout` | Bricht die laufende Tiefe ab; geprüft alle 1024 Knoten, weil jeder Aufruf von `elapsed_ms` Zeit kostet |
| `elapsed_ms() * 2 > budget_ms` | Keine neue Tiefe beginnen, wenn die nächste absehbar nicht mehr fertig wird |
| Bester Zug zuerst | Der Zug der vorigen Tiefe wird in der nächsten zuerst durchsucht und verbessert das Abschneiden |
| `ordered` | Schlagzüge nach Wert des geschlagenen Steins zuerst (vereinfachtes MVV) |
| `report` | Tiefe, Bewertung, Knoten und Zug erscheinen in der Arena mit `--moves` |

Nach einem `Timeout` mitten in `search` bleiben Züge auf dem Brett ausgeführt. Das ist unbedenklich: Das Brett in `choose_move` ist eine Kopie, das SDK führt die Partiestellung getrennt ([bot.md](bot.md)). Wer das Brett nach dem Abbruch weiter nutzen will, nimmt die Züge in einem `try`/`finally` zurück.

## Ausprobieren

```
sbm-check .
sbm-arena bot.py material --games 10 --time 10+0.1 --moves
```

## Mögliche Erweiterungen

| Erweiterung | Hilfsmittel im SDK |
|-------------|--------------------|
| Transpositionstabelle | `board.hash()` als Schlüssel, `move.value()` als gespeicherter Zug |
| Ruhesuche | `board.legal_captures()` |
| Null-Move-Pruning | `board.make_null_move()`, `board.undo_null_move()`, vorher `board.is_check()` prüfen |
| Stellungsbewertung | `board.squares()` oder `board.bitboards()` mit eigenen Tabellen, ggf. per `load_data` |
| Mattdistanz | `MATE - ply` statt `MATE`, Ausgabe als `Info(score_mate=…)`; siehe `sbm/bots/material.py` |
| Eröffnungsbuch | `load_data` in `on_game_start`, Schlüssel `board.hash()` (Polyglot-kompatibel) oder FEN |
