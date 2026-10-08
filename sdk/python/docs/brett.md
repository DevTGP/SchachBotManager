# Brett (`sbm.Board`)

Eine Schachstellung mit Zugverlauf. Alle Regeln (Zuggenerierung, Matt, Remis) kommen aus dem gemeinsamen C++-Kern, denselben, den der Schiedsrichter nutzt.

Felder, Farben und Figuren sind einfache `int`-Werte; die Konstanten stehen in [konstanten.md](konstanten.md).

## Erzeugen und Ausgeben

| Aufruf | Ergebnis |
|--------|----------|
| `sbm.Board()` | Grundstellung |
| `sbm.Board.from_fen(fen)` | Stellung aus FEN; `InvalidFenError` bei fehlerhafter FEN oder unmöglicher Stellung |
| `board.fen()` | FEN der Stellung |
| `board.copy()` | Unabhängige Kopie samt Zugverlauf (auch `copy.copy`, `copy.deepcopy`) |
| `board.hash()` | 64-Bit-Zobrist-Hash mit den Polyglot-Schlüsseln; gleich dem Polyglot-Buchschlüssel |
| `board.move_history()` | Gespielte Züge, ältester zuerst; Nullzüge als `NULL_MOVE` |
| `board.to_text()` bzw. `str(board)` | Lesbares Diagramm plus FEN, zum Debuggen |

```python
>>> board = sbm.Board.from_fen("8/8/8/4k3/8/8/4P3/4K3 w - - 0 1")
>>> print(board)
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . k . . .
. . . . . . . .
. . . . . . . .
. . . . P . . .
. . . . K . . .
8/8/8/4k3/8/8/4P3/4K3 w - - 0 1
```

- `fen()` und `en_passant_square()` nennen das En-passant-Feld nur, wenn das Schlagen legal ist. Gleiche Stellungen ergeben so gleiche FEN.
- `==` vergleicht Bretter nach Identität, nicht nach Stellung. Für Stellungsvergleiche `fen()` oder `hash()` nutzen.
- Das Layout von `to_text()` ist nicht Teil der API.

## Abfragen

| Methode | Rückgabe |
|---------|----------|
| `piece_at(square)` | Figur auf dem Feld, `NO_PIECE` wenn leer |
| `side_to_move()` | `WHITE` oder `BLACK` |
| `castling_rights()` | Bitmaske der verbleibenden Rechte, unabhängig davon, ob gerade rochiert werden kann |
| `en_passant_square()` | Zielfeld eines legalen En-passant-Schlagens, sonst `NO_SQUARE` |
| `halfmove_clock()` | Halbzüge seit dem letzten Schlag- oder Bauernzug |
| `fullmove_number()` | Zugnummer, beginnt bei 1, steigt nach jedem schwarzen Zug |
| `king_square(color)` | Feld des Königs |

Eine Figur ist `farbe * 6 + figurentyp`; Typ und Farbe ergeben sich als `piece % 6` und `piece // 6`.

## Züge

| Methode | Wirkung |
|---------|---------|
| `legal_moves()` | Alle legalen Züge als `list[Move]`, vollständig mit Flags; leer bei Matt oder Patt. Reihenfolge nicht festgelegt |
| `legal_captures()` | Nur Schlagzüge, einschließlich en passant und Umwandlung mit Schlagen |
| `is_legal(move)` | Ob ein legaler Zug mit gleichem Start, Ziel und Umwandlung existiert |
| `parse_move(uci)` | Zug aus UCI-Text, nachgeschlagen in dieser Stellung, mit allen Flags; `InvalidUciError` bzw. `IllegalMoveError` |
| `san(move)` | Kurznotation wie in PGN, z. B. `Nbd7`, `exd6`, `O-O`, `e8=Q+`, `Qxf7#` |
| `make_move(move)` | Führt einen legalen Zug aus; `IllegalMoveError` sonst, das Brett bleibt dann unverändert |
| `undo_move()` | Nimmt den letzten Zug zurück; `InvalidStateError` ohne Verlauf oder wenn der letzte Eintrag ein Nullzug ist |
| `make_null_move()` | Übergibt das Zugrecht (Null-Move-Pruning); `InvalidStateError` im Schach |
| `undo_null_move()` | Nimmt den letzten Nullzug zurück |

```python
for move in board.legal_moves():
    board.make_move(move)
    score = -self.search(board, depth - 1)
    board.undo_move()
```

