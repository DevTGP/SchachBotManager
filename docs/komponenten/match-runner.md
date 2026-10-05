# Match-Runner / Referee

Führt genau ein Spiel aus und ist die einzige Instanz, die über Züge, Zeit und Ergebnis entscheidet.

## Aufbau

| Teil | Aufgabe |
|------|---------|
| Job-Consumer | Holt `match`-Jobs atomar aus der Queue, hält Heartbeat |
| Referee | Autoritative Stellung, Zugprüfung, Endbedingungen; eigene Brett-Instanz auf dem gemeinsamen C++-Kern, getrennt vom Brett im Bot-Prozess |
| Uhr | Bedenkzeit je Seite, Inkrement, Startbudget |
| Spieler-Adapter | `SandboxBotPlayer`, `RemoteBotPlayer`, `HumanPlayer` – gleiche Schnittstelle |
| Sandbox-Treiber | Bot-Prozesse über nsjail starten, einfrieren/fortsetzen, überwachen, beenden |
| Recorder | Schreibt Züge, Zeiten, Ereignisse fortlaufend in die DB |

## Zeitmodell

- Gemessen wird **Wanduhrzeit** mit einer monotonen Systemuhr (E19), keine CPU-Zeit: Wer ab Zeitpunkt x 30 Minuten hat, darf bis x+30 rechnen, egal wie viel Rechenzeit der Prozess tatsächlich bekommt.
- Die Uhr einer Seite läuft von **Absenden von `turn`** bis **Empfang von `move`**.
- Außerhalb des eigenen Zuges ist der Bot-Prozess per cgroup-Freezer **eingefroren**: kein Rechnen in gegnerischer Zeit, Speicherinhalt bleibt erhalten. Damit ist die Anforderung „läuft das ganze Spiel, rechnet aber nur in eigener Zeit“ technisch erzwungen statt nur per Regel verlangt.
- Reihenfolge pro Zug: fortsetzen → `turn` senden → Uhr starten → `move` lesen → Uhr stoppen → einfrieren → prüfen.
- Läuft die Zeit ab, wird der Prozess sofort beendet; das Spiel endet mit `timeout`.
- **Startbudget** (Prozessstart, JIT, `on_game_start`) ist getrennt von der Bedenkzeit und pro Disziplin konfigurierbar.
- **Toleranz pro Zug** (wenige ms) gleicht Overhead von Fortsetzen/Einfrieren und Pipe-Latenz aus; pro Disziplin einstellbar.
- Für alle Sprachen gelten dieselben Zeiten (E8).

## Spielende

| Grund | Ergebnis |
|-------|----------|
| Matt | Sieg |
| Patt, dreifache Wiederholung, 50-Züge-Regel, ungenügendes Material | Remis (automatisch durch den Referee) |
| Zeitüberschreitung | Niederlage; Remis, falls der Gegner mit seinem Material nicht mattsetzen kann |
| Illegaler Zug, Protokollverstoß, Absturz, Speicherlimit, Start-Timeout | Niederlage |
| Aufgabe | Niederlage |
| Maximale Zugzahl (Schutz vor Endlospartien) | Remis |
| Beide Bots starten nicht | Annulliert / beidseitige Niederlage (konfigurierbar) |
| Infrastrukturfehler (Runner-Absturz, Host-Neustart) | Spiel wird verworfen und neu angesetzt, nicht gewertet |

Jedes Ende bekommt einen maschinenlesbaren `termination`-Code, der im Viewer und in der Bot-Historie angezeigt wird.

## Fairness

- Standard: ein Spiel gleichzeitig (E12); Parallelität ist einstellbar. Da immer nur ein Bot rechnet, braucht ein Spiel einen Kern.
- Fester Kern und hohe CPU-Gewichtung für den Bot-Prozess dämpfen Störungen durch andere Dienste auf dem Server; ausschließen lässt sich das bei Wanduhrzeit auf geteilter Hardware nicht (R6).
- Identische Limits für beide Seiten und alle Sprachen laut Disziplin.
- Anzahl der Spiele pro Paarung (und damit Farbverteilung) legt der Wettbewerb fest.

## Robustheit

- **Heartbeat/Lease** auf dem Job: stirbt ein Runner, wird der Job nach Ablauf wieder frei und das Spiel neu gestartet.
- **Idempotenz:** Ergebnis und Tabellen-Update in einem Schritt mit Schutz gegen doppelte Verbuchung.
- **Aufräumen:** Beim Runner-Start werden verwaiste Sandbox-Prozesse und cgroups entfernt.
- **Queue:** Nach Spielende holt der Runner sofort das nächste Spiel (E20); Reihenfolge und Pausen siehe [ligen-turniere.md](ligen-turniere.md).
- **Eingaben der Bots sind feindlich:** Längenlimits, Lese-Timeouts, strikte Schema-Prüfung.
- **stderr-Limit:** Logs werden mitgeschnitten, aber ab einer Obergrenze verworfen (kein Blockieren des Bots durch volle Pipes).

## Aufgezeichnete Daten pro Zug

`uci`, `san`, FEN nach dem Zug, verbrauchte Zeit, Restzeit, optionale `info` des Bots. Siehe [datenmodell.md](datenmodell.md).
