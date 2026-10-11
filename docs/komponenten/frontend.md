# Frontend (SPA)

Eigenständige Anwendung (E5) in React + TypeScript, gebaut mit Vite (E9). Spricht ausschließlich mit der [Flask-API](backend-api.md). Alle Ansichten außer „Mein Bereich“ und „Admin“ sind ohne Login zugänglich (E10).

## Sprachen (E32)

Deutsch und Englisch. Alle Texte liegen von Beginn an in Übersetzungsdateien; Sprachwahl nach Browser-Einstellung mit Umschalter, die Wahl bleibt gespeichert. Fehlermeldungen der API kommen als Codes und werden im Frontend übersetzt; das gilt auch für Endgründe von Partien und Meldungen der Verifikation.

## Bereiche

| Bereich | Inhalt |
|---------|--------|
| Start | Erklärt die Idee des Projekts ohne Abfragen an die API (E166) |
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
| `src/format/botLabel.ts` | „Name Version“ als Anzeige eines Bots (seit E165 entfallen: Namen ohne Version, siehe unten) |

Die Bot-Liste zeigt die Version und verlinkt jeden Bot; die Kontonavigation führt zum Upload. Fehler `invalid_upload` nennen die betroffene Datei.

## Stand M3, Schritt 4 (E95–E98)

| Ort | Inhalt |
|-----|--------|
| `src/pages/ownBots/` | Seite `/account/bots` „Meine Bots“ (nur angemeldet): eigene Bots nach Name gruppiert mit allen Versionen und Status, Link zum Upload, Formular für Partien eines eigenen geprüften Bots gegen jeden geprüften Bot mit den Grenzen aus E98, seit E154 aus `GET /account/limits` (`ownLimits.ts`) in Feldern und Texten |
| `src/pages/bot/` | Zusätzlich Beschreibung (Besitzer bearbeitet sie), Zurückziehen und Reaktivieren für den Besitzer, Sperre durch Admins auch für zurückgezogene Bots, Liste der Versionen, Dateien als Text (nur gültiges UTF-8) und Download einzeln oder als ZIP |
| `src/pages/upload/` | Feld für die Beschreibung; statt der Liste eigener Bots ein Link auf „Meine Bots“ |
| `src/format/botLabel.ts` | `sideLabel` und `playersLabel`: Seiten einer Partie als „Name Version“ in Listen, Queue und Viewer (seit E165 ersetzt durch `pairing.ts` und `SideName`) |
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
| `src/pages/RatingsPage.tsx` | Seite `/ratings` („Rangliste“) in der Hauptnavigation: Platz, Name, Version, Ersteller („Referenzbot“ ohne Besitzer, E164), Art (Sprache des Bots oder „Spieler“), Rating, gewertete Partien; Auswahl „Gesamt“ oder eine Disziplin (auch archivierte) in der URL (`discipline`, E163) mit Hinweis zur Gewichtung bei „Gesamt“; Filter Alle/Bots/Spieler in der URL (`show`), Spieler ohne Link und ohne Version und Ersteller (E118) |
| `src/pages/ranking.ts` | Lädt `/ratings` und `/ratings/players` je nach Filter, gesamt oder mit `discipline_id`, und sortiert sie gemeinsam nach Rating (E118, E163) |
| `src/pages/BotsPage.tsx`, `src/pages/bot/BotSummary.tsx` | Spalte bzw. Zeilen „Rating“ (seit E163 gesamt) und „Gewertete Partien“; die Botliste hat die Spalte „Ersteller“ (E164) |
| `src/viewer/MatchDetails.tsx`, `src/format/rating.ts` | Zeilen „Rating Weiß“ und „Rating Schwarz“ als „2500 → 2550 (+50)“, sobald die Partie verbucht ist |

## Stand M4, Schritt 3 (E130–E137)

