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

- Befehl `sbm-arena` aus dem Python-Paket (`sbm.arena`, auch `python -m sbm.arena`); nutzt denselben Referee-Kern `sbm.referee` wie der Server (E65, kein Nachbau). Bedienung und Verhalten: E67.
- Keine Sandbox, keine Container – läuft direkt auf dem Entwicklergerät.
- Mitgeliefert: Referenzbots `random` (Zufall) und `material` (Materialzähler mit Suchtiefe 2) als Gegner und als Vorlage (E68); für Python unter `sbm.bots`, für die übrigen Sprachen mit deren SDKs. Ein menschlicher Spieler auf der Konsole kommt später.

```
sbm-arena mein_bot.py gegner.py --games 10 --time 10+0.1 --pgn partien.pgn
sbm-arena tcp gegner.py --no-clock          # mein Bot startet in der IDE mit --tcp 7470
sbm-arena mein_bot.py material --games 20 --time 5+0.05
sbm-arena "java -jar bot.jar" mein_bot.py --fen "8/8/8/4k3/8/8/4P3/4K3 w - - 0 1" --moves
sbm-arena tcp material --no-clock --replay partien.pgn --replay-game 3 --replay-ply 41
```

| Bot-Angabe | Bedeutung |
|------------|-----------|
| `bot.py` | Läuft mit dem Python, in dem die Arena läuft |
| andere Datei, z. B. `engine.exe` | Wird direkt gestartet |
| Befehlszeile, z. B. `"java -jar bot.jar"` | Wird so gestartet; Name nach der Datei im Befehl (`bot`) |
| `tcp`, `tcp:PORT` | Arena wartet auf 127.0.0.1 (Standard 7470), bis sich der Bot verbindet; je Partie eine neue Verbindung |
| `random`, `material` | Referenzbot aus `sbm.bots` (E68); eine Datei dieses Namens als `./random` angeben |

| Option | Wirkung |
|--------|---------|
| `--games N` | N Partien, Farben wechseln; am Ende eine Tabelle mit Punkten |
| `--time S+I` | Bedenkzeit in Sekunden plus Inkrement je Zug, Standard `60+1` |
| `--no-clock` | Keine Zeitgrenzen, für Haltepunkte |
| `--fen FEN` | Startstellung |
| `--replay PGN` | Startstellung aus einer aufgezeichneten Partie (E69); nicht zusammen mit `--fen` |
| `--replay-game N`, `--replay-ply N` | Partie in der Datei (Standard 1) und nachgespielte Halbzüge (Standard alle) |
| `--pgn DATEI` | Partien an die Datei anhängen |
| `--moves` | Jeden Zug mit Zeit und `info` ausgeben |
| `--quiet` | Logausgaben der Bots verbergen (sonst auf stderr mit `[Name]` davor) |
| `--startup-ms`, `--tolerance-ms`, `--max-moves` | Startbudget, Toleranz je Zug, Remis nach so vielen ganzen Zügen |

- **Einfrieren:** Lokal gestartete Bots werden wie auf dem Server außerhalb des eigenen Zuges angehalten, samt aller Kindprozesse. Gelingt das nicht, warnt die Arena und der Bot läuft weiter. TCP-Bots werden nie eingefroren.
- **Ende:** Nach der Partie hat ein Bot 2 s, um sich selbst zu beenden; danach beendet die Arena ihn und alle Prozesse, die er gestartet hat.
- **Exit-Codes:** 0 fertig, 1 Fehler der Arena (z. B. Port belegt), 2 falsche Argumente, 130 abgebrochen.

## Debugging

| Thema | Lösung |
|-------|--------|
| Bot aus der IDE starten | Bot verbindet sich per `tcp` mit der wartenden Arena (`--tcp` oder `SBM_TRANSPORT=tcp`, Port 7470, E61); dadurch normales Starten/Debuggen als Hauptprogramm |
| Haltepunkte vs. Uhr | Arena-Option `--no-clock` (E67); sonst verliert der Bot beim ersten Haltepunkt auf Zeit |
| Reproduzierbarkeit | Start aus beliebiger FEN (`--fen`) oder aus einer PGN-Partie nach N Halbzügen (`--replay`, E69); die Bots erhalten nur die Stellung, Wiederholungen davor zählen nicht |
| Ausgaben | Log-Bibliothek des SDK mit Stufen (siehe [sdk-api.md](sdk-api.md)); Stufe per `--log-level`/`SBM_LOG_LEVEL`, Logdatei per `--log-file`/`SBM_LOG_FILE` (E61); `print` landet auf stderr, stdout gehört dem Protokoll |
| Datendateien | Lokal im Ordner `data/` neben dem Bot-Skript; `load_data(name)` liest sie dort wie auf dem Server (E62) |
| Server-Fehler nachstellen | Partie vom Server als PGN herunterladen und mit `--replay` bis zur Fehlstellung abspielen; der Download kommt mit dem Partie-Viewer (M2) |
| IDE-Einrichtung | Vorlagenprojekt je Sprache unter `templates/` mit fertiger Debug-Konfiguration (E69), siehe unten |
| Limits lokal prüfen | Optionaler Modus, der den Bot mit derselben Sandbox-Konfiguration wie der Server startet (nur unter Linux) |
| Regeln lokal prüfen | Statischer Analyzer als CLI, identisch zur Serverprüfung (siehe [statische-analyse.md](statische-analyse.md)) |

### Schritt für Schritt (Python, VS Code)

Ausgangspunkt ist die Vorlage `templates/python/` (E69); ihr README beschreibt die Einrichtung.

1. Ordner kopieren, in VS Code öffnen, das Python mit installiertem SDK als Interpreter wählen.
2. Haltepunkt in `choose_move` setzen und z. B. „Bot debuggen: Weiß gegen material“ starten.
3. VS Code startet als Hintergrundaufgabe `python -m sbm.arena tcp material --no-clock --moves`; sobald die Arena „waiting for … to connect“ meldet, startet `bot.py --tcp` im Debugger und verbindet sich.
4. Fehler aus einer Testreihe: Aufgabe „Arena: 10 Partien gegen material“ schreibt `games.pgn`; „Bot debuggen: Stellung aus games.pgn, …“ fragt nach Partie und Halbzügen und startet genau dort.

Ohne VS Code gilt dieselbe Reihenfolge: erst die Arena mit `tcp` im Terminal, dann den Bot mit `--tcp` im Debugger der eigenen IDE.

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
- **Vorlagenprojekt je Sprache** unter `templates/<sprache>/` mit fertiger Debug-Konfiguration und einem lauffähigen Beispielbot (E69); vorhanden für Python, die übrigen folgen mit ihren SDKs.
