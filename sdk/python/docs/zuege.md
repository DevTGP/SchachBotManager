# Züge (`sbm.Move`)

Ein Zug ist intern eine 16-Bit-Ganzzahl und als Objekt unveränderlich.

| Bits | Inhalt |
|------|--------|
| 0–5 | Startfeld |
| 6–11 | Zielfeld |
| 12–15 | Flags ([konstanten.md](konstanten.md#zug-flags)) |

## Erzeugen

| Aufruf | Ergebnis |
|--------|----------|
| `board.parse_move("e2e4")` | Vollständiger Zug mit Flags, nachgeschlagen in der Stellung; empfohlen, wenn ein Brett vorhanden ist |
| `board.legal_moves()` | Alle legalen Züge, vollständig |
| `sbm.Move.parse("e7e8q")` | Zug ohne Brett: Flags nur für Umwandlungen, sonst 0. `0000` wird nicht angenommen |
| `sbm.Move(from_square, to_square, flags)` | Zug aus Teilen, z. B. `sbm.Move(sbm.E2, sbm.E4, sbm.DOUBLE_PAWN_PUSH)`; nicht gegen eine Stellung geprüft |
| `sbm.Move.from_value(value)` | Zug aus dem Rohwert, z. B. aus einer Transpositionstabelle |

Ungültige Teile (Feld > 63, Flags > 15 oder 6/7) lösen `InvalidArgumentError` aus, fehlerhafter UCI-Text `InvalidUciError`.

## Eigenschaften

Alle Eigenschaften sind Methoden.

| Methode | Rückgabe |
|---------|----------|
| `from_square()`, `to_square()` | Start- und Zielfeld (`from_square`, weil `from` in Python reserviert ist) |
| `flags()` | Flags 0–15 |
| `promotion()` | Figurentyp der Umwandlung (`KNIGHT` … `QUEEN`) oder `NO_PIECE_TYPE` |
| `is_promotion()`, `is_capture()`, `is_castling()`, `is_en_passant()` | Aus den Flags abgeleitet; `is_capture` schließt en passant ein |
| `uci()` | UCI-Notation, z. B. `e2e4`, `e7e8q`; Rochade als Königszug `e1g1`. `InvalidArgumentError` für `NULL_MOVE` und `RESIGN` |
| `value()` | Rohwert 0–65535 |

Für die Kurznotation (`Nf3`, `O-O`) dient `board.san(move)`, weil sie die Stellung braucht.

## Vergleich und Hash

`==` und `hash()` vergleichen den Rohwert, also **einschließlich der Flags**:

```python
>>> board = sbm.Board()
>>> board.parse_move("e2e4") == sbm.Move.parse("e2e4")
False          # Flags 1 (Doppelschritt) gegen 0
>>> board.parse_move("e2e4") == sbm.Move(sbm.E2, sbm.E4, sbm.DOUBLE_PAWN_PUSH)
True
```

Züge aus `legal_moves()` und `parse_move` sind untereinander vergleichbar und eignen sich als Schlüssel in `dict` und `set`. Für Vergleiche mit Zügen aus `Move.parse` den UCI-Text (`move.uci()`) oder `board.parse_move` nutzen.

## Sonderwerte

| Wert | Rohwert | Bedeutung |
|------|---------|-----------|
| `sbm.Move.NULL_MOVE` (auch `sbm.NULL_MOVE`) | 0 | Kein Zug; erscheint in `move_history()` nach `make_null_move`. Als Rückgabe von `choose_move` ein Fehler |
| `sbm.Move.RESIGN` (auch `sbm.RESIGN`) | 0xFFFF | Aufgabe, als Rückgabe von `choose_move` |

Beide haben keine UCI-Form.

## Züge in Tabellen

```python
# Speichern als int, Wiederherstellen als Move
self.best_move[board.hash()] = move.value()
...
stored = self.best_move.get(board.hash())
if stored is not None:
    move = sbm.Move.from_value(stored)
```
