# Code-Karte: Frontend (SPA)

Die Weboberfläche unter [`frontend/`](../../frontend/) (Paket `sbm-frontend`, React + TypeScript + Vite, E77). Sie spricht nur mit der Web-API unter `/api/v1` und für interaktive Partien mit dem Gateway. Konzept, Bereiche und Stand je Meilenstein: [frontend.md](../komponenten/frontend.md).

## Einstieg

Befehle aus [`package.json`](../../frontend/package.json), aufgerufen in `frontend/`:

| Befehl | Wirkung |
|--------|---------|
| `npm run dev` | Vite-Server; reicht `/api` an `SBM_API_URL` (Standard `http://127.0.0.1:5000`) und `/api/v1/play/socket` an `SBM_GATEWAY_URL` (Standard `ws://127.0.0.1:8001`) weiter ([`vite.config.ts`](../../frontend/vite.config.ts)) |
| `npm run build` | `tsc -b`, dann `vite build` nach `dist/` |
| `npm run api-types` | erzeugt `src/api/schema.d.ts` aus [`spec/web/openapi.json`](../../spec/web/openapi.json); `api-types:check` prüft nur (CI) |
| `npm test`, `npm run lint`, `npm run format:check` | Vitest, ESLint, Prettier (siehe [Tests](#tests)) |

Lesereihenfolge:

1. [`src/main.tsx`](../../frontend/src/main.tsx): lädt `i18n` und die Stylesheets, baut den Router aus `routes`.
2. [`src/routes.tsx`](../../frontend/src/routes.tsx): alle Pfade unter `SessionProvider` und `Layout`; Schutz der Seiten mit `RequireRole`.
3. [`src/api/client.ts`](../../frontend/src/api/client.ts) und [`src/hooks/useApi.ts`](../../frontend/src/hooks/useApi.ts): wie eine Seite Daten holt.
4. Eine einfache Seite wie [`QueuePage.tsx`](../../frontend/src/pages/QueuePage.tsx), danach eine mit Formular wie [`ApiTokens.tsx`](../../frontend/src/pages/account/ApiTokens.tsx).
5. Für Partien [`src/viewer/Viewer.tsx`](../../frontend/src/viewer/Viewer.tsx) und [`src/play/usePlayGame.ts`](../../frontend/src/play/usePlayGame.ts).

## Module

Pfade relativ zu `frontend/src/`.

### Rahmen, API, Hooks

| Modul | Aufgabe |
|-------|---------|
| `main.tsx` | Wurzel: `createBrowserRouter(routes)` in `StrictMode`, Übersetzungen und CSS laden |
| `routes.tsx` | Alle Routen als `RouteObject[]`; dieselbe Liste rendern die Tests |
| `api/schema.d.ts` | Von `openapi-typescript` erzeugte Typen (`paths`, `components`, `operations`); nie von Hand ändern, ESLint und Prettier lassen sie aus |
| `api/types.ts` | Kurze Aliase auf `components["schemas"]` und Abfrageparameter (`Query<"list_matches">`) |
| `api/client.ts` | `fetch`-Hülle: `getJson`, `getBytes`, `sendJson`, `sendForm`, `apiUrl`; `ApiError` mit `code`, `status`, `field`, `path`; Netzfehler als Code `network`; Header `X-SBM-CSRF: 1` bei jeder Änderung (E84) |
| `api/endpoints.ts` | Lesende öffentliche Endpunkte: Partien, Serien, Gegner, Bots, Ratings, Queue, Disziplinen |
| `api/account.ts` | Sitzung, Anmeldung, Einladung, Passwort, eigenes Rating, Grenzen, API-Tokens |
| `api/admin.ts` | Nutzer, Einladungen, Partien ansetzen, Queue-Eingriffe, Bot-Sperre und -Löschung, Neuprüfung, Disziplinen, Ligen anlegen, ändern und wartende Saison starten (E171), Play-Grenzen, Einstellungen, Audit-Log |
| `api/leagues.ts` | Ligen, Liga mit Anmeldungen, Saison mit Tabellen, Ligen eines Bots; Bot oder Konto an- und abmelden (E136, E137, E182); Spielplan einer Stufe und Saisons eines Bots (E138, E139) |
| `api/tournaments.ts` | Turniere, Turnier mit Ausgaben und Anmeldungen, Ausgabe, Runden einer Ausgabe, Turniere und Ausgaben eines Bots; Bot oder Konto an- und abmelden (E170–E180, E182) |
| `api/participants.ts` | `participantId`: Kennung einer Anmeldung, `bot_id` eines Bots oder `user_id` eines Kontos (E182) |
| `api/competitionGames.ts` | Eigene offene Liga- und Turnierpartien (`GET /account/competition-games`) und `declareReady` (`POST /matches/{id}/ready`, E183) |
| `api/adminTournaments.ts` | Turnier anlegen, ändern und wartende Ausgabe starten (E170–E172) |
| `api/botHistory.ts` | Rating-Verlauf und Bilanz eines Bots (E140, E141) |
| `api/bots.ts` | Upload als `FormData`, Bot, eigene Bots, Dateien und ZIP, eigene Partien ansetzen und zurückziehen |
| `api/play.ts` | `startGame`: `POST /play`, Antwort mit Sitz-Token (E114) |
| `api/positions.ts` | `positionFromPgn`: FEN aus `POST /positions/from-pgn` (E159) |
| `hooks/useApi.ts` | Laden je `key`, Abbruch per `AbortSignal`, optionales Abfrageintervall (fest oder abhängig von den Daten), `reload`; Daten bleiben bei Fehlern stehen |
| `hooks/polling.ts` | Intervalle: wartende Partie und laufende ohne Event-Stream 2 s, Listen und Queue 10 s, Verifikation 3 s (E76, E77, E142) |
| `hooks/useLiveMatch.ts` | Partie für die Partieseite: lädt über `useApi`, folgt einer laufenden Partie über `EventSource` (`matchLiveUrl`) und hängt die Züge an; fragt bei offenem Strom nicht nach, sonst alle 2 s; Lücke schließt den Strom, `end` lädt neu (E142) |
| `hooks/useRegistrableBots.ts` | Bots für die Anmeldung in Ligen und Turnieren: Admins alle geprüften (`GET /bots`), Coder ihre eigenen (E181) |
| `hooks/useSubmit.ts` | Eine Änderung zur Zeit: `pending`, `error` (`ApiError` oder Übersetzungsschlüssel), `submit`, `fail` |
| `hooks/useLocale.ts` | Aktive Sprache `de`/`en` für `Intl`-Formate |

### Sitzung, Sprache, Darstellung

| Modul | Aufgabe |
|-------|---------|
| `session/SessionProvider.tsx` | Fragt `GET /session` einmal; ohne Antwort gilt der Besucher als Gast |
| `session/sessionContext.ts` | `useSession()`: `user` (`undefined` beim Laden, `null` für Gäste) und `setUser` nach Login oder Logout |
| `session/RequireRole.tsx` | Gäste zur Anmeldung mit `?next=`; falsche Rolle sieht `error.forbidden`; Admins dürfen alles, `role="coder"` sperrt `player` |
| `session/nextPath.ts` | Rücksprungziel nach dem Login, nur Pfade dieser Seite |
| `session/oneTimeToken.ts` | `useOneTimeToken`: Token hinter `#` lesen und aus Adresse und Verlauf entfernen (E83) |
| `i18n/index.ts` | i18next mit `de.json`, `en.json`; Sprache aus `localStorage` (`sbm.language`) oder Browser, Rückfall Englisch (E32) |
| `i18n/de.json`, `i18n/en.json` | Alle Texte, Schlüssel nach Bereich (siehe [Konventionen](#konventionen)) |
| `styles/base.css` | Farbvariablen hell/dunkel, Grundelemente |
| `styles/layout.css` | Kopfzeile, Navigation, Tabellen, Reiter |
| `styles/forms.css` | Eingabefelder und Formulare |
| `styles/bot.css` | Bot-Seite: Beschreibung, Dateien, Report |
| `styles/viewer.css` | Raster von Brett und Seitenleiste, Steuerung, Zugliste |
| `styles/landing.css` | Startseite: Einleitung, Schritte, Abschnitte zur Idee (E166) |

### Gemeinsame Bausteine

| Modul | Aufgabe |
|-------|---------|
| `components/Layout.tsx` | Kopf mit Hauptnavigation (`NAV`, seit E170 mit „Turniere“), `AccountNav`, Sprachumschalter, `Outlet` |
| `components/AccountNav.tsx` | Anmelden für Gäste; „Meine Bots“ (nicht für `player`), Verwaltung für Admins, Konto; Abmelden über `session/useLogout.ts` |
| `components/LanguageSwitch.tsx` | Knöpfe Deutsch/Englisch |
| `components/ApiContent.tsx` | Daten aus `useApi` rendern, sonst Fehler oder Laden |
| `components/Loading.tsx`, `ErrorMessage.tsx` | Ladehinweis; Fehlercode als `error.<code>` |
| `components/FormError.tsx` | Formularfehler: Feldregel aus `rules`, dann `fieldError`, dann `error.<code>`; bei `invalid_upload` Datei und Meldung |
| `components/MatchTable.tsx`, `Pager.tsx` | Partientabelle mit Paarung, Ergebnis in derselben Reihenfolge und „Öffnen“ (E165); Blättern über `offset` |
| `components/TableShell.tsx` | Tabelle mit Hinweis bei leerer Liste (E168) |
| `components/Pairing.tsx`, `SideName.tsx` | `PairingHeader`/`PairingCells`: beide Seiten alphabetisch in eigenen Spalten mit „–“ dazwischen; Name einer Seite ohne Version, Bot als Link (E165) |
| `components/OpenCell.tsx` | Knopf „Öffnen“ statt unterstrichener Zeile, `ActionsHeader` für die Spalte (E165) |
| `components/QueueTable.tsx` | Eine Queue-Tabelle für alle: Sicht `public`, `admin` (Priorität, Eingriffe über `actions`) und `own` (E167) |
| `components/PillSelect.tsx` | Pillenauswahl für wenige Optionen statt Dropdown (E168) |
| `components/ConfirmButton.tsx` | Zweiter Klick bestätigt; für Sperren, Zurückziehen, Abmelden von Partien, Token widerrufen (E168) |
| `components/StatusBadge.tsx`, `BotStatusBadge.tsx` | Status einer Partie bzw. eines Bots als Plakette (E168) |
| `components/ExploreLinks.tsx` | Links zu Partien, Rangliste, Spielen und Start (404 und Login) |
| `components/NumberField.tsx`, `PasswordFields.tsx`, `RatedField.tsx` | Zahlenfeld, Passwort doppelt (10–128 Zeichen), Kästchen „Gewertet“ (E158) |
| `components/BotPicker.tsx`, `DisciplineSelect.tsx` | Bot nach Name, dann Version, mit „Zufall“ (E162, E165; bis E165 `BotOptions.tsx`); Disziplin oder freie Zeiten (E100) |
| `components/matchFields/` | `MatchFields` mit `ColorSelect` und `conditions.ts`: gemeinsame Felder für Admin, Coder und `/play` (Varianten `admin`, `coder`, `play`, E167) |
| `components/StartPositionField.tsx` | FEN-Feld mit „Aus PGN“ (E159) |
| `components/ScheduleRounds.tsx` | Runden als aufklappbare Abschnitte mit Partien, offen die erste nicht beendete; gemeinsam für Spielplan einer Liga und Runden eines Turniers (E138, E180) |
| `components/RecurrenceText.tsx` | Kalender als Text in Ortszeit: Intervall mit erstem Start oder Start durch Admins (E171) |
| `components/QueuedNotice.tsx` | Bestätigung nach dem Ansetzen, Link auf die Serie (E155) |
| `components/CopyButton.tsx`, `OneTimeLinkBox.tsx` | In die Zwischenablage kopieren; einmal sichtbarer Link (E83) |
| `format/*.ts` | Reine Formatierer: `pairing` (Seiten alphabetisch, Ergebnis gedreht, `compareSides`, E165), `botGroups` (Versionen je Name), `clock`, `dateTime`, `duration` (Sekunden/Minuten mit Komma ↔ ms, E168), `points` (½), `recurrence` (Intervall als größte passende Einheit, E171, E180), `rating` (2500 → 2550, ohne Partien „–“), `result`, `score` (Sicht von Weiß), `timeControl` („3 min + 2 s“, E168), `competition` („Bundesliga, Saison 2“, E183); `botLabel` ist seit E165 entfallen |
| `chess/fen.ts` | Felder der FEN lesen: Seite am Zug, Zugnummer, Materialbilanz, Felder eines UCI-Zugs; keine Regeln |
| `upload/selection.ts` | Welche Dateien eines Ordners hochgeladen werden, Grenzen 100 Dateien und 1 MB (E92) |
| `upload/version.ts` | Muster für Name und Version, Vorschlag der nächsten Patch-Version |
| `upload/dropped.ts` | Gezogene Ordner und Dateien lesen; versteckte Ordner und `__pycache__` bleiben weg |

### Viewer (`viewer/`)

| Modul | Aufgabe |
|-------|---------|
| `Viewer.tsx` | Setzt Brett, Spielerleisten, Steuerung, Details, Zugliste, Bot-Info und Export zusammen |
| `game.ts` | Stellung, Uhren und Ziehender je Halbzug aus `match.moves`; Zugliste in Zeilen |
| `useViewerPly.ts` | Halbzug in der URL (`?ply=N`); ohne `ply` letzter Zug, bei laufender Partie „live folgen“ |
| `playback.ts`, `usePlayback.ts` | Geschwindigkeiten 0,5×–4× und `"real"` nach `spent_ms` (mindestens 50 ms); Abspielen bis zum letzten Zug |
| `useViewerKeys.ts` | Pfeiltasten, Pos1/Ende, Leertaste; Formularfelder behalten ihre Tasten |
| `Board.tsx` | `react-chessboard` ohne Ziehen, letzter Zug markiert |
| `PlayerBar.tsx`, `Controls.tsx` | Name, Material und Uhr je Seite; Navigation, Wiedergabe, Brett drehen |
| `MoveList.tsx`, `MoveInfoPanel.tsx` | SAN mit Zugzeit, Klick springt; Bot-`info` des Zugs (E33) |
| `MatchDetails.tsx`, `ExportPanel.tsx` | Metadaten mit Rating-Änderung; PGN, FEN und Link mit `?ply=` |

### Spielen im Browser (`play/`)

| Modul | Aufgabe |
|-------|---------|
| `protocol.ts` | Nachrichten von gateway-v1 (`join`, `joined`, `refused`) und play-v1 (`state`, `move`, `resign`, `error`); unbekannte werden verworfen |
| `usePlayGame.ts` | WebSocket je Sitz: `join` beim Öffnen, Phasen `connecting` … `lost`, Neuverbindung nach 0,5–8 s, Aufgabe nach 55 s ohne Verbindung; Close-Code 1000 heißt Ende |
| `seats.ts` | Sitz-Token je Partie im `localStorage`, ohne Speicher nur für die Dauer der Seite (E113); Art `play` für Partien aus `/play`, `ready` für Wettbewerbspartien (E183) |

### Seiten (`pages/`)

| Bereich | Module |
|---------|--------|
| Öffentlich | `StartPage` (Idee des Projekts, keine Abfragen, E166), `MatchesPage` (Filter in der URL, E156, E119), `MatchPage` (Viewer mit `useLiveMatch`, folgt laufenden Partien über den Live-Kanal), `MatchSeries` (Platz in der Serie), `QueuePage` (`QueueTable` in der Sicht `public`), `BotsPage`, `RatingsPage` mit `ranking.ts` (Bots und Spieler gemeinsam sortiert, E118, E163), `series/SeriesPage` (E155), `MatchLeague` (Liga, Saison und Runde einer Ligapartie), `MatchTournament` (Turnier, Ausgabe und Runde einer Turnierpartie, E178, E180), `NotFoundPage` |
| Ligen (`leagues/`) | `LeaguesPage`, `LeaguePage` mit `LeagueFacts`, `LeagueSeasons`, `NextSeason`, `LeagueRegistrations` und `LeagueRegisterForm` (E136, E137) samt `components/registration/SelfRegistration` und `AccountRegistration` (E182), `SeasonPage` mit `TierTable` je Staffel (E134) und darin `TierSchedule` (E138) |
| Turniere (`tournaments/`) | `TournamentsPage`, `TournamentPage` mit `TournamentFacts`, `TournamentEditions`, `NextEdition`, `TournamentRegistrations` und `TournamentRegisterForm` samt `SelfRegistration` und `AccountRegistration` (E182), `EditionPage` mit `EditionState`, `EditionParticipants`, `EditionTable` (Round-Robin und Schweizer System), `EditionRoundsSection`, `KnockoutBracket` und `KnockoutPlacements` (K.-o.) (E170–E180) |
| Konto (`account/`) | `LoginPage`, `InvitePage` und `ResetPasswordPage` (Token aus `#`), `AccountPage` mit `OwnRating` (E117) und `ApiTokens` (E116) |
| Upload (`upload/`) | `UploadPage` mit `FileDrop` (Ordner oder Dateien, auch per Ziehen, Name, Version, Beschreibung, E91), `SelectedFiles` (Hochgeladenes und Weggelassenes) |
| Bot (`bot/`) | `BotPage` (fragt während Verifikation und Neuprüfung alle 3 s) mit `BotHeader` (Name, Version, Status), `BotActions` (Schnellstart, Besitzer) und `BotAdmin` (Eingriffe der Admins), `BotSummary`, `BotDescription`, `BotVersions` mit `playLink.ts` (E160), `BotOpponents` (E161), `BotFiles` mit `FileView` (nur UTF-8-Text, E97), `ReportView`, `ReportStages`, `FindingsTable`, `TestGamesTable`, `reportFacts.ts`, `BotRechecks` (E153), `BotLeagues` (Ligen des Bots), `BotSeasons` (E139), `BotRatingChart` mit `ratingChart.ts` (SVG, E140), `BotResults` (E141), `BotTournaments` und `BotEditions` (E179, E180); Eingriffe `BotOwnerSwitch` (E96), `BotStatusSwitch` (E93), `BotChecks` (E153), `BotDelete` (E105) |
| Meine Bots (`ownBots/`) | `OwnBotsPage`, `OwnBotGroups` (nach Name gruppiert), `OwnMatchForm` mit `ownMatchOrder.ts` und `ownLimits.ts` (E98, E154), `OwnWaitingMatches` (E157) |
| Spielen (`play/`) | `PlaySetupPage` (`POST /play`, Sitz speichern, weiter zu `/play/:id`) mit `OwnCompetitionGames` (eigene Wettbewerbspartien, E183), `GamePage` (nimmt `createSocket` für Tests; mit Sitz `Game`, sonst für angemeldete Konten `CompetitionGame` mit „Bereit“ und Anwesenheit alle 15 s, E183), `Game` (Brett einer Partie), `PlayBoard` (nur Züge aus `legal_moves`), `PromotionChoice`, `GameClock` |
| Admin (`admin/`) | `AdminLayout` (Reiter, `RequireRole role="admin"`); Reiter „Queue“: `AdminMatchesPage` mit `QueueControl`, `AdminQueueTable` (`QueueTable` in der Sicht `admin`), `QueueEntryActions` (E152, E167), `EnqueueForm` mit `MatchFields` und `matchOrder.ts`; Reiter „Neuprüfung“: `RecheckLanguage` unter `/admin/rechecks` (E153); `MatchRepeat` (Partieseite, E152); `AdminUsersPage`; `AdminInvitesPage` mit `InviteForm`; `AdminDisciplinesPage` mit `DisciplineEditor` und `disciplineForm.ts` (E100); `AdminLeaguesPage` mit `LeagueEditor`, `TiebreakField` und `leagueForm.ts` (E131, E132, Kalender seit E171); `AdminTournamentsPage` mit `TournamentEditor`, `tournamentForm.ts` und `startable.ts` (E170, E172); `RecurrenceField` mit `recurrenceForm.ts` für Ligen und Turniere (E171); `AdminPlayPage` (E115); `AdminAuditPage` mit `AuditTable` (Ziel mit Namen, E151, E169); `AdminSettingsPage` mit `SettingsGroupFields` und `settingsFields.ts`, ein Speichern für alle Gruppen (E154, E168) |

## Ablauf

**Laufende Partie ansehen** (`/matches/:id`):

1. `MatchPage` ruft `useLiveMatch(id)`, das `useApi(fetchMatch, id, poll)` nutzt; `poll` gibt `POLL_MATCH_MS` zurück, solange der Status `queued` ist oder die Partie läuft und kein Event-Stream offen ist, sonst `undefined`. Läuft die Partie, öffnet der Hook `EventSource` auf `/api/v1/matches/{id}/live?after=n` (Gateway, E142) und hängt jeden `move` an; bei `end` ruft er `reload()`.
2. `fetchMatch` → `getJson` → `fetch("/api/v1/matches/…")`. Ein Fehler wird zu `ApiError`; `useApi` behält die alten Daten.
3. `ApiContent` rendert `Viewer` mit `live`. `useViewerPly` liest `?ply`; ohne Wert zeigt der Viewer den letzten Zug und folgt damit neuen Zügen.
4. `game.ts` liefert FEN und Uhren zum Halbzug; `Board` zeigt die FEN, die Leisten zeigen Uhren und Material aus `chess/fen.ts`.
5. Blättern, Tasten und Wiedergabe rufen `goTo`, das nur `?ply` ersetzt (`replace`). Der Link im Export enthält denselben Parameter.

**Partie gegen einen Bot** (`/play` → `/play/:id`):

1. `PlaySetupPage` sendet `startGame` (`POST /play`), speichert `seat` mit `saveSeat` und navigiert zu `/play/<match_id>`.
2. `GamePage` liest den Sitz mit `loadSeat`; ohne Sitz Hinweis `play.noSeat`.
3. `usePlayGame` öffnet `ws(s)://<host>/api/v1/play/socket` (`socketUrl`) und sendet `joinMessage`. Nach `joined` ist die Phase `waiting`, jeder `state` ersetzt den Stand ganz.
4. `PlayBoard` bietet nur Züge aus `state.legal_moves`; mehrere Züge zwischen denselben Feldern gehen über `PromotionChoice`. `move` sendet `moveMessage`, ein `error` landet in `problem`.
5. Bricht die Verbindung ohne Code 1000 ab, verbindet der Hook neu; der Server schickt den Stand erneut ([gateway.md](../komponenten/gateway.md)).

**Wettbewerbspartie eines Kontos** (`/play/:id`, E183):

1. `GamePage` findet keinen Sitz der Art `play` und zeigt für ein angemeldetes Konto `CompetitionGame`; es fragt `fetchCompetitionGames` alle 5 s.
2. Ist die Partie freigegeben, sendet „Bereit“ `declareReady` und speichert den Sitz mit `saveSeat(id, seat, "ready")`. Solange die Seite offen ist, wiederholt `usePresence` das alle 15 s; das Konto gilt so als anwesend.
3. Hat der Runner die Partie gestartet (`readiness.started_at` oder Status nicht mehr `queued`), zeigt `CompetitionGame` das Brett mit `Game` und dem Sitz der Art `ready`; weiter wie oben ab Schritt 3.

## Konventionen

- **Ein API-Aufruf, eine Funktion** in `src/api/<bereich>.ts`. Sie nimmt bei GET ein `AbortSignal`, nutzt nur Typen aus `types.ts` und übersetzt Parameter in `snake_case` der API (`botId` → `bot_id`). Listen kommen als `{ items }` und werden ausgepackt.
- **Typen nur aus dem Schema.** Neue Typen als Alias in `types.ts`, nie eigene Interfaces für API-Daten.
- **Laden mit `useApi`.** Der `key` enthält alles, wovon die Abfrage abhängt (`bot:${id}`, `JSON.stringify(query)`); ein neuer Key zeigt nichts Altes. Nach einer Änderung `reload()`.
- **Ändern mit `useSubmit`.** Die Aktion läuft in `submit(async () => …)`; Fehler zeigt `FormError`. Prüfungen im Browser setzen mit `fail("schlüssel")` einen Übersetzungsschlüssel.
- **Fehler als Codes.** Die englische `message` der API erscheint nie, außer bei `invalid_upload`. Texte unter `error.<code>`, Feldregeln unter `fieldError.<feld>` oder einem eigenen Bereich des Formulars (`playError`, `ownMatchError`, `tokenError`, `settingsError`, `pgnError`, `disciplineError`), mit Platzhaltern wie `{{games}}` über `values`.
- **Übersetzungen** in `de.json` und `en.json` mit gleichem Aufbau: oberste Ebene ein Bereich (`nav`, `common`, `matches`, `bot`, `admin`, `play` …), darunter flache Schlüssel. Werte aus der API mit eigenem Bereich: `status`, `termination`, `botStatus`, `role`, `language`, abgefragt als `` t(`status.${…}`) ``. Namen von Bots und Spielern bleiben unübersetzt.
- **Zustand in der URL:** Filter, Seite, Halbzug und Vorbelegung von Formularen (`?white=`, `?own=`) über `useSearchParams`.
- **Rechte in der UI sind Komfort** (`RequireRole`, `AccountNav`, Knöpfe nur für Besitzer oder Admins); die API prüft selbst.
- **Keine Schachregeln im Browser.** Viewer und Spielbrett zeigen nur FEN und Züge vom Server.
- **Kommentare** auf Englisch als JSDoc über jedem exportierten Baustein, mit Verweis auf die Entscheidung (`(E152)`).
- **Format:** Prettier mit `printWidth` 100; ESLint mit `react-hooks` und `react-refresh`.

## Erweitern

**Neue Seite**

1. Komponente unter `src/pages/` bzw. dem Unterordner des Bereichs anlegen, Daten über `useApi` und `ApiContent`.
2. Route in `src/routes.tsx` eintragen; geschützt mit `<RequireRole>` (angemeldet) oder `<RequireRole role="coder">`. Admin-Seiten als Kind von `admin` und Eintrag in `SECTIONS` von `AdminLayout.tsx`.
3. Link in `NAV` von `components/Layout.tsx` (öffentlich) oder in `AccountNav.tsx` (Konto).
4. Texte unter einem neuen Bereich in `de.json` und `en.json`, dazu `nav.<name>`.
5. Test in `src/pages/<thema>.test.tsx` mit `mockApi` und `renderRoute("/pfad")`, auch für Gast und falsche Rolle.
6. [frontend.md](../komponenten/frontend.md) und bei neuer Entscheidung `docs/00_entscheidungen.md` nachführen.

**Neuer API-Aufruf**

1. Endpunkt zuerst in [`spec/web/openapi.json`](../../spec/web/openapi.json) und im Backend.
2. `npm run api-types`; die geänderte `schema.d.ts` mit einchecken.
3. Alias in `api/types.ts`, Funktion in der passenden Datei unter `api/` mit `getJson`, `sendJson` oder `sendForm`.
4. Neue Fehlercodes als `error.<code>` in beiden Sprachdateien.
5. Seite oder Komponente nutzt die Funktion; Test mit einer Antwort für den neuen Pfad in `mockApi`.

**Neues Formular mit Fehlern vom Server**

1. Zustand mit `useState`, Absenden mit `useSubmit().submit(async () => { await call(); reload(); })`.
2. Liefert die API `invalid_parameter` mit `field`, Regeltext unter `<bereich>Error.<feld>` anlegen und `<FormError error={error} rules="<bereich>Error" values={…} />` rendern; ohne eigenen Bereich greift `fieldError.<feld>`.
3. Feldwerte in Einheiten der Eingabe halten und erst beim Senden umrechnen (Muster `matchOrder.ts`, `disciplineForm.ts`: Sekunden → ms).
4. Test: `mockApi` antwortet mit `Response.json({ code: "invalid_parameter", message: "…", field: "…" }, { status: 400 })`; erwartet wird der Regeltext in `getByRole("alert")` und der Request-Body in `api.calls`.

## Tests

Vitest mit jsdom und Testing Library; Einrichtung in [`vite.config.ts`](../../frontend/vite.config.ts) (`test.environment`, `setupFiles`). Tests liegen neben dem Code (`*.test.ts`) oder als Seitentests unter `src/pages/*.test.tsx`.

| Hilfsmodul | Zweck |
|------------|-------|
| `test/setup.ts` | `jest-dom`-Matcher; vor jedem Test `localStorage` leeren und Sprache Englisch; danach `cleanup`, Mocks und Timer zurücksetzen |
| `test/render.tsx` | `mockApi(responses)` ersetzt `fetch`: Antwort je Pfad ohne `/api/v1` und Query, als Wert, `Response` oder Funktion `(url, call)`; unbekannte Pfade geben 404 `not_found`. Liefert `requests` und `calls` (`ApiCall` mit `url`, `method`, `headers`, JSON-`body`, `form`). `renderRoute(path)` rendert die echten `routes` in einem Memory-Router und gibt `router` zurück |
| `test/fixtures.ts` | Testdaten: `START_FEN`, `OPENING`, `match()`, `summary()`, `side()`, `BOTS`, `botDetail()`, `queue()`, `storedDiscipline()`, `adminSettings()`, `CODER_LIMITS`, Konten `ADMIN`, `CODER`, `PLAYER`, `user()`, `ownMatches()` |
| `test/leagues.ts` | Testdaten für Ligen: `LEAGUE_ID`, `SEASON_ID`, `league()`, `registration()`, `leagueDetail()`, `season()`, `schedule()`, `botSeason()` |
| `test/fakeEventSource.ts` | `FakeEventSource` als Ersatz für `EventSource` (`vi.stubGlobal`): `open()`, `emit(type, data)`, `fail()`, `closed`, `url`, `FakeEventSource.latest()` |
| `test/tournaments.ts` | Testdaten für Turniere: `TOURNAMENT_ID`, `EDITION_ID`, `tournament()`, `tournamentRegistration()`, `tournamentDetail()`, `swissEdition()`, `knockoutEdition()`, `botEdition()` |
| `test/fakeSocket.ts` | `FakeSocket` als Ersatz für `WebSocket` (`vi.stubGlobal`): `open()`, `receive(msg)`, `drop(code)`, `sentMessages()`, `FakeSocket.latest()` |
| `test/files.ts` | `folderFile`: Datei wie aus einer Ordnerauswahl (`webkitRelativePath`) |

- Jeder Seitentest antwortet auf `/session` (z. B. `{ user: CODER }`), sonst ist der Besucher Gast.
- `Viewer.test.tsx` ersetzt `react-chessboard` per `vi.mock`, weil jsdom keine Maße kennt; `play.test.tsx` nutzt das echte Brett über `data-square`.
- Texte werden auf Englisch geprüft; ein fehlender deutscher Schlüssel fällt in den Tests nicht auf.

Befehle in `frontend/` (nach `npm ci`, Node ab 22.12), wie im CI-Job `frontend`:

```
npm run api-types:check
npm run lint
npm run format:check
npm test
npm run build
```
