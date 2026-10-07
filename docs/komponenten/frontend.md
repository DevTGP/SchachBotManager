# Frontend (SPA)

Eigenständige Anwendung (E5) in React + TypeScript, gebaut mit Vite (E9). Spricht ausschließlich mit der [Flask-API](backend-api.md). Alle Ansichten außer „Mein Bereich“ und „Admin“ sind ohne Login zugänglich (E10).

## Sprachen (E32)

Deutsch und Englisch. Alle Texte liegen von Beginn an in Übersetzungsdateien; Sprachwahl nach Browser-Einstellung mit Umschalter, die Wahl bleibt gespeichert. Fehlermeldungen der API kommen als Codes und werden im Frontend übersetzt; das gilt auch für Endgründe von Partien und Meldungen der Verifikation.

## Bereiche

| Bereich | Inhalt |
|---------|--------|
| Start | Laufende Spiele, zuletzt beendete Partien, aktuelle Saisons |
| Queue | Wartende Spiele in Reihenfolge mit geschätzter Startzeit, Wettbewerb und Disziplin |
| Partie-Viewer | siehe unten |
| Ligen | Stufen, Tabellen, Spielplan, Auf-/Abstiegszonen, frühere Saisons |
| Turniere | Teilnehmer, Runden, Tabelle bzw. K.-o.-Baum |
| Bot-Profil | Stammdaten, Besitzer, Sprache, Versionen der Abstammung, Rating-Verlauf, Liga-Verlauf, vollständige Partienliste mit Filtern, Statistik (Bilanz nach Farbe/Gegner/Endgrund) |
| Mein Bereich (Coder) | Eigene Bots, Upload, Verifikationsstatus und Report, Logs eigener Bots, Anmeldungen, API-Tokens, Einzelspiele ansetzen |
| Spielen | Für jeden Besucher (E11): Bot auswählen, Farbe/Zeitkontrolle, Partie gegen den Bot |
| Admin | Nutzer & Invites, Bots (alle), Disziplinen, Ligen, Turniere, Queue-Steuerung (pausieren, umsortieren, Parallelität, Zeitfenster), Systemeinstellungen und Limits, Systemstatus, Audit-Log |

## Partie-Viewer

| Funktion | Detail |
|----------|--------|
| Brett | Figuren, letzter Zug markiert, Brett drehbar, Koordinaten |
| Navigation | Anfang/Ende, vor/zurück, Klick in die Zugliste, Tastatur |
| Wiedergabe | Play/Pause, mehrere Geschwindigkeiten (feste Faktoren und „Echtzeit“ anhand der gespeicherten Zugzeiten) |
| Uhren | Restzeit beider Seiten zum jeweiligen Zug |
| Zugliste | SAN-Notation, verbrauchte Zeit pro Zug |
| Metadaten | Bots, Versionen, Disziplin, Ergebnis, Endgrund, Wettbewerb |
| Zusatz | Bot-`info` (Bewertung/Tiefe) als Verlauf, öffentlich sichtbar (E33), geschlagene Figuren/Materialbilanz |
| Live | Laufende Partien aktualisieren sich über den Live-Kanal (bis M4 durch Abfragen, E77); Wechsel zwischen „live folgen“ und freiem Blättern |
| Export | PGN, FEN der aktuellen Stellung, teilbarer Link auf Partie + Zugnummer |

Der Viewer rendert nur gespeicherte Stellungen (FEN pro Zug) und braucht keine eigene Regelimplementierung.

## Stand M2

Umgesetzt unter `frontend/` (E77): Start, Partienliste mit Filtern, Partie-Viewer, Queue, Bot-Liste; Deutsch und Englisch. Noch nicht: Bewertungsverlauf als Grafik, Versionen, Wettbewerb, Live-Kanal, Bereiche ab M3.

| Ordner | Inhalt |
|--------|--------|
| `src/api/` | `schema.d.ts` (aus `spec/web/openapi.json` erzeugt), Typ-Aliase, `fetch`-Hülle mit Fehlercodes, eine Funktion je Endpunkt |
| `src/hooks/` | `useApi` (Laden, Abfragen in Abständen, Daten bleiben bei Fehlern stehen), Abfrageintervalle, Locale |
| `src/format/` | Uhr, Zugzeit, Zeitkontrolle, Datum, Bewertung, Ergebnis |
| `src/chess/` | Auswertung der FEN (Seite am Zug, Zugnummer, Materialbilanz, Felder eines Zuges) – keine Regeln |
| `src/viewer/` | Stellung und Uhren je Halbzug, Zugnummer in der URL, Wiedergabe, Tastatur, Brett, Spielerleisten, Zugliste, Steuerung, Details, Bot-Info, Export |
| `src/pages/` | Eine Datei je Seite, dazu die Queue-Tabelle |
| `src/components/` | Rahmen mit Navigation und Sprachumschalter, Lade- und Fehleranzeige, Partientabelle, Blättern, Kopierknopf |
| `src/i18n/` | Einrichtung und die Übersetzungsdateien `de.json`, `en.json` |
| `src/styles/` | Farben (hell/dunkel), Rahmen und Tabellen, Viewer |
| `src/test/` | Testdaten, `fetch`-Attrappe, Rendern einer Route |

Tests: Komponenten- und Seitentests mit Vitest und Testing Library gegen eine `fetch`-Attrappe; das Brett ist dort durch einen Platzhalter ersetzt, weil jsdom keine Maße kennt. Lokal startet `npm run dev` den Vite-Server, der `/api` an `SBM_API_URL` (Standard `http://127.0.0.1:5000`) weiterreicht.

## Mensch gegen Bot

- Zugeingabe per Drag-and-drop/Klick; legale Züge kommen vom Server oder aus einer Client-Schachbibliothek (nur Komfort – der Server prüft immer).
- Umwandlungsdialog, Aufgabe, Anzeige der Bot-Bedenkzeit.
- Verbindungsabbruch: Wiederaufnahme innerhalb einer Frist, danach Abbruch.

## Zu beachten

- **Zustand über URLs:** Jede Ansicht (Partie, Zugnummer, Saison, Filter) ist verlinkbar.
- **Rechte in der UI sind nur Komfort**; maßgeblich ist die API.
- **Große Listen** paginiert/virtuell.
- **Upload-Rückmeldung:** Pipeline-Status schrittweise anzeigen, Report mit Datei/Zeile.
- **Kampflose Siege (E17)** in Tabellen und Partienlisten eigens kennzeichnen; zurückgezogene Bots in der Saisonansicht ausweisen.
- **Brett-Komponente:** Bei Fremdbibliotheken die Lizenz prüfen (einige verbreitete Schachbrett-Komponenten stehen unter GPL).
- **Admin-Formulare** für jede Einstellung (E13) mit Validierung und Laufzeitschätzung (siehe [ligen-turniere.md](ligen-turniere.md)).
- **Auslieferung:** Statischer Build im `frontend`-Container, der auch `/api` und WebSocket an die API weiterreicht; der Nginx Proxy Manager zeigt nur auf diesen Container (E29). Gleicher Ursprung, kein CORS nötig.
- **Tests:** Komponententests für den Viewer, wenige End-to-End-Tests für Login, Upload, Viewer.
