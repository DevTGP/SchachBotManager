# Verifikation (Upload-Pipeline)

Jeder Upload durchläuft die Pipeline vollständig, bevor der Bot an Spielen teilnehmen darf. Die Pipeline läuft als Job im Runner; Partien haben Vorrang, ein Verifikationsjob nach 15 min Wartezeit aber vor der nächsten Partie (E81, E89). Quell- und Datendateien liegen in GridFS (E82, E94).

Umgesetzt ist die Pipeline für Python (E92): Annahme, Analyse, Mindesttests und automatische Freigabe; Build und Artefaktprüfung entfallen bei Python.

## Stufen

| # | Stufe | Prüft | Ort |
|---|-------|-------|-----|
| 1 | Annahme | Rolle des Nutzers, Upload-Rate, Dateitypen, Größen, Struktur (keine Pfad-Tricks, keine Symlinks) | Web-API |
| 2 | Statische Analyse | Regeln aus [statische-analyse.md](statische-analyse.md) | Runner (E81) |
| 3 | Build | Kompilieren/Paketieren mit festen, serverseitigen Build-Einstellungen; Zeit- und Speicherlimit | Sandbox (Build-Verzeichnis) |
| 4 | Artefaktprüfung | Größe, bei Java/C# referenzierte APIs im Kompilat | Runner (E81) |
| 5 | Mindesttests | siehe unten | Sandbox (Laufzeitverzeichnis) |
| 6 | Freigabe | Automatisch nach bestandenen Tests; Admins können sperren und wieder freigeben (E93) | Runner, Web-API |

## Inhalt eines Uploads (E30)

| Teil | Regel |
|------|-------|
| Quelldateien | Eine oder mehrere Dateien der gewählten Sprache, auch in Unterordnern; eine Datei ist als Einstieg markiert (enthält die Bot-Klasse) |
| Datendateien | Beliebige Binär-/Textdateien (Eröffnungsbuch, Gewichte, Tabellen), zusammen höchstens 1 MB |
| Form | Mehrere Dateien direkt im Browser auswählbar oder als ein Archiv; Obergrenzen für Dateianzahl und Gesamtgröße des Quellcodes |
| Nicht erlaubt | Build-Dateien (Projektdateien, Makefiles, Paketlisten), fertige Binaries, Dateien anderer Sprachen |

- Datendateien werden nicht analysiert und nie ausgeführt. Der Bot liest sie ausschließlich über die SDK-Funktion `load_data(name)`; direkter Dateizugriff bleibt verboten.
- Die statische Analyse läuft über **alle** Quelldateien; Importe zwischen eigenen Dateien sind erlaubt.
- Der Build läuft mit serverseitig gestellten Einstellungen über alle Quelldateien.

### Python (E92)

| Regel | Wert |
|-------|------|
| Quelldateien | `.py`-Dateien außerhalb von `data/`, auch in Unterordnern; höchstens 100 Dateien und 1 MiB |
| Datendateien | Direkt in `data/`, weil `load_data` nur einfache Namen nimmt (E62); höchstens 100 Dateien und 1 MiB |
| Pfade | Teile beginnen mit Buchstabe, Ziffer oder `_` und enthalten nur Buchstaben, Ziffern, `_`, `.` und `-`; höchstens 8 Ebenen und 200 Zeichen; eindeutig auch ohne Rücksicht auf Groß- und Kleinschreibung, keine Datei heißt wie ein Ordner |
| Einstieg | Eine `.py`-Datei im obersten Ordner, Standard `bot.py`; der Bot startet als `python /bot/<entry>` |
| Form | Ein Ordner oder einzelne Dateien im Browser; die Upload-Seite lässt versteckte Ordner, `__pycache__` und alles Übrige weg und zeigt es an |

Dieselben Regeln (`sbm.analysis.upload`) prüfen die Web-API bei der Annahme, der Runner beim Bereitstellen der Dateien (E94) und `sbm-check` vor dem Upload.

## Mindestanforderungen (Stufe 5)

