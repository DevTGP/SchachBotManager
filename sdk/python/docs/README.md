# Python-SDK – Anleitung

Anleitung für Bot-Autoren: Wie ein Schachbot mit dem Paket `schachbotmanager` (Import als `sbm`) entsteht, lokal gespielt und getestet wird und auf den Server kommt.

Die Konzeptseite dazu ist [docs/komponenten/sdk-api.md](../../../docs/komponenten/sdk-api.md); maßgeblich für Namen und Verhalten ist die maschinenlesbare Definition unter [`spec/api/`](../../../spec/api/).

## Inhalt

| # | Datei | Thema |
|---|-------|-------|
| 1 | [erste-schritte.md](erste-schritte.md) | Installation, erster Bot, erste Partie |
| 2 | [bot.md](bot.md) | Basisklasse `Bot`, Ablauf einer Partie, `run`, Suchinformation, Aufgeben |
| 3 | [brett.md](brett.md) | `Board`: Abfragen, Züge ausführen und zurücknehmen, Spielzustand, Rohzugriff |
| 4 | [zuege.md](zuege.md) | `Move`: Aufbau, Notation, Vergleich, Sonderwerte |
| 5 | [konstanten.md](konstanten.md) | Farben, Figuren, Felder, Rochaderechte, Zug-Flags |
| 6 | [uhr.md](uhr.md) | `Clock` und Zeiteinteilung |
| 7 | [log.md](log.md) | `Log`, Log-Stufen, Ausgaben |
| 8 | [datendateien.md](datendateien.md) | `load_data` für Eröffnungsbücher und Tabellen |
| 9 | [fehler.md](fehler.md) | Ausnahmen des SDK und Fehler im eigenen Bot |
| 10 | [arena.md](arena.md) | Lokale Partien mit `sbm-arena` |
| 11 | [debugging.md](debugging.md) | Bot im Debugger, Stellungen nachspielen |
| 12 | [upload.md](upload.md) | Regeln für Bot-Code, `sbm-check`, Hochladen |
| 13 | [beispiel-suche.md](beispiel-suche.md) | Vollständiger Bot mit iterativer Vertiefung und Zeitgrenze |
| 14 | [remote.md](remote.md) | Mit API-Token gegen Bots auf dem Server spielen (`--remote`) |
| 15 | [spielen-per-code.md](spielen-per-code.md) | Partien aus einem Skript starten, lokal oder auf dem Server (`sbm.play`) |
| 16 | [viewer.md](viewer.md) | Partien live im Fenster verfolgen und durchspulen (`viewer=True`) |

## Auf einen Blick

```python
import sbm


class MyBot(sbm.Bot):
    def choose_move(self, board: sbm.Board, clock: sbm.Clock) -> sbm.Move:
        captures = board.legal_captures()
        return captures[0] if captures else board.legal_moves()[0]


if __name__ == "__main__":
    sbm.run(MyBot)
```

```
pip install schachbotmanager
sbm-arena my_bot.py material --games 10 --pgn games.pgn
sbm-check .
```

- Das SDK übernimmt Protokoll, Schachregeln, Uhr und Log. Der Bot liefert nur den Zug.
- Dieselbe Datei läuft lokal, im Debugger und auf dem Server; nur Argumente bzw. Umgebungsvariablen unterscheiden sich.
- Ein lauffähiges Vorlagenprojekt mit VS-Code-Konfiguration liegt unter [`templates/python/`](../../../templates/python/README.md).
