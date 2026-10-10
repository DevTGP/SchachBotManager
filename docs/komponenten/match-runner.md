# Match-Runner / Referee

Führt genau ein Spiel aus und ist die einzige Instanz, die über Züge, Zeit und Ergebnis entscheidet.

Der Referee-Kern (Uhr, Zugprüfung, Endbedingungen, Ablauf eines Spiels) liegt als `sbm.referee` im Python-SDK-Paket und wird vom Runner und von der lokalen Arena gleichermaßen benutzt (E65). Der Runner ergänzt Job-Consumer, Sandbox-Adapter und Recorder.

## Aufbau

| Teil | Aufgabe |
|------|---------|
| Job-Consumer | Holt `match`-Jobs atomar aus der Queue, hält Heartbeat |
| Referee | Autoritative Stellung, Zugprüfung, Endbedingungen; eigene Brett-Instanz auf dem gemeinsamen C++-Kern, getrennt vom Brett im Bot-Prozess |
| Uhr | Bedenkzeit je Seite, Inkrement, Startbudget |
| Spieler-Adapter | `JailPlayer` (Bot in nsjail), `RelayPlayer` (Sitz über den Gateway, E112), `HumanPlayer` (M7 Schritt 2) – gleiche Schnittstelle `sbm.referee.Player` |
| Sandbox-Treiber | Bot-Prozesse über nsjail starten, einfrieren/fortsetzen, überwachen, beenden |
| Recorder | Schreibt Züge, Zeiten, Ereignisse fortlaufend in die DB |

## Zeitmodell

- Gemessen wird **Wanduhrzeit** mit einer monotonen Systemuhr (E19), keine CPU-Zeit: Wer ab Zeitpunkt x 30 Minuten hat, darf bis x+30 rechnen, egal wie viel Rechenzeit der Prozess tatsächlich bekommt.
- Die Uhr einer Seite läuft von **Absenden von `turn`** bis **Empfang von `move`**.
- Außerhalb des eigenen Zuges ist der Bot-Prozess per cgroup-Freezer **eingefroren**: kein Rechnen in gegnerischer Zeit, Speicherinhalt bleibt erhalten. Damit ist die Anforderung „läuft das ganze Spiel, rechnet aber nur in eigener Zeit“ technisch erzwungen statt nur per Regel verlangt.
- Reihenfolge pro Zug: fortsetzen → auf vorzeitig gesendete Zeile prüfen → `turn` senden → Uhr starten → `move` lesen → Uhr stoppen → einfrieren → prüfen.
- Start: Die Bots starten nacheinander (Weiß, dann Schwarz), jeder mit eigenem Startbudget ohne Toleranz; wer es überschreitet, wird sofort eingefroren (E65).
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
| Maximale Zugzahl (Schutz vor Endlospartien, zählt ganze Züge) | Remis |
| Beide Bots starten nicht | Annulliert / beidseitige Niederlage (konfigurierbar) |
| Infrastrukturfehler (Runner-Absturz, Host-Neustart) | Spiel wird verworfen und neu angesetzt, nicht gewertet |

Jedes Ende bekommt einen maschinenlesbaren `termination`-Code (Liste in [bot-protokoll.md](bot-protokoll.md), E44), der im Viewer und in der Bot-Historie angezeigt wird. Starten beide Bots nicht, erhalten beide `startup_timeout` mit Ergebnis `*`; wie das gewertet wird, legt der Wettbewerb fest.

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

### Stand M2 (E72, E75), ergänzt in M3 Schritt 2 (E86)

- Der Runner (`services/runner`, Befehl `sbm-runner`) spielt nur die Referenzbots; andere Bots führen zum Abbruch der Partie (`aborted`) ohne Wiederholung, bis der Upload kommt (E80).
- Mit `SBM_SANDBOX=nsjail` (im Runner-Image) läuft jeder Bot in nsjail in einer eigenen cgroup, die außerhalb seines Zuges eingefroren ist ([sandbox.md](sandbox.md)). Vor der ersten Partie richtet der Runner den cgroup-Baum ein und prüft die Sandbox; scheitert das, beendet er sich mit Code 1. Mit `SBM_SANDBOX=none` (Standard außerhalb des Images) laufen die Referenzbots als eigene Prozesse ohne Sandbox.
- Eine Partie gleichzeitig. Vor jedem Abruf gibt der Runner abgelaufene Leases frei; ist die Queue pausiert, wartet er.
- Infrastrukturfehler (z. B. Datenbank weg): Partie zurücksetzen, nach 30 s neuer Versuch, nach drei Versuchen `aborted`.
- SIGTERM/SIGINT: Bots beenden, Partie und Job zurück in die Queue, Versuch zählt nicht.
- Konfiguration über Umgebungsvariablen: `SBM_MONGO_URI`, `SBM_MONGO_DB` (Standard `sbm`), `SBM_WORKER_ID` (Standard Rechnername und PID), `SBM_LOG_LEVEL`, `SBM_SANDBOX` (`nsjail` oder `none`).
- `sbm-enqueue WEISS SCHWARZ [--time 60+1] [--games N] [--alternate] [--fen …] [--max-moves N] [--startup-ms N] [--priority N] [--discipline NAME]` reiht Partien zwischen Bots nach Namen ein (Entwicklungswerkzeug bis M3, E71).

