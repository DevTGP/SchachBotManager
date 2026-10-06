# Entscheidungen, Annahmen, offene Punkte

Stand: 2026-10-06, Revision 4 mit Festlegungen für M0 (E34–E53; vorherige Stände unter `_archiv/`)

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
| E8 | Fairness | **Keine Sprachfaktoren.** Alle Sprachen haben identische Zeiten und Schutzgrenzen (geändert) | Langsamere Sprachen sind benachteiligt; Disziplinen enthalten keine sprachspezifischen Einstellungen |
| E9 | Frontend-Framework | React + TypeScript, Build mit Vite | – |
| E10 | Sichtbarkeit | Partien, Tabellen, Bot-Profile sind öffentlich | Lesende API-Routen ohne Login |
| E11 | Mensch gegen Bot | Jeder Besucher darf spielen, ohne Account | Kapazitätsgrenzen pro IP/gesamt nötig |
| E12 | Hardware | Schwacher, nicht dedizierter Server | Standard: ein Spiel gleichzeitig; Störungen durch andere Dienste werden hingenommen |
| E13 | Konfiguration | Alles über die Website einstellbar (Disziplinen, Ligen, Turniere, Queue); Ressourcenlimits ausgenommen (E23) | Konfiguration liegt in der DB, Admin-UI für jeden Parameter |
| E14 | Versionen pro Liga | Keine Obergrenze | Bots lassen sich deaktivieren |
| E15 | Quellcode | Für andere nicht einsehbar | Nur Besitzer und Admin |
| E16 | Bibliotheken | Whitelist laut [statische-analyse.md](komponenten/statische-analyse.md) | Auf Typ-/Funktionsebene |
| E17 | Bot verlässt Liga | Bot wird aus der Tabelle entfernt; gespielte Partien zählen normal, ausstehende als kampfloser Sieg des Gegners (eigens markiert); ein Bot weniger steigt ab | Siehe [ligen-turniere.md](komponenten/ligen-turniere.md) |
| E18 | Isolation | Einfache Isolation ohne Docker: **nsjail** | Siehe [sandbox.md](komponenten/sandbox.md) |
| E19 | Zeitmessung | Wanduhrzeit (Systemzeit), keine CPU-Zeit | Bedenkzeit läuft unabhängig von der tatsächlich erhaltenen Rechenzeit |
| E20 | Spielplanung | Eine Queue; Spiele starten direkt nacheinander; online stehen geschätzte Startzeiten | Keine festen Termine |
| E21 | SDK-API | Callback-Modell; hohe Ebene plus Rohzugriff aufs Brett; Schreibweise idiomatisch pro Sprache | Siehe [sdk-api.md](komponenten/sdk-api.md) |
| E23 | Ressourcenlimits | Konfigurierbare Ressourcenlimits (Speicher, CPU, Dateigröße) und darauf aufbauende Disziplinen sind **zurückgestellt**; Ausgestaltung offen | Disziplinen enthalten vorerst nur Zeitkontrolle und Regeln; die Sandbox arbeitet mit festen Schutzgrenzen |
| E24 | Mensch gegen Bot und Queue | Spiele gegen Menschen und Remote-Bots laufen an der Queue vorbei, mit eigener Kapazitätsgrenze | Können eine laufende Liga-Partie zeitlich stören (R10) |
| E25 | Kampflose Siege | Zählen als Punkte; kein Einfluss auf Rating, Sonneborn-Berger und direkten Vergleich | – |
| E26 | Server | Ubuntu auf x86-64 | Sandbox, Laufzeiten und Server-Build nur für diese Plattform |
| E27 | Repo | Öffentlich auf GitHub | Keine Secrets, Domains oder Serverdetails im Repo; kein Self-hosted Runner |
| E28 | Deployment | Wie in deinen anderen Projekten: GitHub Actions verbindet sich per SSH, setzt den Compose-Stack, die Container bauen den Rest auf dem Server | Kein Registry-Zwang; Build-Last liegt auf dem Server |
| E29 | Proxy | Bestehender Nginx Proxy Manager, Docker-Netz `local-web`; Subdomain einer vorhandenen Domain; Portfreigabe 80/443 | Der Stack bringt keinen eigenen Proxy und kein TLS mit |
| E30 | Upload | Mehrere Quelldateien erlaubt; Datendateien bis insgesamt 1 MB | Zugriff auf Datendateien nur über eine SDK-Funktion |
| E31 | Laufzeiten | Jeweils aktuelle stabile Version zum Zeitpunkt der Umsetzung, danach fest gepinnt | – |
| E32 | Sprache der Oberfläche | Deutsch und Englisch | Übersetzungsdateien von Beginn an |
| E33 | Bot-`info` | Bewertung/Tiefe eines Bots sind im Viewer öffentlich | – |
| E22 | Brett-Instanz | Jeder Bot hat sein eigenes Brett im eigenen Prozess; Probezüge sind rein lokal | Der Match-Runner sieht nur den abgegebenen Zug |
| E34 | Zugkodierung | Zug als 16-Bit-Ganzzahl: Bits 0–5 Startfeld, 6–11 Zielfeld, 12–15 Flags (0 ruhig, 1 Doppelschritt, 2/3 kurze/lange Rochade, 4 Schlagzug, 5 en passant, 8–11 Umwandlung S/L/T/D, 12–15 Umwandlung mit Schlagen); `0` = `NULL_MOVE` | `is_capture`, `is_castling`, `is_en_passant`, `promotion` ohne Brett lesbar; `Move.parse(uci)` kennt keine Flags, deshalb `board.parse_move(uci)`; `is_legal`/`make_move` vergleichen nur Start, Ziel, Umwandlung |
| E35 | Figur, Farbe, Feld | `WHITE = 0`, `BLACK = 1`; `PAWN = 0` … `KING = 5` (Bauer, Springer, Läufer, Turm, Dame, König); `Piece = color * 6 + type` (0–11), `NO_PIECE = 12`; Feld = `rank * 8 + file` (a1 = 0 … h8 = 63); Bit *i* eines Bitboards = Feld *i* | Index in `bitboards()` = `Piece`-Code; `squares()` liefert 64 `Piece`-Codes; Umwandlungsfigur = `(flags & 3) + 1` |
| E36 | Protokollversion | `v` ist eine Ganzzahl, erhöht nur bei inkompatiblen Änderungen; Aushandlung über `supported` in `init` und `v` in `ready`; SDK-Version nach SemVer, gleich für Kern und alle Bindings, jede SDK-Version spricht genau eine Protokollversion | SDK ignoriert unbekannte Felder vom Referee; Referee prüft Bot-Nachrichten streng gegen das Schema; Schemas unter `spec/protocol/v<N>/` als JSON Schema 2020-12 |
| E37 | Testvektoren | Durchgehend JSON, je Thema eine Datei (`perft`, `fen`, `uci`, `rules`, `api/*`); jeder Vektor hat eine `id`; tiefe Perft-Läufe mit `"slow": true` | Eigenes Schema für die Vektordateien; Perft-Stellungen aus dem Chess Programming Wiki |
| E38 | Kern-Toolchain | C++20, Build mit CMake | – |
| E39 | Format von `spec/api/` | JSON, mit eigenem Schema | Quelle für Binding-Tests und die spätere API-Referenz (M8) |
| E40 | Lizenz | MIT-0 (MIT No Attribution) | Gilt für das ganze Repo inklusive SDKs; Bot-Autoren unterliegen keinen Auflagen |
| E41 | Versionsstabile Nachrichten | `init`, `error` und `game_over` tragen kein `v`; ihr Format bleibt über alle Protokollversionen gleich und wird nur ergänzt | Jedes SDK kann sie lesen, auch wenn die Aushandlung scheitert; `turn`, `move`, `resign`, `ready` tragen `v` |
| E42 | FEN in `turn` | Der Referee sendet die FEN in jedem `turn`; bei Abweichung vom eigenen Brett übernimmt das SDK sie und protokolliert eine Warnung | Wiederholungshistorie geht dabei verloren; Abweichung gilt als SDK-Fehler |
| E43 | Bot-`info` | Optionale Felder `depth`, `seldepth`, `score_cp` oder `score_mate`, `nodes`, `pv` (≤ 32 Züge), `text` (≤ 256 Zeichen) | Feste Obergrenzen im Schema; unbekannte Felder sind ein Protokollverstoß |
| E44 | Spielende im Protokoll | `game_over` enthält `result` (PGN, `*` = abgebrochen) und `termination` aus einer festen Code-Liste; dieselben Codes speichert die Datenbank | Schema erzwingt, dass `result` zum Code passt; `forfeit_withdrawn` gibt es nur in der Datenbank |
| E45 | Info und Aufgabe im SDK | `Bot.report(info)` speichert die Suchinformation des laufenden Zuges; der letzte Aufruf vor der Rückgabe wird mit dem Zug gesendet. Aufgeben durch Rückgabe von `Move.RESIGN` (`0xFFFF`, nie ein legaler Zug) | `choose_move` hat genau eine Rückgabeform; `report` wirkt nicht über den Zug hinaus und ist bei Aufgabe wirkungslos |
| E46 | Zobrist-Hash | `board.hash()` nutzt die veröffentlichten Polyglot-Schlüssel und ist gleich dem Polyglot-Buchschlüssel der Stellung | Hashwerte in Testvektoren festlegbar; Polyglot-Eröffnungsbücher über `load_data` nutzbar; En-passant-Anteil nach Polyglot-Regel (Bauer daneben, ohne Legalitätsprüfung) |
| E47 | Namen und Codes der API | Kanonisch `snake_case` für Funktionen, Felder, Parameter, `PascalCase` für Typen und Fehler, `UPPER_SNAKE` für Konstanten; Konstruktor `create` wird zum Konstruktor der Sprache; `Move.from_square`/`to_square` statt `from`/`to`; `NO_PIECE_TYPE = 6`, `NO_SQUARE = 64`; Rochaderechte als Bitmaske (1 weiß kurz, 2 weiß lang, 4 schwarz kurz, 8 schwarz lang) | `from` ist in Python reserviert; Felder A1–H8, Zug-Flags und Log-Stufen als benannte Konstanten in `spec/api/constants.json` |
| E48 | En passant in der FEN | `fen()` und `en_passant_square()` nennen das Feld nur, wenn ein Schlagen en passant legal ist; `from_fen` nimmt ein Feld ohne legales Schlagen an und verwirft es | Gleiche Stellungen ergeben gleiche FEN (Abgleich nach E42, Wiederholungserkennung); `hash()` folgt davon abweichend der Polyglot-Regel (E46) |
| E49 | Fehler in der API | Sechs Fehlerarten (`InvalidArgument`, `InvalidFen`, `InvalidUci`, `IllegalMove`, `InvalidState`, `DataNotFound`) mit gemeinsamer Basis `ChessError`, als Ausnahme der Sprache mit üblicher Endung; eine Ausnahme aus einem Callback wird protokolliert und beendet den Prozess | Wertung `crash`; das SDK prüft den Rückgabewert von `choose_move` nicht, der Referee entscheidet; `NULL_MOVE` als Rückgabe scheitert an `Move.uci` |
| E50 | Form der C-Schnittstelle | Die Header unter `sdk/core/include/sbm/` sind maßgeblich, die Bedeutung jeder Funktion steht in `spec/api/`; Regeln in [kern-c-schnittstelle.md](komponenten/kern-c-schnittstelle.md). Präfix `sbm_`, Wahrheitswerte als `int32_t`, Bitoperationen von `Move` im Binding | Header C11-kompatibel, CI übersetzt sie als C11 und C++20; keine zweite Beschreibung der Signaturen |
| E51 | Speicher an der C-Grenze | Der Aufrufer stellt Puffer mit festen Obergrenzen; der Kern reserviert nur beim Anlegen eines Bretts und beim Wachsen des Zugverlaufs und gibt nie Speicher an den Aufrufer | Keine Freigabefunktionen außer `sbm_board_free`; nur `move_history` braucht eine Längenabfrage |
| E52 | Fehler an der C-Grenze | Jede Funktion liefert nur einen Statuscode (sechs API-Fehler plus Puffer zu klein, Speichermangel, interner Fehler); `sbm_status_name` liefert einen festen Namen; C++-Ausnahmen verlassen den Kern nie | Kein Fehlerzustand im Kern, keine Fehlertexte; das Binding baut die Meldung der Ausnahme |
| E53 | SAN und Material je Farbe | `board.san(move)` und `board.has_insufficient_material(color)` gehören zur öffentlichen API | Referee (Wertung bei Zeitablauf, E44) und Arena (PGN) nutzen dieselben Funktionen wie die Bots; Materialregel wie python-chess |

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
| A13 | Runner und Verifier laufen als Container im Compose-Stack mit erweiterten Rechten, damit nsjail darin Namespaces und cgroups anlegen kann (folgt aus E28) | Eigene Dienste direkt auf dem Host |
| A14 | Feste Schutzgrenzen der Sandbox (Speicher, Prozesse, Ausgabemenge) sind großzügig, für alle Sprachen gleich und stehen in der Sandbox-Konfiguration, nicht in der Website | – |

