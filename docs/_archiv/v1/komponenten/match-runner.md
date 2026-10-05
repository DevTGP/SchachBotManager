# Match-Runner / Referee

Führt genau ein Spiel aus und ist die einzige Instanz, die über Züge, Zeit und Ergebnis entscheidet.

## Aufbau

| Teil | Aufgabe |
|------|---------|
| Job-Consumer | Holt `match`-Jobs atomar aus der Queue, hält Heartbeat |
| Referee | Autoritative Stellung, Zugprüfung, Endbedingungen (eigener Schachkern, unabhängig vom Bot-SDK) |
| Uhr | Bedenkzeit je Seite, Inkrement, Startbudget |
| Spieler-Adapter | `SandboxBotPlayer`, `RemoteBotPlayer`, `HumanPlayer` – gleiche Schnittstelle |
| Sandbox-Treiber | Container erzeugen, einfrieren/fortsetzen, überwachen, entfernen |
| Recorder | Schreibt Züge, Zeiten, Ereignisse fortlaufend in die DB |

## Zeitmodell

- Die Uhr einer Seite läuft von **Absenden von `turn`** bis **Empfang von `move`**.
- Außerhalb des eigenen Zuges ist der Bot-Prozess per cgroup-Freezer **eingefroren**: kein Rechnen in gegnerischer Zeit, Speicherinhalt bleibt erhalten. Damit ist die Anforderung „läuft das ganze Spiel, rechnet aber nur in eigener Zeit“ technisch erzwungen statt nur per Regel verlangt.
- Reihenfolge pro Zug: fortsetzen → `turn` senden → Uhr starten → `move` lesen → Uhr stoppen → einfrieren → prüfen.
- Läuft die Zeit ab, wird der Container sofort beendet; das Spiel endet mit `timeout`.
- **Startbudget** (Prozessstart, JIT, `on_game_start`) ist getrennt von der Bedenkzeit und pro Disziplin konfigurierbar.
- **Toleranz pro Zug** (wenige ms) gleicht Overhead von Fortsetzen/Einfrieren und Pipe-Latenz aus; pro Disziplin einstellbar.
- Sprachfaktoren (E8) werden beim Initialisieren der Uhr angewandt, nicht im Bot.

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

- Ein fest zugewiesener CPU-Kern pro laufendem Spiel (Pinning); da immer nur ein Bot rechnet, reicht ein Kern pro Spiel.
- Runner startet nie mehr Spiele parallel als freie Kerne (abzüglich Reserve für API/DB).
- Liga-Paarungen werden mit beiden Farben gespielt.
- Identische Container-Images und Limits für beide Seiten laut Disziplin.

## Robustheit

- **Heartbeat/Lease** auf dem Job: stirbt ein Runner, wird der Job nach Ablauf wieder frei und das Spiel neu gestartet.
- **Idempotenz:** Ergebnis und Tabellen-Update in einem Schritt mit Schutz gegen doppelte Verbuchung.
- **Aufräumen:** Beim Runner-Start werden verwaiste Container entfernt.
- **Eingaben der Bots sind feindlich:** Längenlimits, Lese-Timeouts, strikte Schema-Prüfung.
- **stderr-Limit:** Logs werden mitgeschnitten, aber ab einer Obergrenze verworfen (kein Blockieren des Bots durch volle Pipes).

## Aufgezeichnete Daten pro Zug

`uci`, `san`, FEN nach dem Zug, verbrauchte Zeit, Restzeit, optionale `info` des Bots. Siehe [datenmodell.md](datenmodell.md).