### Stand M3 Schritt 3 (E89, E92–E94)

- Der Runner spielt auch hochgeladene Bots, aber nur in `verified`; eingereihte Partien anderer Bots bricht er ab, sobald sie an der Reihe sind (E93).
- Neben Partien holt er Verifikationsjobs: zuerst einen, der seit mindestens 15 min wartet, sonst die nächste Partie, sonst den ältesten Verifikationsjob (E89). Mit `SBM_SANDBOX=none` nimmt er nur Partien.
- Die Verifikation (`verification/`) setzt den Bot auf `analyzing`, führt die Analyse aus, dann auf `testing` und die Mindesttests, schreibt den Report und setzt `verified` oder `rejected` ([verifikation.md](verifikation.md)).
- Infrastrukturfehler und verlorene Leases behandelt er wie bei Partien: nach 30 s neu, nach drei Versuchen wird der Bot mit der Stufe `internal` abgelehnt (`verification/rejection.py`).

### Stand M3 Schritt 4 (E95, E96, E98)

- Eingereihte Partien eines zurückgezogenen Bots (`retired`) bricht er ab wie bei einer Sperre (E96).
- Partien durch Coder haben Priorität 50 und kommen damit nach denen der Admins (E98); sonst behandelt er sie gleich.
- Die Seiten einer Partie halten die Version des Bots (E95).

### Stand M4 Schritt 2 (E103, E104)

- Nach jedem Partie-Job verbucht der Worker alle beendeten, gewerteten und noch offenen Partien in der Reihenfolge ihres Endes (`sbm_store.ratings.count_pending`). Ein Datenbankfehler dabei wird nur protokolliert; die nächste Partie holt das nach. Der Play-Runner verbucht ebenso nach jeder interaktiven Partie, Halter ist dort auch das Konto eines Menschen (E117).
- Liegt eine Anforderung zum Neuberechnen vor (E105, nach dem Löschen eines Bots), verbucht der Worker vor seinem nächsten Job alle Ratings neu (`sbm_store.rating_recount`), auch bei pausierter Queue. Das setzt einen einzigen Worker voraus, wie bisher.

## Aufgezeichnete Daten pro Zug

`uci`, `san`, FEN nach dem Zug, verbrauchte Zeit, Restzeit, optionale `info` des Bots. Siehe [datenmodell.md](datenmodell.md).

### Stand M7 Schritt 1 (E111–E113)

- Mit `SBM_RUNNER_ROLE=play` ist `sbm-runner` der Play-Runner: Er nimmt nur Jobs der Art `play` und spielt bis `SBM_PLAY_SLOTS` (Standard 2) interaktive Partien gleichzeitig, jede in einem eigenen Thread mit eigenem Heartbeat (`play/`). Mit der Rolle `queue` (Standard) bleibt alles wie bisher; der Queue-Runner nimmt nie Jobs der Art `play`.
- Bots laufen wie in der Queue in der Sandbox. Jede Seite mit Sitz bekommt eine Relay-Verbindung zum Gateway (`SBM_RELAY_ADDRESS`, Standard `127.0.0.1:9000`); vor dem Start wartet der Play-Runner bis 30 s, bis alle Sitze eingenommen sind.
- Eine Remote-Seite ist ein `RelayPlayer`: Ihre Zeilen gehen unverändert an den Referee und werden wie die eines Bots geprüft. Eine Seite der Art `human` ist ein `HumanPlayer` (E114), der zwischen Referee und Browser (play-v1) übersetzt und über `on_move` jeden Zug sieht.
- Die Plätze kommen aus den Einstellungen auf `/admin/play` (`max_games`), höchstens `SBM_PLAY_SLOTS` (E115).
- Kein Neustart: Infrastrukturfehler, verlorene Leases, ein nicht eingenommener Sitz, ein Client, der länger als 60 s fehlt, und SIGTERM brechen die Partie ab (`aborted`), Einzelheiten in [gateway.md](gateway.md).

### Stand M6 (E152–E154)

- Die Zahlen der Rating-Regel liest `count_pending` aus den Einstellungen (`settings`, Dokument `rating_rule`, E154); ändert ein Admin sie, fordert die Web-API eine Neuberechnung an, die der Worker wie nach E105 ausführt.

- Ein Admin bricht eine laufende Partie ab, indem er ihren Job auf `cancelled` setzt. Der Heartbeat bemerkt beim nächsten Verlängern, dass der Worker den Job nicht mehr hält, und ruft `on_lost`; `stopper.py` beendet dann die Bots der Partie (`stop` an Sandbox- und Klartext-Spielern, auch für Spieler, die erst danach starten).
- Das Ergebnis einer so beendeten Partie wird verworfen: Die Web-API hat sie bereits auf `aborted` gesetzt, der Worker schreibt kein Ergebnis und wiederholt nichts. Bis dahin gespielte Züge bleiben stehen.
- Neuprüfung (E153): Ein Verifikationsjob mit `payload.recheck` durchläuft dieselbe Pipeline, schreibt aber nur einen Report der Art `recheck`. Er ändert weder Status noch `report_id`, `rejection` oder Versionen des Bots; auch ein Fehler des Servers nach drei Versuchen und eine verlorene Lease (`recovery.py`) ergeben nur einen Report.
