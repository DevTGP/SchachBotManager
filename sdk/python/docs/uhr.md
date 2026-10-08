# Uhr (`sbm.Clock`) und Zeiteinteilung

`choose_move` erhält mit jedem Zug ein `Clock`-Objekt. Es ist die lokale Sicht auf die Zeiten; maßgeblich ist die Uhr des Schiedsrichters.

| Methode | Rückgabe |
|---------|----------|
| `remaining_ms()` | Eigene Restzeit zu Beginn dieses Zuges, wie vom Schiedsrichter gesendet. Sinkt während des Nachdenkens **nicht** |
| `opponent_remaining_ms()` | Restzeit des Gegners |
| `increment_ms()` | Zeitgutschrift nach jedem eigenen Zug |
| `elapsed_ms()` | Seit Empfang des Zuges verstrichene Zeit, monoton gemessen |

Alle Werte in Millisekunden. Die tatsächlich noch verfügbare Zeit ist `remaining_ms() - elapsed_ms()`.

## Regeln der Zeitmessung

- Gemessen wird Wanduhrzeit, nicht CPU-Zeit. Für alle Sprachen gelten dieselben Bedingungen.
- Außerhalb des eigenen Zuges ist der Prozess eingefroren; die Uhr läuft nur im eigenen Zug.
- Die Messung des Schiedsrichters enthält zusätzlich die Übertragung. Ein Sicherheitsabstand von einigen zehn Millisekunden ist deshalb nötig.
- Bei Zeitüberschreitung beendet der Server den Prozess sofort. Hat der Gegner noch Mattmaterial, ist die Partie verloren, sonst remis (`timeout_insufficient_material`).
- `on_game_start` hat ein eigenes Budget (`GameInfo.startup_ms`), getrennt von der Bedenkzeit.

## Zeitbudget je Zug

Ein verbreitetes Muster: ein fester Anteil der Restzeit plus der größte Teil des Inkrements, abzüglich eines Abstands.

```python
def budget_ms(clock: sbm.Clock) -> int:
    budget = clock.remaining_ms() // 30 + clock.increment_ms() * 3 // 4 - 50
    return max(budget, 10)
```

Innerhalb der Suche regelmäßig, aber nicht bei jedem Knoten prüfen:

```python
if self.nodes % 1024 == 0 and self.clock.elapsed_ms() > self.budget:
    raise SearchTimeout
```

Bei iterativer Vertiefung wird nach jeder abgeschlossenen Tiefe entschieden, ob die nächste noch beginnt; der Zug der letzten vollständigen Tiefe ist dann die Rückgabe. Ein vollständiges Beispiel steht in [beispiel-suche.md](beispiel-suche.md).

## Lokal testen

| Ziel | Arena-Aufruf |
|------|--------------|
| Kurze Partien | `sbm-arena bot.py material --time 5+0.05 --games 20` |
| Knappe Restzeit | `sbm-arena bot.py material --time 1+0` |
| Ohne Uhr (Debugger) | `sbm-arena tcp material --no-clock` |

Mit `--no-clock` bleiben die Zeiten in `Clock` auf dem Startwert stehen.
