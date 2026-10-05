# Entscheidungen, Annahmen, offene Punkte

Stand: 2026-10-05, Revision 2 (vorheriger Stand: `_archiv/v1/`)

## 1. Entscheidungen

| ID | Thema | Entscheidung | Konsequenz |
|----|-------|--------------|------------|
| E1 | Sicherheit | Sandbox **und** strikte statische Analyse | Pro Sprache ein eigener Analyzer; Sandbox bleibt die eigentliche Sicherheitsgrenze |
| E2 | Schachlogik | SDK liefert alles (Brett, legale Züge, make/undo, Endbedingungen) | Bot schreibt nur Suche und Bewertung |
| E3 | SDK-Kern | **Ein gemeinsamer C++-Kern mit Bindings** für alle Sprachen (geändert, vorher: nativ pro Sprache) | Eine Regelimplementierung; Referee nutzt denselben Kern; SDKs werden als vorkompilierte Pakete ausgeliefert |
| E4 | Legitimierung | Invite-only | Keine offene Registrierung; Invite-Verwaltung im Adminbereich |
| E5 | Frontend | Flask als reine API + separate SPA | Zwei Codebasen, Build-Schritt fürs Frontend |
| E6 | Bot-Bearbeitung | Neue Version = neuer Bot; Versionen können gegeneinander antreten | Jede Version ist eigener Teilnehmer, startet unten, eigene Historie; Verknüpfung über Abstammung |
| E7 | Liga-Modus | Saisons mit Tabellen (Round-Robin, Auf-/Abstieg) | Rating nur als Statistik |
| E8 | Fairness | **Keine Sprachfaktoren.** Alle Sprachen haben identische Zeit- und Ressourcenlimits (geändert) | Langsamere Sprachen sind benachteiligt; Disziplinen enthalten keine sprachspezifischen Einstellungen |
| E9 | Frontend-Framework | React + TypeScript, Build mit Vite | – |
| E10 | Sichtbarkeit | Partien, Tabellen, Bot-Profile sind öffentlich | Lesende API-Routen ohne Login |
| E11 | Mensch gegen Bot | Jeder Besucher darf spielen, ohne Account | Kapazitätsgrenzen pro IP/gesamt nötig |
| E12 | Hardware | Schwacher, nicht dedizierter Server | Standard: ein Spiel gleichzeitig; Störungen durch andere Dienste werden hingenommen |
| E13 | Konfiguration | Alles über die Website einstellbar (Disziplinen, Ligen, Turniere, Queue, Limits) | Konfiguration liegt in der DB, Admin-UI für jeden Parameter |
| E14 | Versionen pro Liga | Keine Obergrenze | Bots lassen sich deaktivieren |
| E15 | Quellcode | Für andere nicht einsehbar | Nur Besitzer und Admin |
| E16 | Bibliotheken | Whitelist laut [statische-analyse.md](komponenten/statische-analyse.md) | Auf Typ-/Funktionsebene |
| E17 | Bot verlässt Liga | Bot wird aus der Tabelle entfernt; gespielte Partien zählen normal, ausstehende als kampfloser Sieg des Gegners (eigens markiert); ein Bot weniger steigt ab | Siehe [ligen-turniere.md](komponenten/ligen-turniere.md) |
| E18 | Isolation | Einfache Isolation ohne Docker: **nsjail** | Siehe [sandbox.md](komponenten/sandbox.md) |
| E19 | Zeitmessung | Wanduhrzeit (Systemzeit), keine CPU-Zeit | Bedenkzeit läuft unabhängig von der tatsächlich erhaltenen Rechenzeit |
| E20 | Spielplanung | Eine Queue; Spiele starten direkt nacheinander; online stehen geschätzte Startzeiten | Keine festen Termine |
| E21 | SDK-API | Callback-Modell; hohe Ebene plus Rohzugriff aufs Brett; Schreibweise idiomatisch pro Sprache | Siehe [sdk-api.md](komponenten/sdk-api.md) |
| E22 | Brett-Instanz | Jeder Bot hat sein eigenes Brett im eigenen Prozess; Probezüge sind rein lokal | Der Match-Runner sieht nur den abgegebenen Zug |

