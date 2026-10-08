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

## Stand M3, Schritt 1 (E83–E85)

Anmeldung, eigenes Konto und die ersten Admin-Seiten:

| Ort | Inhalt |
|-----|--------|
| `src/session/` | `SessionProvider` lädt `GET /session` einmal und hält das Konto; `RequireRole` schickt Gäste zur Anmeldung (mit Rücksprung über `?next=`, nur auf eigene Pfade) und zeigt Coder auf Admin-Seiten einen Fehler; `oneTimeToken` liest das Token hinter `#` und entfernt es aus Adresse und Verlauf |
| `src/pages/account/` | Anmelden, Einladung einlösen, neues Passwort über Link, „Konto“ mit Passwortwechsel und Abmelden |
| `src/pages/admin/` | Partien ansetzen samt Queue-Steuerung, Nutzer (Rolle, Aktiv-Status, Passwort-Link), Einladungen (erstellen, auflisten, zurückziehen) |
| `src/api/account.ts`, `src/api/admin.ts` | Eine Funktion je Endpunkt; `sendJson` setzt den Header `X-SBM-CSRF: 1` (E84) |
| `src/components/` | Navigation zum Konto, Formularfehler, Passwortfelder, Anzeige eines Einmal-Links mit Kopierknopf |
| `src/hooks/useSubmit.ts` | Absenden eines Formulars mit Fehlercode und Feld aus der API |

Einmal-Links zeigt die Seite nur direkt nach dem Erstellen; die Liste der Einladungen kennt sie nicht mehr (E83). Feldfehler der API (`field`) erscheinen am passenden Eingabefeld.

## Stand M3, Schritt 3 (E91–E93)

| Ort | Inhalt |
|-----|--------|
| `src/pages/upload/` | Seite `/bots/new` (nur angemeldet): Ordner oder einzelne `.py`-Dateien wählen, Auswahl der Dateien mit Liste des Weggelassenen, Einstiegsdatei, Name mit Vorschlägen aus den eigenen Bots, Version mit Vorschlag der nächsten Patch-Version; darunter die eigenen Bots |
| `src/upload/` | Auswahl und Prüfung der Dateien nach den Regeln aus E92 vor dem Senden, Muster für Name und Version |
| `src/pages/bot/` | Seite `/bots/:id`: Status, Sprache, Version, Link zu den Partien; für Besitzer und Admins Dateien und Report mit Befunden und Testpartien; Admins können sperren und freigeben. Während der Verifikation fragt sie alle 3 s nach |
| `src/api/bots.ts` | Upload als `FormData`, Bot, eigene Bots, Sperre |
| `src/format/botLabel.ts` | „Name Version“ als Anzeige eines Bots |

Die Bot-Liste zeigt die Version und verlinkt jeden Bot; die Kontonavigation führt zum Upload. Fehler `invalid_upload` nennen die betroffene Datei.

## Stand M3, Schritt 4 (E95–E98)

| Ort | Inhalt |
|-----|--------|
| `src/pages/ownBots/` | Seite `/account/bots` „Meine Bots“ (nur angemeldet): eigene Bots nach Name gruppiert mit allen Versionen und Status, Link zum Upload, Formular für Partien eines eigenen geprüften Bots gegen jeden geprüften Bot mit den Grenzen aus E98 |
| `src/pages/bot/` | Zusätzlich Beschreibung (Besitzer bearbeitet sie), Zurückziehen und Reaktivieren für den Besitzer, Sperre durch Admins auch für zurückgezogene Bots, Liste der Versionen, Dateien als Text (nur gültiges UTF-8) und Download einzeln oder als ZIP |
| `src/pages/upload/` | Feld für die Beschreibung; statt der Liste eigener Bots ein Link auf „Meine Bots“ |
| `src/format/botLabel.ts` | `sideLabel` und `playersLabel`: Seiten einer Partie als „Name Version“ in Listen, Queue und Viewer |
| `src/components/NumberField.tsx` | Zahlenfeld mit Grenzen, gemeinsam für Admin- und Coder-Formular |

Die Kontonavigation führt zu „Meine Bots“, von dort zum Upload. Dateien eines Bots zeigt die Seite nur als Text, den React maskiert; HTML in einer Datei wird nie ausgeführt.

## Stand M4, Schritt 1 (E100)

| Ort | Inhalt |
|-----|--------|
| `src/pages/admin/AdminDisciplinesPage.tsx`, `DisciplineEditor.tsx`, `disciplineForm.ts` | Seite `/admin/disciplines`: Disziplinen anlegen, ändern, archivieren und wiederherstellen |
| `src/components/DisciplineSelect.tsx` | Auswahl einer nicht archivierten Disziplin oder freier Zeiten, im Admin- und im Coder-Formular für Partien; mit Disziplin entfallen die Zeitfelder |
| `src/viewer/MatchDetails.tsx` | Zeile „Gewertet“ |

Lädt `/disciplines` nicht, bieten die Formulare nur freie Zeiten an.

## Stand M4, Schritt 2 (E103, E104)

| Ort | Inhalt |
|-----|--------|
| `src/pages/RatingsPage.tsx` | Seite `/ratings` („Rangliste“) in der Hauptnavigation: Platz, Bot, Sprache, Rating, gewertete Partien |
| `src/pages/BotsPage.tsx`, `src/pages/bot/BotSummary.tsx` | Spalte bzw. Zeilen „Rating“ und „Gewertete Partien“ |
| `src/viewer/MatchDetails.tsx`, `src/format/rating.ts` | Zeilen „Rating Weiß“ und „Rating Schwarz“ als „2500 → 2550 (+50)“, sobald die Partie verbucht ist |

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
