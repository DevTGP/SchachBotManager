# Log (`sbm.Log`)

Debug-Ausgaben des Bots. `Log` hat nur statische Methoden und wird nicht instanziiert.

| Methode | Wirkung |
|---------|---------|
| `Log.trace(msg)`, `Log.debug(msg)`, `Log.info(msg)`, `Log.warn(msg)`, `Log.error(msg)` | Schreibt auf der jeweiligen Stufe |
| `Log.set_level(level)` | Setzt die Mindeststufe; `sbm.OFF` schreibt nichts |
| `Log.level()` | Aktuelle Mindeststufe |
| `Log.is_enabled(level)` | Ob eine Meldung dieser Stufe geschrieben würde |

Stufen: `TRACE < DEBUG < INFO < WARN < ERROR < OFF`, Startstufe `INFO`.

```python
sbm.Log.info(f"depth {depth} score {score} nodes {self.nodes}")

if sbm.Log.is_enabled(sbm.DEBUG):
    sbm.Log.debug(board.to_text())     # teure Meldung nur bauen, wenn sie erscheint
```

## Format und Ziel

Jede Zeile trägt Uhrzeit, Halbzug und Stufe:

```
14:03:27.512 [ply 12] INFO  depth 6 score 35 nodes 120000
```

| Umgebung | Ziel |
|----------|------|
| Lokal | stderr; in der Arena mit `[Botname]` davor, mit `--quiet` verborgen |
| Lokal mit `--log-file PATH` | Zusätzlich an die Datei angehängt |
| Server | stderr; der Runner behält derzeit nur die letzten 4 KiB für sein Betriebslog. Eine Ansicht für Besitzer ist geplant, aber noch nicht umgesetzt |

## Startstufe setzen

```
python bot.py --tcp --log-level debug
SBM_LOG_LEVEL=trace python bot.py --tcp
```

Ein Aufruf von `Log.set_level` im Code gilt ab dann.

## `print` und stdout

stdout gehört dem Protokoll. Beim Start über stdin/stdout lenkt das SDK stdout auf stderr um, sodass `print` das Protokoll nicht stören kann; die Ausgabe erscheint wie Log-Zeilen, aber ohne Zeit und Stufe. Für dauerhafte Ausgaben ist `Log` gedacht, weil sich die Menge über die Stufe steuern lässt.
