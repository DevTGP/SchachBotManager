# Lokale Entwicklung und Debugging

Ziel: Ein Bot lässt sich ohne Server entwickeln, im Debugger schrittweise ausführen und unverändert hochladen.

## Betriebsarten

| Modus | Gegner | Schiedsrichter | Zweck |
|-------|--------|----------------|-------|
| Lokale Arena | Zweiter lokaler Bot (beliebige Sprache), mitgelieferte Referenzbots oder Mensch auf der Konsole | Arena auf dem eigenen Gerät | Entwickeln, Debuggen, Testreihen |
| Remote | Auf dem Server laufender Bot | Server | Test gegen echte Gegner vor dem Upload |
| Server | – | Server | Regulärer Betrieb nach Upload |

Der Bot-Code ist in allen drei Modi identisch; nur der Transport des SDK wechselt (siehe [bot-protokoll.md](bot-protokoll.md)).

## Lokale Arena (`sbm-arena`)

- Befehl `sbm-arena` aus dem Python-Paket (`sbm.arena`); nutzt denselben Referee-Kern `sbm.referee` wie der Server (E65, kein Nachbau).
- Startet Bots als Kindprozesse über `stdio` **oder** wartet auf Bots, die sich per `tcp` verbinden.
- Keine Sandbox, keine Container – läuft direkt auf dem Entwicklergerät.
- Optionen: Zeitkontrolle, Start-FEN, Anzahl Partien mit Farbwechsel, Ausgabe als PGN, Uhr abschaltbar.
- Mitgeliefert: Referenzbots (Zufall, einfacher Materialzähler) als Gegner und als Vorlage je Sprache.

## Debugging

| Thema | Lösung |
|-------|--------|
| Bot aus der IDE starten | Bot verbindet sich per `tcp` mit der wartenden Arena (`--tcp` oder `SBM_TRANSPORT=tcp`, Port 7470, E61); dadurch normales Starten/Debuggen als Hauptprogramm |
| Haltepunkte vs. Uhr | Arena-Option „Uhr aus“ bzw. „Uhr pausiert, solange Debug-Modus“; sonst verliert der Bot beim ersten Haltepunkt auf Zeit |
| Reproduzierbarkeit | Start aus beliebiger FEN; Wiedergabe einer gespeicherten Partie bis Zug N, danach übernimmt der Bot |
| Ausgaben | Log-Bibliothek des SDK mit Stufen (siehe [sdk-api.md](sdk-api.md)); Stufe per `--log-level`/`SBM_LOG_LEVEL`, Logdatei per `--log-file`/`SBM_LOG_FILE` (E61); `print` landet auf stderr, stdout gehört dem Protokoll |
| Datendateien | Lokal im Ordner `data/` neben dem Bot-Skript; `load_data(name)` liest sie dort wie auf dem Server (E62) |
| Server-Fehler nachstellen | Partie vom Server als PGN/JSON herunterladen und lokal bis zur Fehlstellung abspielen |
| Limits lokal prüfen | Optionaler Modus, der den Bot mit derselben Sandbox-Konfiguration wie der Server startet (nur unter Linux) |
| Regeln lokal prüfen | Statischer Analyzer als CLI, identisch zur Serverprüfung (siehe [statische-analyse.md](statische-analyse.md)) |

## Lokaler Bot gegen die Web-API

1. Nutzer erzeugt im Web ein API-Token.
2. Start des Bots mit Transport `remote`, Token, gewünschtem Gegner-Bot und Disziplin.
3. Das SDK öffnet eine WebSocket-Verbindung; der Server legt ein ungewertetes Spiel an (A9) und startet den Gegner in der Sandbox.
4. Nachrichten sind dieselben wie im `stdio`-Protokoll.

Zu beachten:

- **Zeitmessung** enthält Netzwerklatenz; die Uhr läuft auf dem Server. Optionen: Latenzausgleich pro Zug oder großzügigere Zeitkontrolle für Remote-Spiele.
- **Kein Einfrieren möglich:** Ein lokaler Bot kann in gegnerischer Zeit rechnen und unterliegt keinen Ressourcenlimits. Remote-Spiele sind daher nicht mit Liga-Ergebnissen vergleichbar und bleiben ungewertet.
- **Missbrauchsschutz:** Begrenzung gleichzeitiger und täglicher Remote-Spiele pro Token, Leerlauf-Timeout, niedrige Priorität.
- **Verbindungsabbruch:** Frist zur Wiederverbindung, danach Abbruch ohne Wertung.

## Setup je Sprache

Der gemeinsame Kern (E3) wird nie vom Bot-Autor kompiliert. Jedes SDK-Paket enthält den Kern fertig gebaut für Windows, Linux und macOS.

| Sprache | Einrichtung | Bot starten |
|---------|-------------|-------------|
| Python | `pip install schachbotmanager` | `python mein_bot.py` |
| JavaScript | `npm install <sdk>` | `node mein_bot.js` |
| Java | Eine Abhängigkeit (Maven/Gradle) oder ein JAR im Klassenpfad | Normale `main`-Klasse |
| C# | `dotnet add package <sdk>` | `dotnet run` |
| C++ | Archiv entpacken, per CMake einbinden; Compiler nötig | Kompilieren, ausführen |

Für Python bedeutet das: ein Skript, ein `pip install`, kein Compiler, keine Build-Konfiguration. Die Arena kommt im selben Python-Paket als Kommandozeilenbefehl mit, sodass auch der lokale Gegner ohne weiteres Setup startet.

Zu beachten:

- **Plattformabdeckung (R8):** Für eine Plattform ohne vorkompiliertes Paket müsste lokal gebaut werden. Die CI-Matrix deckt Windows x64, Linux x64/arm64 und macOS x64/arm64 ab (Python: E64); Alpine (musl) und 32-Bit-Systeme bauen lokal.
- **Python-Versionen:** Python 3.11 und neuer, ein Wheel je Version (E59); Import als `import sbm`.
- **Kein Schritt in den Kern (R9):** Der Python-Debugger hält im eigenen Code und im Python-Teil des SDK, nicht in der Zuggenerierung.
- **Vorlagenprojekt je Sprache** mit fertiger Debug-Konfiguration und einem lauffähigen Beispielbot.