| Ort | Inhalt |
|-----|--------|
| `src/api/leagues.ts` | Ligen, Saisons, Ligen eines Bots, An- und Abmelden |
| `src/pages/leagues/LeaguesPage.tsx` | `/leagues` („Ligen“) in der Hauptnavigation: Name, Disziplin, Stufen, Angemeldete, Stand der letzten Saison |
| `src/pages/leagues/LeaguePage.tsx`, `NextSeason.tsx`, `LeagueFacts.tsx`, `LeagueSeasons.tsx`, `LeagueRegistrations.tsx`, `LeagueRegisterForm.tsx` | `/leagues/:id`: wann die nächste Saison beginnt (oder dass die erste auf Freigabe wartet), Einstellungen, Saisons, Anmeldungen mit Stufe oder Warteliste; Coder und Admins melden eigene geprüfte Bots an, Admins melden jeden ab |
| `src/pages/leagues/SeasonPage.tsx`, `TierTable.tsx` | `/seasons/:id`: Tabelle je Stufe mit Platz (bei Rückzug „–“), Siegen samt kampflosen, Punkten und Ausgang, Link auf `/matches?season=…&tier=…`; fragt nach, solange die Saison läuft |
| `src/pages/admin/AdminLeaguesPage.tsx`, `LeagueEditor.tsx`, `TiebreakField.tsx`, `leagueForm.ts` | `/admin/leagues`: Ligen anlegen und ändern (Feinwertung als bis zu vier geordnete Auswahlfelder), erste Saison freigeben, archivieren und wiederherstellen |
| `src/pages/bot/BotLeagues.tsx` | Bot-Seite: Ligen des Bots; Besitzer und Admins melden ab und bei `verified` in einer weiteren Liga an |
| `src/pages/MatchLeague.tsx` | Partieseite: Liga, Saison, Stufe, Runde und Brett |
| `src/pages/MatchesPage.tsx` | `/matches`: Filter nach Saison und Stufe aus der URL (`season`, `tier`) mit Hinweis und „Alle Partien zeigen“ |

Ungültige Einstellungen nennt das Formular je Feld (`leagueError.*`).

## Stand M4, Schritt 4 (E138–E141)

| Ort | Inhalt |
|-----|--------|
| `src/pages/leagues/TierSchedule.tsx` | `/seasons/:id`: Spielplan unter der Tabelle jeder Stufe, je Runde ein aufklappbarer Abschnitt mit Fortschritt; die erste noch nicht beendete Runde ist offen. Je Brett die Paarung alphabetisch mit Ergebnis in derselben Reihenfolge, Status oder „kampflos“ und „Öffnen“ (E165), spielfreier Bot ohne Version darunter; fragt nach, solange die Saison läuft |
| `src/pages/bot/BotSeasons.tsx` | Bot-Seite (hochgeladene Bots): Ligasaisons dieser Version mit Liga, Saison, Stufe, Platz „n von m“, Partien, Punkten und Ausgang bzw. „Läuft“ |
| `src/pages/bot/BotRatingChart.tsx`, `ratingChart.ts` | Bot-Seite: Rating-Verlauf als SVG-Kurve je Disziplin (Auswahl bei mehreren), Werte als Tooltip, Stand mit Höchst- und Tiefstwert als Text |
| `src/pages/bot/BotResults.tsx` | Bot-Seite: Siege, Remis und Niederlagen je Disziplin mit Summenzeile |
| `src/api/botHistory.ts`, `src/api/leagues.ts` | Rating-Verlauf und Bilanz bzw. Spielplan und Saisons eines Bots |

## Endgültiges Löschen (E105)

| Ort | Inhalt |
|-----|--------|
| `src/pages/bot/BotDelete.tsx` | Knopf „Endgültig löschen“ für Admins auf der Bot-Seite (nicht bei Referenzbots und während der Verifikation), mit Rückfrage; danach weiter zu einer anderen Version des Namens oder zu `/bots` |

## Mensch gegen Bot (Stand M7, E114–E119)

| Datei | Inhalt |
|-------|--------|
| `src/pages/play/PlaySetupPage.tsx` | `/play`: Bot, Farbe, Disziplin oder freie Zeiten (bis 30 min + 30 s), dann `POST /play`; Hinweis, wann die Partie gewertet wird (E117) |
| `src/pages/play/GamePage.tsx`, `PlayBoard.tsx`, `GameClock.tsx`, `PromotionChoice.tsx` | `/play/:id`: Brett mit Ziehen und Anklicken, nur Züge aus `legal_moves` des Servers (keine eigenen Regeln), Umwandlungsauswahl, laufende Uhren, Zugliste, Aufgabe mit Rückfrage |
| `src/play/usePlayGame.ts`, `protocol.ts`, `seats.ts` | WebSocket zum Gateway (gateway-v1, dann play-v1), Neuverbindung mit wachsendem Abstand bis 55 s, Sitz-Token im `localStorage` |
| `src/pages/admin/AdminPlayPage.tsx` | `/admin/play`: Grenzen interaktiver Partien (E115) |
| `src/pages/account/OwnRating.tsx` | Kontoseite, jede Rolle: eigenes Rating und gewertete Partien (`GET /account/rating`, E117) |
| `src/pages/account/ApiTokens.tsx` | Kontoseite für Coder: API-Tokens anlegen (einmal sichtbar), auflisten, widerrufen (E116) |
| `src/pages/MatchesPage.tsx` | Zusätzlicher Filter „Art“ (Alle Partien, Bot gegen Bot, Mit Spielern) in der URL (`kind`), Standard alle (E119) |

