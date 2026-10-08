# Upload und Regeln für Bot-Code

Hochgeladene Bots laufen auf dem Server in einer Sandbox. Vorher prüft der Server den Code statisch und spielt Testpartien. Dieselben Regeln prüft `sbm-check` lokal.

## Vor dem Upload: `sbm-check`

```
sbm-check                        # aktueller Ordner, Einstieg bot.py
sbm-check my_bot --entry main.py
sbm-check . --exclude 'tests/*' --exclude 'tools/*'
sbm-check . --json
```

```
bot.py:1: import_not_allowed: import os is not allowed
bot.py:6: forbidden_name: the name open is not allowed
sbm-check: 2 problems in 1 files (python-1)
```

| Exit-Code | Bedeutung |
|-----------|-----------|
| 0 | Keine Befunde |
| 1 | Befunde |
| 2 | Falsche Argumente |

`sbm-check` wählt die Dateien wie die Upload-Seite: alle `.py`-Dateien außerhalb versteckter Ordner und `__pycache__`, dazu die Dateien direkt in `data/`. Übergangene Dateien nennt es auf stderr.

## Erlaubte Module

`sbm`, die eigenen Module des Bots und aus der Standardbibliothek:

`__future__`, `array`, `bisect`, `collections`, `collections.abc`, `copy`, `dataclasses`, `enum`, `functools`, `heapq`, `itertools`, `math`, `operator`, `random`, `time`, `typing`

Alles andere ist verboten, auch `os`, `sys`, `struct`, `re`, `json` und Pakete von PyPI. Aus `sbm` sind nur die öffentlichen Namen erlaubt (`sbm.Board`, `sbm.Log` …), nicht `sbm.arena` oder `sbm.referee`.

## Verbotene Sprachmittel

| Regel | Verboten |
|-------|----------|
| Builtins | `eval`, `exec`, `compile`, `__import__`, `open`, `getattr`, `setattr`, `delattr`, `globals`, `locals`, `vars`, `breakpoint`, `input`, `help`, `exit`, `quit` |
| Dunder-Namen | Alle außer `__name__` (lesen), `__all__` und `__slots__` (zuweisen), `.__init__` (z. B. `super().__init__()`) und dem Text `"__main__"`; auch in Zeichenketten |
| Private Attribute | `_x` nur an `self`, `cls`, `super()` und eigenen Modulen |
| Umwege | Frame-, Code- und Traceback-Attribute (`f_globals`, `tb_frame` …), `operator.attrgetter`, `operator.methodcaller`, `typing.get_type_hints`, `ForwardRef` |
| Module als Wert | Ein Modul darf nicht als Wert weitergegeben werden, etwa als Argument |

Folgen für eigenen Code:

- Dateien nur über `sbm.load_data` lesen ([datendateien.md](datendateien.md)).
- Dunder-Methoden wie `__eq__`, `__lt__` oder `__repr__` dürfen definiert werden; verboten ist nur der Zugriff über Namen, Attribute und Texte (`obj.__dict__`, `type(x).__mro__`, `"__class__"`).
- Private Attribute fremder Objekte (`board._x`) sind gesperrt, eigene (`self._cache`) erlaubt.
- Bot-Code muss UTF-8 sein und unter Python 3.14 laufen (Laufzeit auf dem Server).

## Was hochgeladen wird

```
my_bot/
├── bot.py            Einstieg (Standardname), enthält sbm.run(...)
├── search.py         weitere Module, auch in Unterordnern
├── evaluation/
│   └── pst.py
└── data/
    └── book.txt      Datendateien, direkt in data/
```

| Regel | Wert |
|-------|------|
| Quelldateien | `.py`-Dateien außerhalb von `data/`; höchstens 100 Dateien und 1 MiB |
| Datendateien | Direkt in `data/`; höchstens 100 Dateien und 1 MiB |
| Pfade | Jeder Teil beginnt mit Buchstabe, Ziffer oder `_` und enthält nur Buchstaben, Ziffern, `_`, `.` und `-`; höchstens 8 Ebenen und 200 Zeichen; eindeutig auch ohne Rücksicht auf Groß- und Kleinschreibung |
| Einstieg | Eine `.py`-Datei im obersten Ordner, Standard `bot.py`; der Server startet `python /bot/<einstieg>` ohne Argumente |
| Nicht erlaubt | Andere Dateitypen außerhalb von `data/` (Projektdateien, `requirements.txt`, Binaries) |

Das SDK wird nicht mit hochgeladen; der Server stellt es bereit.

## Hochladen

Nur mit Einladung: Nach der Anmeldung auf der Website unter „Meine Bots“ bzw. `/bots/new`.

| Feld | Regel |
|------|-------|
| Name | Wie Nutzernamen; ein vorhandener eigener Name ergibt eine neue Version desselben Bots |
| Version | `X.Y.Z`, jeder Teil 0 bis 999; höher als die letzte Version des Namens |
| Einstieg | Standard `bot.py` |
| Beschreibung | Optional, reiner Text bis 500 Zeichen |
| Dateien | Ordner oder einzelne Dateien; versteckte Ordner und `__pycache__` werden weggelassen |

Höchstens 3 MiB je Upload und 20 Uploads je Tag. Ein hochgeladener Bot ist unveränderlich; Änderungen ergeben eine neue Version.

## Verifikation auf dem Server

Nach dem Upload durchläuft der Bot nacheinander:

| Status | Prüfung |
|--------|---------|
| `analyzing` | Statische Analyse wie `sbm-check` |
| `testing` | Mindesttests gegen den Referenzbot `random`, in der Sandbox |
| `verified` | Bestanden; der Bot kann spielen |
| `rejected` | Gescheitert, mit Stufe und Grund im Report |

Mindesttests, Abbruch beim ersten Fehlschlag:

| Test | Bedingungen |
|------|-------------|
| Einzelstellungen | Fünf Stellungen (Eröffnung, Schach, Umwandlung, en passant, einziger legaler Zug), je ein Zug in 5 s |
| Ganze Partien | Je eine als Weiß und als Schwarz, 10 s + 0,1 s, höchstens 150 Züge |
| Zeitdruck | 2 s für 20 Züge |

Ein Test scheitert bei Niederlage durch Zeit, illegalen Zug, Protokollverstoß, Absturz, Speichergrenze oder Startzeit, wenn der Prozess nach Partieende nicht innerhalb der Nachfrist mit Code 0 endet oder mehr als 1 MiB auf stderr schreibt.

Lokal nachstellen lässt sich das annähernd mit:

```
sbm-check .
sbm-arena bot.py random --games 2 --time 10+0.1 --max-moves 150
sbm-arena bot.py random --time 2+0 --max-moves 20
```

## Sandbox

Zur Orientierung, was zur Laufzeit gilt:

| Grenze | Wert |
|--------|------|
| Speicher | 1 GiB ohne Swap (`GameInfo.memory_limit_mib`), Überschreitung ergibt `memory_limit` |
| Prozesse und Threads | höchstens 128 |
| Dateisystem | Nur lesend; keine Dateien schreibbar |
| Netz | Keines |
| Außerhalb des eigenen Zuges | Prozess eingefroren |
