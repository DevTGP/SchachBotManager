# Viewer-Fenster

Der Viewer zeigt die Partien des eigenen Bots in einem Fenster: live während der Partie und danach Zug für Zug zum Vor- und Zurückspulen (E106, E107). Eingeschaltet wird er im Code, mit dem Argument `viewer=True`:

```python
# start.py
sbm.play(MyBot, "material", games=4, viewer=True)
```

```python
# bot.py
if __name__ == "__main__":
    sbm.run(MyBot, viewer=True)
```

Standard ist `viewer=False`. Ein Fenster gilt für das ganze Programm: Bei `sbm.play` mit mehreren Partien zeigt es alle nacheinander.

## Bedienung

| Taste | Wirkung |
|-------|---------|
| ← / → oder Mausrad über dem Brett | Einen Halbzug zurück bzw. vor |
| Pos1 / Ende | Zum Anfang bzw. zum letzten Zug |
| „Live“ | Wieder der laufenden Partie folgen |
| F | Brett drehen |

Zum gewählten Zug zeigt das Fenster Uhren, Bedenkzeit, die Suchinformation aus `self.report(...)` ([bot.md](bot.md#suchinformation)) und die Log-Zeilen, die der Bot dabei geschrieben hat.

## Ende des Programms

- Nach der letzten Partie wartet das Programm, bis das Fenster geschlossen ist. Strg+C oder das Beenden des Prozesses in der IDE schließt es ebenfalls.
- Startet die Arena den Bot (`sbm-arena bot.py …`), schließt sich das Fenster, sobald die Arena den Bot nach der Partie beendet.

## Wann kein Fenster aufgeht

| Fall | Verhalten |
|------|-----------|
| Umgebungsvariable `SBM_NO_VIEWER` ist gesetzt (nicht leer) | Kein Fenster, ohne Meldung; so lassen sich Tests oder Läufe ohne Bildschirm ausführen |
| Auf dem Server | Kein Fenster: Die Sandbox setzt `SBM_NO_VIEWER`. Ein hochgeladener Bot darf `viewer=True` also behalten |
| Paket ohne Viewer-Programm (eigener Build mit `SBM_VIEWER=OFF`) | Eine Warnung im Log, die Partie läuft ohne Fenster |

Das Programm `sbm-viewer` steckt in jedem Wheel unter `sbm/bin`; es braucht nichts weiter. Unter Linux läuft es unter X11 bzw. XWayland.

## Fehler

`viewer` muss `True` oder `False` sein; sonst wirft `run` bzw. `play` vor der ersten Partie einen `TypeError`.