- Partien mit Spielern stehen in Partienliste, Queue (nur laufende) und Viewer wie Botpartien; eine Seite ohne Bot erscheint mit ihrem Namen (Nutzername oder „Guest“, unübersetzt wie im PGN) ohne Version (E119).
- Die Rolle `player` sieht weder „Meine Bots“ noch Tokens; `RequireRole role="coder"` schützt die Coder-Seiten.
- Der Vite-Entwicklungsserver reicht `/api/v1/play/socket` an `SBM_GATEWAY_URL` weiter (Standard `ws://127.0.0.1:8001`).

## Adminbereich (Stand M6, E150–E169)

| Datei | Inhalt |
|-------|--------|
| `src/pages/admin/AdminAuditPage.tsx` | `/admin/audit`: Audit-Log mit Filtern nach Akteur, Aktion, Zeitraum und Ziel in der URL, Klick auf ein Ziel filtert danach, Seitenwechsel (E151) |
| `src/pages/admin/AdminQueueTable.tsx`, `QueueEntryActions.tsx` | `/admin`: Queue mit Priorität; bei wartenden Einzelspielen Priorität setzen und „Nach vorn“, bei wartenden und laufenden Abbrechen mit Rückfrage (E152) |
| `src/pages/admin/MatchRepeat.tsx` | Partieseite, nur Admins: beendete oder abgebrochene Einzelspiele erneut einreihen, danach die neue Partie (E152) |
| `src/pages/bot/BotChecks.tsx` | Bot-Seite, nur Admins: Neuprüfung auslösen, bei abgelehnten Bots Override mit Rückfrage (E153) |
| `src/pages/bot/BotRechecks.tsx`, `ReportStages.tsx`, `reportFacts.ts` | Bot-Seite für Besitzer und Admins: Neuprüfungen als aufklappbare Liste mit denselben Stufen wie der Report; die Seite fragt nach, solange eine Prüfung wartet (E153) |
| `src/pages/admin/AdminSettingsPage.tsx`, `SettingsGroupFields.tsx`, `settingsFields.ts` | `/admin/settings`: je Gruppe (Coder, Einladungen und Konten, Rating, Schätzung der Queue) ein Abschnitt mit Feldern und Grenzen aus `settingsFields.ts`, Zeiten in Sekunden; Hinweis, solange eine Neuberechnung der Ratings ansteht (E154) |
| `src/pages/admin/InviteForm.tsx` | `/admin/invites`: Formular für Einladungen mit Standard und Höchstwert der Gültigkeit aus den Einstellungen (E154) |
| `src/pages/upload/UploadPage.tsx` | zeigt die Zahl der Uploads je Tag aus `GET /account/limits` (E154) |
| `src/components/FormError.tsx` | zusätzlich `values` für Texte mit eingesetzten Grenzen (E154) |
| `src/components/BotPicker.tsx` (bis E165 `BotOptions.tsx`) | Bot-Auswahl, auf Wunsch zuerst „Zufall“ (Wert `random`, E162): im Admin-Formular für beide Seiten (`EnqueueForm.tsx`), unter „Meine Bots“ nur für den Gegner (`OwnMatchForm.tsx`), auf `/play` für den Bot (`PlaySetupPage.tsx`); mit Zufall verlinkt die Rückmeldung keine Serie |
| `src/pages/admin/RecheckLanguage.tsx` | `/admin`: alle verifizierten und abgelehnten Bots einer Sprache erneut prüfen, meldet die Zahl der eingereihten Prüfungen (E153) |

## Einzelspiele (Stand M6, E155–E161)

| Datei | Inhalt |
|-------|--------|
| `src/pages/series/SeriesPage.tsx`, `src/format/points.ts` | `/series/:id`: beide Bots mit Punkten (½ als Zeichen), Zahl der beendeten Partien und die Partien in Reihenfolge (E155) |
| `src/pages/MatchSeries.tsx` | Partieseite: „Partie 2 von 3 einer Serie“ mit Link auf die Serie (E155) |
| `src/components/QueuedNotice.tsx` | Bestätigung nach dem Ansetzen in beiden Formularen, mit Link auf die Serie (E155) |
| `src/components/RatedField.tsx` | Kästchen „Gewertet“ in beiden Formularen (E158) |
| `src/components/StartPositionField.tsx`, `src/api/positions.ts` | FEN-Feld mit aufklappbarem Teil „Aus PGN“ (Partie, Halbzüge), setzt die FEN aus `POST /positions/from-pgn` ein (E159) |
| `src/pages/MatchesPage.tsx` | `/matches`: zusätzlich Filter Gegner (nur mit Bot), Disziplin und für Coder und Admins „Von mir angesetzt“, alle in der URL (`opponent`, `discipline`, `mine`) (E156) |
| `src/pages/ownBots/OwnWaitingMatches.tsx` | „Meine Bots“: wartende eigene Partien mit „Zurückziehen“ (E157) |
| `src/pages/bot/BotOpponents.tsx` | Bot-Seite: Tabelle „Bilanz“ mit Link auf `/matches?bot=…&opponent=…` (E161) |
| `src/pages/bot/playLink.ts`, `BotVersions.tsx` | Links „Spielen“ und „Gegen Vorgänger spielen“; das Formular auf `/account/bots` (`own`, `opponent`) bzw. `/admin` (`white`, `black`) übernimmt die Bots aus der Adresse (E160) |

