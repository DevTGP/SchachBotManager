# Konstanten

Alle Konstanten sind einfache `int`-Werte direkt unter `sbm` (`sbm.WHITE`, `sbm.E4`, `sbm.QUEEN`). Die Kodierung ist Teil der öffentlichen API und in allen Sprachen gleich.

## Farbe

| Name | Wert |
|------|------|
| `WHITE` | 0 |
| `BLACK` | 1 |

Gegenfarbe: `1 - color` bzw. `color ^ 1`.

## Figurentyp

| Name | Wert |
|------|------|
| `PAWN` | 0 |
| `KNIGHT` | 1 |
| `BISHOP` | 2 |
| `ROOK` | 3 |
| `QUEEN` | 4 |
| `KING` | 5 |
| `NO_PIECE_TYPE` | 6 |

## Figur

`farbe * 6 + figurentyp`, also 0–11; `NO_PIECE = 12` für ein leeres Feld.

| Weiß | Wert | Schwarz | Wert |
|------|------|---------|------|
| `WHITE_PAWN` | 0 | `BLACK_PAWN` | 6 |
| `WHITE_KNIGHT` | 1 | `BLACK_KNIGHT` | 7 |
| `WHITE_BISHOP` | 2 | `BLACK_BISHOP` | 8 |
| `WHITE_ROOK` | 3 | `BLACK_ROOK` | 9 |
| `WHITE_QUEEN` | 4 | `BLACK_QUEEN` | 10 |
| `WHITE_KING` | 5 | `BLACK_KING` | 11 |

Index in `board.bitboards()`, Wert in `board.squares()` und `board.piece_at()`.

## Feld

`rang * 8 + linie`, a1 = 0, h1 = 7, a8 = 56, h8 = 63. Konstanten `A1` … `H8`, dazu `NO_SQUARE = 64`.

```python
file, rank = square % 8, square // 8
name = "abcdefgh"[file] + str(rank + 1)
```

Bitboards nutzen dieselbe Nummerierung: Bit *i* = Feld *i*.

## Rochaderechte

Bitmaske aus `board.castling_rights()`.

| Name | Wert |
|------|------|
| `NO_CASTLING` | 0 |
| `WHITE_KINGSIDE` | 1 |
| `WHITE_QUEENSIDE` | 2 |
| `BLACK_KINGSIDE` | 4 |
| `BLACK_QUEENSIDE` | 8 |
| `ALL_CASTLING` | 15 |

## Zug-Flags

| Name | Wert | Bedeutung |
|------|------|-----------|
| `QUIET` | 0 | Ruhiger Zug |
| `DOUBLE_PAWN_PUSH` | 1 | Doppelschritt des Bauern |
| `KING_CASTLE` | 2 | Kurze Rochade |
| `QUEEN_CASTLE` | 3 | Lange Rochade |
| `CAPTURE` | 4 | Schlagzug |
| `EN_PASSANT` | 5 | Schlagen en passant |
| `PROMOTION_KNIGHT` … `PROMOTION_QUEEN` | 8–11 | Umwandlung in Springer, Läufer, Turm, Dame |
| `PROMOTION_CAPTURE_KNIGHT` … `PROMOTION_CAPTURE_QUEEN` | 12–15 | Umwandlung mit Schlagen, gleiche Reihenfolge |

Die Werte 6 und 7 sind ungültig. Bei Umwandlungen ist der Figurentyp `(flags & 3) + 1`.

## Log-Stufen

| Name | Wert |
|------|------|
| `TRACE` | 0 |
| `DEBUG` | 1 |
| `INFO` | 2 |
| `WARN` | 3 |
| `ERROR` | 4 |
| `OFF` | 5 |

## Sonderzüge

`NULL_MOVE` und `RESIGN`, siehe [zuege.md](zuege.md#sonderwerte).
