# Lokale Entwicklung und Debugging

Ziel: Ein Bot lässt sich ohne Server entwickeln, im Debugger schrittweise ausführen und unverändert hochladen.

## Betriebsarten

| Modus | Gegner | Schiedsrichter | Zweck |
|-------|--------|----------------|-------|
| Lokale Arena | Zweiter lokaler Bot (beliebige Sprache), mitgelieferte Referenzbots oder Mensch auf der Konsole | Arena auf dem eigenen Gerät | Entwickeln, Debuggen, Testreihen |
| Remote | Auf dem Server laufender Bot | Server | Test gegen echte Gegner vor dem Upload |
| Server | – | Server | Regulärer Betrieb nach Upload |

Der Bot-Code ist in allen drei Modi identisch; nur der Transport des SDK wechselt (siehe [bot-protokoll.md](bot-protokoll.md)).

## Lokale Arena (`tools/arena`)

- Eigenständiges CLI-Programm, enthält denselben Referee-Kern wie der Server (gemeinsames Paket, kein Nachbau).
- Startet Bots als Kindprozesse über `stdio` **oder** wartet auf Bots, die sich per `tcp` verbinden.
- Keine Sandbox, keine Container – läuft direkt auf dem Entwicklergerät.
- Optionen: Zeitkontrolle, Start-FEN, Anzahl Partien mit Farbwechsel, Ausgabe als PGN, Uhr abschaltbar.
- Mitgeliefert: Referenzbots (Zufall, einfacher Materialzähler) als Gegner und als Vorlage je Sprache.

## Debugging

| Thema | Lösung |
|-------|--------|
| Bot aus der IDE starten | Bot verbindet sich per `tcp` mit der wartenden Arena; dadurch normales Starten/Debuggen als Hauptprogramm |
| Haltepunkte vs. Uhr | Arena-Option „Uhr aus“ bzw. „Uhr pausiert, solange Debug-Modus“; sonst verliert der Bot beim ersten Haltepunkt auf Zeit |
| Reproduzierbarkeit | Start aus beliebiger FEN; Wiedergabe einer gespeicherten Partie bis Zug N, danach übernimmt der Bot |
| Ausgaben | Log-Bibliothek des SDK mit Stufen (siehe [sdk-api.md](sdk-api.md)); Stufe per Flag/Umgebungsvariable |
| Server-Fehler nachstellen | Partie vom Server als PGN/JSON herunterladen und lokal bis zur Fehlstellung abspielen |
| Limits lokal prüfen | Optionaler Modus, der den Bot im selben Run-Image wie der Server startet (erfordert Docker lokal) |
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

## Auslieferung der SDKs

| Sprache | Naheliegender Kanal |
|---------|--------------------|
| Python | Paket (pip) |
| JavaScript | Paket (npm) |
| Java | JAR / Maven-Artefakt |
| C# | NuGet-Paket |
| C++ | Header + Quellen, CMake-Einbindung |

Alternativ für alle: Download als Archiv von der Website inklusive Vorlagenprojekt und Arena. Jede Sprache bekommt ein lauffähiges Beispielprojekt mit Debug-Konfiguration.