## Durchsicht der Website (Stand M6, E165–E169)

Einheitliche Darstellung nach der Durchsicht aller Seiten:

| Datei | Inhalt |
|-------|--------|
| `src/format/pairing.ts`, `src/components/Pairing.tsx`, `SideName.tsx` | Paarung alphabetisch nach Name, dann Version; Ergebnis passend gedreht (`pairingResult`); jede Seite in einer eigenen Zelle mit festem Platz, Farbe als Kennzeichen am Namen; Namen ohne Version, Bots verlinkt (E165) |
| `src/components/OpenCell.tsx` | Letzte Spalte mit dem Button „Öffnen“ und den Aktionen der Rolle statt Links auf der Paarung (E165) |
| `src/components/BotPicker.tsx`, `src/format/botGroups.ts` | Bot-Auswahl nach Name, bei mehreren Versionen eine zweite Auswahl „Version von …“ mit der neuesten vorgewählt; Wert bleibt die Id (E165) |
| `src/pages/StartPage.tsx`, `src/styles/landing.css` | Startseite: Brett, vier Schritte, Codebeispiel, Ablauf über den Referee, Überblick; keine Abfragen an die API (E166) |
| `src/components/QueueTable.tsx` | Eine Queue-Tabelle mit den Ansichten `public` (`/queue`), `admin` (`AdminQueueTable` mit Priorität und Abbrechen) und `own` (`OwnWaitingMatches` mit Zurückziehen) (E167) |
| `src/components/matchFields/` | Gemeinsame Felder der Formulare zum Ansetzen (`EnqueueForm`, `OwnMatchForm`, `PlaySetupPage`): `MatchFields` (Disziplin oder freie Zeiten, Startstellung, gewertet), `ColorSelect`, `conditions.ts` (Felder je Rolle) (E167) |
| `src/components/PillSelect.tsx` | Pillen statt Dropdowns für kleine Auswahlen: Status und Art in `/matches`, Anzeige und Disziplin in `/ratings`, Sprache der Neuprüfung (E168) |
| `src/components/ConfirmButton.tsx` | Zweiter Klick zur Bestätigung für Sperren, Zurückziehen, Partie zurückziehen und Token widerrufen (E168) |
| `src/components/TableShell.tsx` | Tabelle mit Leertext und waagerechtem Scrollen mit Schatten; Spalten `optional` entfallen auf schmalen Bildschirmen (E168) |
| `src/components/StatusBadge.tsx`, `BotStatusBadge.tsx` | Status von Partien und Bots als farbige Abzeichen (E168) |
| `src/format/timeControl.ts`, `duration.ts` | Zeiten als „3 min + 2 s“, Disziplinen als „Blitz (3 min + 2 s)“; Eingaben in Sekunden oder Minuten mit Punkt oder Komma (E168) |
| `src/components/AccountNav.tsx`, `src/session/useLogout.ts` | Kontonavigation mit Abmelden; auf schmalen Bildschirmen als Auswahl (E168) |
| `src/components/ExploreLinks.tsx` | Links auf Partien, Rangliste, Spielen und Startseite auf der Seite 404 und bei fehlgeschlagener Anmeldung (E168) |
| `src/pages/bot/BotHeader.tsx`, `BotActions.tsx`, `BotAdmin.tsx` | Bot-Seite: Kopf mit Version, Ersteller, Sprache, Status und Rating; eine Leiste der Aktionen; Eingriffe der Admins gesammelt am Ende |
| `src/pages/upload/FileDrop.tsx`, `src/upload/dropped.ts` | Upload: Ordner oder Dateien hineinziehen oder wählen; versteckte Ordner und `__pycache__` entfallen |
| `src/pages/account/OwnRating.tsx` | Kontoseite: Gesamtrating und Rating je Disziplin aus `GET /account/rating` (E169) |
| `src/pages/admin/AuditTable.tsx` | `/admin/audit`: Ziel mit Name und Link aus `target_kind` und `target_label` (E169) |

Namen von Bots stehen nirgends mehr mit Version; eine Spalte „Version“ haben nur Botliste, Rangliste, „Meine Bots“, Bilanz und Versionen eines Bots. Ein Test (`src/i18n/keys.test.ts`) prüft, dass `de.json` und `en.json` dieselben Schlüssel haben.

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