| Test | Kriterium |
|------|-----------|
| Start | `ready` innerhalb des Startbudgets |
| Legale Züge | Legaler Zug in einer Reihe vorgegebener Stellungen (Eröffnung, Schach, Umwandlung, en passant, einziger legaler Zug) |
| Beide Farben | Vollständige Partie als Weiß und als Schwarz gegen einen Referenz-Zufallsbot ohne Regelverstoß |
| Zeitverhalten | Hält eine kurze Zeitkontrolle ein; reagiert bei knapper Restzeit |
| Speicher | Bleibt in einer Testpartie unter der festen Schutzgrenze |
| Stabilität | Kein Absturz, sauberes Beenden nach `game_over` |
| Ausgabe | Kein Protokollbruch durch eigene stdout-Ausgaben, Log-Menge im Rahmen |

Die Tests laufen mit einer kurzen Standard-Zeitkontrolle und den festen Schutzgrenzen der Sandbox.

Umsetzung für Python (E92): Gegner ist der Referenzbot `random`, ebenfalls in der Sandbox. Die Tests enden beim ersten Fehlschlag.

| Test | Bedingungen |
|------|-------------|
| `position_opening`, `position_check`, `position_promotion`, `position_en_passant`, `position_only_move` | Ein Zug des Bots aus der Stellung, 5 s |
| `game_white`, `game_black` | Partie als Weiß bzw. Schwarz, 10 s + 0,1 s, höchstens 150 Züge |
| `time_pressure` | Partie als Weiß mit 2 s ohne Inkrement, höchstens 20 Züge |

Ein Test scheitert, wenn der Bot durch Zeit, illegalen Zug, Protokollverstoß, Absturz, Speichergrenze oder Startzeit verliert, nach `game_over` nicht innerhalb der Nachfrist mit Code 0 endet oder mehr als 1 MiB auf stderr schreibt.

## Status eines Bots

```
uploaded → analyzing → building → testing → verified
                 ↘         ↘          ↘
                          rejected
verified ↔ retired (Besitzer)
verified, retired → disabled (Admin)   disabled → verified (Admin)
```

Bei Python fehlt `building`. Admins sperren und geben frei (E93, E96); der Besitzer zieht einen geprüften Bot zurück und aktiviert ihn wieder, eine Sperre kann er nicht aufheben (E96). Kann der Server einen Bot dreimal nicht prüfen (Infrastrukturfehler), wird er mit der Stufe `internal` abgelehnt (E89).

- Der Report (Stufe, Regel, Datei/Zeile, Build-Ausgabe gekürzt, Testprotokoll) ist für Besitzer und Admin einsehbar. Er liegt in `verification_reports` mit Regelsatz und den Versionen von Python und SDK; der Bot verweist über `report_id` darauf und hält Stufe und Grund einer Ablehnung in `rejection`.
- Der Quellcode ist ausschließlich für Besitzer und Admin abrufbar (E15).
- Quellcode und Artefakt eines Bots sind nach dem Upload **unveränderlich** (E6). Bearbeitbar bleiben nur Metadaten (Name, Beschreibung) und Anmeldungen.

## Versionen (E6)

- „Bearbeiten“ des Codes erzeugt einen **neuen Bot** mit Verweis auf den Vorgänger (`lineage_id`, `parent_bot_id`, `version_no`). Ein Upload unter einem eigenen Namen ist eine neue Version; die Versionsnummer `X.Y.Z` vergibt der Besitzer, sie muss steigen (E91).
- Der neue Bot durchläuft die Pipeline vollständig, hat eigene Historie und beginnt in der untersten Liga.
- Die UI gruppiert Versionen einer Abstammung und kann Partien zwischen Versionen ansetzen (Einzelspiele).
- Keine Obergrenze für aktive Versionen einer Abstammung (E14); nicht mehr benötigte Versionen werden deaktiviert.

## Zu beachten

- **Speicherung:** Quellcode, Artefakt und Report mit Hash ablegen; Version des Laufzeitverzeichnisses und SDK-Version am Bot speichern.
- **Missbrauch:** 20 Uploads je Konto und Tag (E92); Pipeline-Jobs haben niedrigere Priorität als Partien (E89).
- **Determinismus:** Die Stellungen sind fest, der Zufallsbot spielt ohne festen Seed. Ein regelkonformer Bot besteht unabhängig von dessen Zügen; der Report nennt Test, Ende und Grund (E92).
- **Neuprüfung:** Admin kann für einen Bot oder alle Bots einer Sprache eine erneute Verifikation auslösen (z. B. nach Sicherheitsfix).