`make_move` und `is_legal` vergleichen nur Start, Ziel und Umwandlung. Ein Zug aus `Move.parse("e2e4")` ohne Flags wird deshalb angenommen und auf dem Brett mit den richtigen Flags ausgeführt.

## Spielzustand

| Methode | Wahr, wenn |
|---------|-----------|
| `is_check()` | Die Seite am Zug steht im Schach |
| `is_checkmate()` | Schach und kein legaler Zug |
| `is_stalemate()` | Kein Schach und kein legaler Zug |
| `is_repetition(count)` | Die Stellung kam mindestens `count`-mal vor, sie selbst mitgezählt; `is_repetition(3)` ist die dreifache Wiederholung |
| `is_fifty_move_rule()` | `halfmove_clock() >= 100` und kein Matt |
| `has_insufficient_material(color)` | Diese Farbe kann nicht mehr mattsetzen |
| `is_insufficient_material()` | Beide Farben können nicht mehr mattsetzen |
| `is_draw()` | Patt, dreifache Wiederholung, 50-Züge-Regel oder ungenügendes Material – genau wie beim Schiedsrichter |
| `is_game_over()` | Matt oder `is_draw()` |

Zeit, Aufgabe und Zuglimit kennt nur der Schiedsrichter. In einer Suche ist `is_repetition(2)` oft das passendere Remis-Kriterium, weil eine Wiederholung sich vom Gegner erzwingen lässt.

## Rohzugriff

Für eigene Bewertung und Zugsortierung direkt auf den Daten. Ein Bitboard ist ein `int` mit Bit *i* = Feld *i* (a1 = Bit 0, h8 = Bit 63).

| Methode | Rückgabe |
|---------|----------|
| `bitboard(color, piece_type)` | Felder mit Figuren dieser Farbe und Art |
| `bitboards()` | Alle 12 Figuren-Bitboards in einem Aufruf, Index = `Piece` |
| `squares()` | Liste mit 64 Einträgen, Index = Feld, Wert = Figur oder `NO_PIECE` |
| `occupied()`, `occupied_by(color)` | Belegte Felder insgesamt bzw. einer Farbe |
| `piece_count(color, piece_type)` | Anzahl Figuren |
| `attacks_from(square)` | Von der Figur auf dem Feld angegriffene Felder, auch eigene; Bauern nur diagonal; Fesselungen ignoriert |
| `attackers_of(square, color)` | Figuren dieser Farbe, die das Feld angreifen; Fesselungen ignoriert |
| `is_attacked(square, color)` | `attackers_of(square, color) != 0` |
| `checkers()` | Figuren, die der Seite am Zug Schach bieten |
| `pinned(color)` | Figuren dieser Farbe, die an den eigenen König gefesselt sind |

```python
def material(board: sbm.Board) -> int:
    values = (100, 320, 330, 500, 900, 0)
    bitboards = board.bitboards()
    white = sum(v * bitboards[t].bit_count() for t, v in enumerate(values))
    black = sum(v * bitboards[6 + t].bit_count() for t, v in enumerate(values))
    return white - black if board.side_to_move() == sbm.WHITE else black - white


def squares_of(bitboard: int):
    while bitboard:
        low = bitboard & -bitboard
        yield low.bit_length() - 1
        bitboard ^= low
```

## Kosten der Aufrufe

Jeder Aufruf aus Python in den Kern kostet einen festen Betrag, unabhängig von der Arbeit dahinter. Daher:

- Grobkörnige Funktionen bevorzugen: einmal `bitboards()` oder `squares()` statt 64-mal `piece_at`.
- Ergebnisse innerhalb eines Knotens wiederverwenden, statt `legal_moves()` mehrfach aufzurufen.
- Züge lassen sich als `move.value()` (16-Bit-`int`) in Tabellen ablegen und mit `Move.from_value` zurückholen.

## Eigene Bretter

Beliebig viele Bretter sind erlaubt, z. B. `sbm.Board.from_fen(...)` für Tests oder `board.copy()` für eine Nebenrechnung. Alle Aufrufe sind lokal; der Schiedsrichter erfährt nur den Rückgabewert von `choose_move`.

Ein Debugger hält im eigenen Python-Code, nicht in der Zuggenerierung des Kerns. Zum Nachvollziehen dienen `to_text()`, `fen()` und die Ausnahmen ([fehler.md](fehler.md)).
