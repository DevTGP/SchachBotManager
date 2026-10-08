# Datendateien (`sbm.load_data`)

Eröffnungsbücher, Gewichte, Tabellen: Dateien, die mit dem Bot hochgeladen und zur Laufzeit gelesen werden. `load_data` ist der einzige Weg zu Dateien; `open` ist in Bot-Code verboten ([upload.md](upload.md)).

```python
data: bytes = sbm.load_data("book.txt")
text = data.decode("utf-8")
```

| Umgebung | Gelesen aus |
|----------|-------------|
| Lokal | Ordner `data/` neben der Hauptdatei des Bots (die mit `sbm.run`) |
| Server | Ordner aus `SBM_DATA_DIR`, gesetzt vom Runner |

Projektaufbau:

```
my_bot/
├── bot.py
├── search.py
└── data/
    ├── book.txt
    └── pst.bin
```

## Regeln

| Regel | Wert |
|-------|------|
| Name | Nur ein einfacher Dateiname, ohne `/`, `\`, Laufwerk, `.` oder `..`; sonst `InvalidArgumentError` |
| Ort | Direkt in `data/`, keine Unterordner |
| Fehlt die Datei | `DataNotFoundError` |
| Umfang | Höchstens 100 Dateien und 1 MiB zusammen |
| Inhalt | Beliebig; wird nicht analysiert und nie ausgeführt |

## Wann laden

In `on_game_start`, weil dort das Startbudget gilt und die Bedenkzeit noch nicht läuft:

```python
class BookBot(sbm.Bot):
    def on_game_start(self, info: sbm.GameInfo) -> None:
        self.book = {}
        for line in sbm.load_data("book.txt").decode("utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                position, moves = line.split("|")
                self.book[position.strip()] = moves.split()
```

Das Vorlagenprojekt [`templates/python/`](../../../templates/python/README.md) enthält ein solches Buch samt Beispieldatei.

## Binärdaten

Ohne `struct` (nicht freigegeben) lassen sich Binärdaten mit `array` oder `int.from_bytes` lesen:

```python
import array

table = array.array("h")  # 16 Bit mit Vorzeichen
table.frombytes(sbm.load_data("pst.bin"))
```

Die Byte-Reihenfolge von `array` ist die der Maschine; der Server läuft auf x86-64 (Little Endian).