## 3. Offene Punkte

| ID | Frage | Relevant ab |
|----|-------|-------------|
| O17 | Ausgestaltung der Ressourcenlimits (E23); vorerst ignoriert, kommt eventuell nie | – |
| O18 | Genauer Subdomain-Name, SSH-Zugangsdaten und Zielpfad auf dem Server | M2, werden als GitHub-Secrets bzw. Proxy-Eintrag gesetzt, nicht im Repo |

## 4. Risiken

| ID | Risiko | Einordnung |
|----|--------|-----------|
| R2 | Verhalten weicht zwischen Sprachen ab | Durch E3 stark reduziert: Regeln liegen nur im Kern. Verbleibend: Fehler in den Bindings → Binding-Tests je Sprache |
| R3 | Statische Analyse ist umgehbar | Bleibt als zweite Schicht Pflicht, darf aber nie die einzige sein |
| R4 | Runner/Verifier laufen als Container mit erweiterten Rechten; ein Fehler dort wirkt wie Root auf dem Host | Nicht im Netz `local-web`, nicht von außen erreichbar, Aufträge nur über die DB |
| R11 | Build auf dem schwachen Server (C++-Kern, Frontend, fünf Laufzeiten) dauert und belastet andere Dienste | Queue beim Deploy pausieren; Ausweichmöglichkeit: Images in GitHub Actions vorbauen |
| R5 | Rechenbedarf langer Partien auf schwacher Hardware | Alles konfigurierbar (E13), Queue nutzt die Zeit lückenlos (E20), Laufzeitschätzung in der Admin-UI |
| R6 | Wanduhrzeit auf geteiltem Server: Fremdlast kostet den Bot am Zug Bedenkzeit | Akzeptiert (E12, E19); gedämpft durch festen Kern und CPU-Priorität |
| R7 | Übergang über die Sprachgrenze kostet pro Aufruf Zeit | Grobkörnige API (ganze Zuglisten, Massenabfragen), siehe [sdk-api.md](komponenten/sdk-api.md) |
| R8 | Vorkompilierte SDK-Pakete müssen für jede Plattform der Entwickler gebaut werden | Build-Matrix in CI (Windows, Linux, macOS) |
| R9 | Debugger der Bot-Sprache kann nicht in den Kern steppen | Kern liefert aussagekräftige Fehler; Brettzustand jederzeit als FEN/Text ausgebbar |
| R10 | Gäste können Spiele gegen Bots starten (E11) und damit die Queue belasten | Eigene Kapazitätsgrenze, niedrigste Priorität |