Aus dem Anforderungstext fix: MongoDB, Flask, GitHub Actions, Sprachen Python / C++ / Java / C# / JavaScript.

## 2. Annahmen (von mir gesetzt)

| ID | Annahme | Alternative |
|----|---------|-------------|
| A1 | Nur Standardschach | Varianten als Disziplin-Attribut |
| A2 | Ein einzelner Linux-Host; Web-Dienste über Docker Compose | – |
| A3 | Kein Pondering: Bots sind außerhalb ihres Zuges eingefroren | – |
| A4 | Ein Bot = ein Thread | Mehrkern-Disziplinen |
| A5 | Bot-Upload = Quellcode, Build serverseitig | Upload fertiger Binaries |
| A6 | Server ist alleiniger Schiedsrichter | – |
| A7 | Kommunikation Bot ↔ Server über stdin/stdout (zeilenweises JSON) | Lokale Sockets |
| A8 | Job-Queue in MongoDB | Redis + RQ/Celery |
| A9 | Spiele gegen Menschen und Remote-Bots sind ungewertet | Eigene gewertete Kategorie |
| A11 | Der Kern stellt eine flache C-Schnittstelle bereit; alle Bindings setzen darauf auf | Je Sprache direkte C++-Anbindung |
| A12 | JavaScript-Binding als nativer Node-Addon | WebAssembly-Build des Kerns (portabler, langsamer) |
| A13 | Runner und Verifier laufen als Dienste direkt auf dem Host (nicht in Docker), weil nsjail Namespaces und cgroups selbst anlegt | Privilegierter Container |
| A14 | Speicherlimits gelten für den gesamten Prozess inklusive Laufzeitumgebung | – |

## 3. Offene Punkte

Derzeit keine. Neue Fragen werden hier ergänzt.

## 4. Risiken

| ID | Risiko | Einordnung |
|----|--------|-----------|
| R2 | Verhalten weicht zwischen Sprachen ab | Durch E3 stark reduziert: Regeln liegen nur im Kern. Verbleibend: Fehler in den Bindings → Binding-Tests je Sprache |
| R3 | Statische Analyse ist umgehbar | Bleibt als zweite Schicht Pflicht, darf aber nie die einzige sein |
| R4 | Runner/Verifier brauchen Rechte zum Anlegen von Namespaces/cgroups | Strikt von der öffentlichen Web-API getrennt, nicht von außen erreichbar |
| R5 | Rechenbedarf langer Partien auf schwacher Hardware | Alles konfigurierbar (E13), Queue nutzt die Zeit lückenlos (E20), Laufzeitschätzung in der Admin-UI |
| R6 | Wanduhrzeit auf geteiltem Server: Fremdlast kostet den Bot am Zug Bedenkzeit | Akzeptiert (E12, E19); gedämpft durch festen Kern und CPU-Priorität |
| R7 | Übergang über die Sprachgrenze kostet pro Aufruf Zeit | Grobkörnige API (ganze Zuglisten, Massenabfragen), siehe [sdk-api.md](komponenten/sdk-api.md) |
| R8 | Vorkompilierte SDK-Pakete müssen für jede Plattform der Entwickler gebaut werden | Build-Matrix in CI (Windows, Linux, macOS) |
| R9 | Debugger der Bot-Sprache kann nicht in den Kern steppen | Kern liefert aussagekräftige Fehler; Brettzustand jederzeit als FEN/Text ausgebbar |
| R10 | Gäste können Spiele gegen Bots starten (E11) und damit die Queue belasten | Eigene Kapazitätsgrenze, niedrigste Priorität |
