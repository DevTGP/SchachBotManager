# Verifikation (Upload-Pipeline)

Jeder Upload durchläuft die Pipeline vollständig, bevor der Bot an Spielen teilnehmen darf. Die Pipeline läuft als Job im Runner; Partien haben Vorrang (E81). Quell- und Datendateien liegen in GridFS (E82).

## Stufen

| # | Stufe | Prüft | Ort |
|---|-------|-------|-----|
| 1 | Annahme | Rolle des Nutzers, Upload-Rate, Dateitypen, Größen, Struktur (keine Pfad-Tricks, keine Symlinks) | Web-API |
| 2 | Statische Analyse | Regeln aus [statische-analyse.md](statische-analyse.md) | Runner (E81) |
| 3 | Build | Kompilieren/Paketieren mit festen, serverseitigen Build-Einstellungen; Zeit- und Speicherlimit | Sandbox (Build-Verzeichnis) |
| 4 | Artefaktprüfung | Größe, bei Java/C# referenzierte APIs im Kompilat | Runner (E81) |
| 5 | Mindesttests | siehe unten | Sandbox (Laufzeitverzeichnis) |
| 6 | Freigabe | Automatisch oder zusätzlich manuell durch Admin (konfigurierbar) | Web-API |

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

## Status eines Bots

```
uploaded → analyzing → building → testing → verified
                 ↘         ↘          ↘
                          rejected
verified → disabled (Admin oder Besitzer)   verified → retired (Besitzer)
```

- Der Report (Stufe, Regel, Datei/Zeile, Build-Ausgabe gekürzt, Testprotokoll) ist für Besitzer und Admin einsehbar.
- Der Quellcode ist ausschließlich für Besitzer und Admin abrufbar (E15).
- Quellcode und Artefakt eines Bots sind nach dem Upload **unveränderlich** (E6). Bearbeitbar bleiben nur Metadaten (Name, Beschreibung) und Anmeldungen.

## Versionen (E6)

- „Bearbeiten“ des Codes erzeugt einen **neuen Bot** mit Verweis auf den Vorgänger (`lineage_id`, `parent_bot_id`, `version_no`).
- Der neue Bot durchläuft die Pipeline vollständig, hat eigene Historie und beginnt in der untersten Liga.
- Die UI gruppiert Versionen einer Abstammung und kann Partien zwischen Versionen ansetzen (Einzelspiele).
- Keine Obergrenze für aktive Versionen einer Abstammung (E14); nicht mehr benötigte Versionen werden deaktiviert.

## Zu beachten

- **Speicherung:** Quellcode, Artefakt und Report mit Hash ablegen; Version des Laufzeitverzeichnisses und SDK-Version am Bot speichern.
- **Missbrauch:** Upload-Raten pro Nutzer begrenzen, Pipeline-Jobs haben niedrigere Priorität als Liga-Spiele.
- **Determinismus:** Tests mit festen Stellungen und festen Seeds, damit Ergebnisse reproduzierbar sind.
- **Neuprüfung:** Admin kann für einen Bot oder alle Bots einer Sprache eine erneute Verifikation auslösen (z. B. nach Sicherheitsfix).
