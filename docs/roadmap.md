# Roadmap

Stand: Revision 4 (gemeinsamer C++-Kern, nsjail im Container, Spiel-Queue; Ressourcenlimits zurückgestellt)

## Prioritätsstufen

| Stufe | Bedeutung |
|-------|-----------|
| P0 | Kernfunktion: ohne das gibt es kein Spiel zwischen zwei Bots, das gespeichert und angesehen werden kann |
| P1 | Nötig für den Betrieb mit fremden Bots (Sicherheit, Upload, Wettbewerbe) |
| P2 | Ausbau der geforderten Funktionen (weitere Sprachen, Turniere, Mensch/Remote) |
| P3 | Härtung und Komfort |

## Abhängigkeiten

```mermaid
flowchart TD
  M0[M0 Spezifikation] --> M1[M1 Kern + Python lokal]
  M1 --> M2[M2 Persistenz + Queue + Viewer]
  M1 --> M3[M3 Sandbox + Upload]
  M2 --> M3
  M3 --> M4[M4 Ligen + Saisons]
  M1 --> M5[M5 Weitere Sprachen]
  M3 --> M5
  M4 --> M6[M6 Turniere + Admin]
  M3 --> M7[M7 Mensch + Remote]
  M2 --> M7
  M4 --> M8[M8 Härtung]
  M5 --> M8
```

Reihenfolge (E110): M4 und M7 laufen parallel, M6 folgt nach M7. M5 ist zurückgestellt; wie M8 ohne M5 geschnitten wird, ist offen (O22).

## Meilensteine

### M0 – Spezifikation und Gerüst (P0)

| Inhalt | Ergebnis |
|--------|----------|
| Monorepo-Struktur, Coding-Standards, CI-Grundgerüst | Leere Pipelines laufen grün |
| Protokoll-Schema (`spec/protocol`) | Versioniertes JSON-Schema + Beispielnachrichten |
| Kanonische Bot-API (`spec/api`) inklusive Rohzugriff | Sprachneutrale Definition; Feldnummerierung, Zug- und Figurenkodierung festgelegt |
| C-Schnittstelle des Kerns | Funktionsliste, Fehlercodes, Regeln für Handles |
| Testvektoren (`spec/testvectors`) | Perft, Regeln, FEN/UCI, API-Erwartungswerte |

Abnahme: Spezifikationen sind vollständig genug, dass Kern und ein Binding ohne Rückfragen implementierbar sind.

### M1 – Schachkern und Python lokal (P0)

| Inhalt | Ergebnis |
|--------|----------|
| C++-Kern mit C-Schnittstelle | Besteht alle Perft- und Regelvektoren |
| Python-Binding: `Board` (hohe Ebene + Rohzugriff), `Bot`-Callback, `Clock`, Log-Bibliothek, `stdio`/`tcp`-Transport | Besteht die API-Vektoren |
| Vorkompilierte Wheels über CI (Windows, Linux, macOS) | `pip install` genügt als Setup |
| Referee-Kern (Uhr in Wanduhrzeit, Zugprüfung, Endbedingungen) auf demselben C++-Kern | Wiederverwendbares Paket |
| Lokale Arena (CLI, im Python-Paket) | Zwei lokale Bots spielen eine vollständige Partie, PGN-Ausgabe |
| Referenzbots (Zufall, Material) | Gegner und Vorlagen |
| Debug-Workflow | Bot aus der IDE mit Haltepunkten, Uhr abschaltbar |

Abnahme: Auf einem frischen Rechner reichen `pip install` und ein Skript, um zwei Python-Bots regelkonform gegeneinander spielen zu lassen, inklusive Zeitüberschreitung, illegalem Zug und Absturz als Endgründe.

### M2 – Persistenz, Queue, API, Viewer (P0)

| Inhalt | Ergebnis |
|--------|----------|
| MongoDB-Schema für `matches`, `bots`, `jobs`, `settings` | Indizes, Migrationsmechanik |
| Runner als Dienst mit Spiel-Queue (noch ohne Sandbox, nur die Referenzbots, E72) | Spiele laufen lückenlos nacheinander und werden gespeichert |
| Flask-API: Partien, Bots, Queue lesen (öffentlich) | OpenAPI-Vertrag unter `spec/web/` (E73) |
| React-SPA: Grundgerüst, Partie-Viewer mit Geschwindigkeiten, Queue-Ansicht mit geschätzten Startzeiten | Gespeicherte Partien ansehbar |
| Deployment: Compose-Stack, SSH-Deploy aus GitHub Actions, Anbindung an Nginx Proxy Manager über `local-web` | Stack kommt per GitHub Actions auf den Server und ist unter der Subdomain erreichbar |
| Zweisprachigkeit (Deutsch/Englisch) im SPA-Grundgerüst | Übersetzungsdateien von Beginn an |

Abnahme: Mehrere in die Queue gestellte Partien laufen direkt hintereinander, liegen in der DB und sind im Browser ohne Login vollständig abspielbar; der Stack läuft auf dem Server unter der Subdomain. Die Partien stellen in M2 Tests und Entwicklungswerkzeuge ein; dass der Admin sie auf dem Server über die Website einstellt, gehört zur Abnahme von M3 (E71).

### M3 – Sandbox, Verifikation, Upload, Auth (P1)

| Inhalt | Ergebnis |
|--------|----------|
| `runner`-Container mit erweiterten Rechten (führt auch die Verifikation aus, E81), nsjail-Konfiguration und Laufzeitverzeichnis Python, feste Schutzgrenzen, Einfrieren über cgroup | Bot läuft isoliert |
| Statischer Analyzer Python inklusive Bibliotheks-Whitelist | Regelwerk als Konfiguration |
| Verifikations-Pipeline mit Mindesttests und Report | Statusmodell umgesetzt |
| Auth: Invite, Login, Rollen, Sessions | Coder und Admin |
| Admin-Seite zum Ansetzen von Partien (aus M2, E71) | Partien auf dem Server ohne DB-Zugriff |
| Upload mehrerer Quelldateien und Datendateien bis 1 MB, `load_data` im SDK | Mehrdatei-Bots möglich |
| Upload-UI, „Mein Bereich“, Bot-Versionen/Abstammung, Quellcode nur für Besitzer/Admin | Coder kann Bot hochladen und Status verfolgen |
| Negativ-Suite (Netz, Datei, Fork-Bombe, Speicher, Endlosschleife, übergroße Ausgabe) | In CI |

Reihenfolge in vier Schritten, jeder für sich ausgerollt (E80): (1) Auth und Admin-Seite zum Ansetzen von Partien – umgesetzt (E83–E85); (2) nsjail im Runner und Negativ-Suite – umgesetzt und auf dem Server geprüft (E86–E88); (3) Analyzer, Verifikation und Upload für Python – umgesetzt (E89–E94); (4) „Mein Bereich“, Versionen und Reports – umgesetzt (E95–E98).

Abnahme: Ein eingeladener Nutzer lädt einen Python-Bot hoch; bösartige Testbots werden abgelehnt oder in der Sandbox folgenlos beendet. Der Admin stellt auf dem Server über die Website mehrere Partien ein, die direkt hintereinander laufen und im Browser abspielbar sind (aus M2 verschoben, E71). Abgenommen auf dem Server am 8. Oktober 2026.

### M4 – Ligen und Saisons (P1)

| Inhalt | Ergebnis |
|--------|----------|
| Disziplin-Modell (Zeitkontrollen), über die Website einstellbar | Konfigurierbar |
| Liga-Konfiguration, Saisons, Round-Robin, Tabellen, Tiebreaks, Auf-/Abstieg | Vollständiger Saisonzyklus |
| Queue-Logik: Prioritäten, Wechsel zwischen Wettbewerben, Pausieren, Neuansetzen, Laufzeitschätzung | Mehrere Wettbewerbe teilen sich die Queue |
| Rückzug eines Bots (kampflose Siege, markiert; weniger Absteiger; Nachrücker) | Regel E17 umgesetzt |
| Rating (E103) | Je Bot, über alle Disziplinen |
| UI: Ligen, Tabellen, Spielplan, Bot-Profil mit voller Historie | Einsehbar |
| Live-Kanal für laufende Spiele | Viewer aktualisiert sich |
| Adminbereich Teil 1 (Disziplinen, Ligen, Queue-Steuerung, Bot sperren) | Betrieb ohne DB-Zugriff |

Reihenfolge in fünf Schritten (E99): (1) Disziplinen mit Admin-Seite und Auswahl bei Einzelspielen – umgesetzt (E100); (2) Rating der Bots – umgesetzt (E103, E104); (3) Ligen, Saisons, Anmeldung, Tabellen und Queue-Logik (E101); (4) Liga-Seiten der Website; (5) Live-Kanal (E102).

Abnahme: Zwei aufeinanderfolgende Saisons laufen ohne manuellen Eingriff durch, inklusive Auf-/Abstieg, neu einsteigendem Bot und einem während der Saison zurückgezogenen Bot.

### M5 – Weitere Sprachen (P2)

Zurückgestellt (E110). Mit jeder Sprache kommt auch ihr Transport `remote` für M7 (E111).

Pro Sprache: Binding auf den Kern, Paket mit eingebetteten Binaries, API- und Protokolltests, Laufzeitverzeichnis + seccomp-Whitelist, Analyzer mit Bibliotheks-Whitelist, Vorlagenprojekt, Aufnahme in den Kreuztest. Die Schachregeln selbst müssen nicht erneut implementiert werden.

| Reihenfolge | Sprache | Begründung der Position |
|-------------|---------|-------------------------|
| 1 | C++ | Binding entfällt praktisch (direkter Zugriff auf den Kern); der Analyzer ist der aufwendigste, kann aber früh beginnen |
| 2 | JavaScript | Analyseform ähnlich zu Python (AST); nativer Addon als neue Bindungsart |
| 3 | Java | Bytecode-Analyse gut abgrenzbar; Laufzeit mit größerer seccomp-Whitelist |
| 4 | C# | Ähnlich zu Java |

Die Reihenfolge ist nach Aufwand und Abhängigkeiten sortiert und frei änderbar; die Sprachen sind untereinander unabhängig.

Abnahme je Sprache: Alle API-Vektoren bestanden, Bot der Sprache spielt regulär gegen Bots aller bereits unterstützten Sprachen, Negativ-Suite bestanden, Setup auf frischem Rechner mit einem Paketbefehl.

### M6 – Turniere, voller Adminbereich (P2)

| Inhalt | Ergebnis |
|--------|----------|
| Turnierformate (Round-Robin, Schweizer, K.-o.), Wiederholung, Anmeldung | Konfigurierbar |
| Adminbereich vollständig: jede Einstellung über die Website (E13), Nutzer, Invites, Overrides, Neuprüfung, Audit-Log | Kein Parameter mehr nur in Dateien |
| Einzelspiele (auch Version gegen Version) | Ansetzbar durch Besitzer/Admin |

Nach M7, Turniere erst nach M4 Schritt 3 (E150). Drei Schritte:

1. Adminbereich: Audit-Log-Ansicht, Eingriffe in die Queue (Priorität, Abbruch wartender und laufender Partien, Neuansetzen), Neuprüfung (nur Bericht) und Override abgelehnter Bots, Einstellungen in der Datenbank auf `/admin/settings`.
2. Einzelspiele: fehlende Teile ergänzen.
3. Turniere auf dem gemeinsamen Modell für Wettbewerbe aus M4; Formate offen (O24).

### M7 – Mensch gegen Bot, lokaler Bot gegen Web-API (P2)

| Inhalt | Ergebnis |
|--------|----------|
| `HumanPlayer`-Adapter, Spiel-UI für Gäste ohne Account | Partie im Browser gegen gewählten Bot |
| Rolle `player` (nur spielen), Rating angemeldeter Konten (E103) | Menschen in der Wertung, auf der Kontoseite (E117) und in der Rangliste mit Filter (E118) |
| `RemoteBotPlayer`-Adapter, `remote`-Transport in den Bindings, API-Tokens | Lokaler Bot spielt gegen Server-Bot |
| Kapazitäts- und Missbrauchsgrenzen (pro IP, gesamt), einstellbar | Schutz der Queue |

Vor M6 und parallel zu M4 (E110). Drei Schritte (E111):

1. Gemeinsame Basis – umgesetzt: Gateway für WebSockets (E112), Play-Runner als eigener Container, Jobs der Art `play`, Sitze und Abbruchregeln (E113), Protokolle gateway-v1 und relay-v1 ([gateway.md](komponenten/gateway.md)).
2. Mensch gegen Bot – umgesetzt: Browser-Protokoll play-v1, `HumanPlayer`, Seiten `/play` und `/play/:id`, Gäste gegen jeden geprüften Bot (E114), Grenzen je Adresse, Konto und Token auf `/admin/play`, Rolle `player` (E115). Interaktive Partien sind öffentlich, in `/matches` filterbar und laufend in der Queue (E119, vorher nicht öffentlich). Gewertet werden Partien angemeldeter Konten unter einer Disziplin (E117); das Rating steht auf der Kontoseite und in der Rangliste, filterbar nach Bots und Spielern (E118).
3. Remote-Bot – umgesetzt: API-Tokens für Coder, `POST /remote/matches`, Transport `remote` im Python-SDK (E116); die übrigen Sprachen folgen mit M5.

Danach: `sbm.play` startet Partien per Code, lokal oder gegen einen Bot auf dem Server; Version 0.2.0 des SDK (E120).

Abnahme: Ein Gast spielt im Browser eine vollständige Partie gegen einen hochgeladenen Bot; ein lokaler Python-Bot spielt mit Token gegen einen Bot auf dem Server; Abbrüche (Verbindung weg, Sitz nicht eingenommen, Runner gestoppt) enden als `aborted`, ohne die Queue zu verzögern. Zusätzlich geprüft: `start.py` der Vorlage lokal und `sbm.play` mit zwei Partien gegen den Server. Abgenommen auf dem Server am 10. Oktober 2026.

### M8 – Härtung und Betrieb (P3)

| Inhalt |
|--------|
| Monitoring, Alarme, Backup-/Restore-Probe |
| Messung der Zeitgenauigkeit unter Fremdlast, Feinabstimmung von CPU-Gewichtung und Toleranz |
| Tabellen-Neuberechnung und Reparaturwerkzeuge |
| Vollständige Autoren-Doku je Sprache, API-Referenz aus `spec/api` generiert |
| Datenschutz-/Löschfunktionen für Accounts |

### Zurückgestellt (ohne Meilenstein)

| Inhalt |
|--------|
| Konfigurierbare Ressourcenlimits und ressourcenlimitierte Disziplinen (E23, O17) |

## Querschnitt (ab M0 durchgehend)

- CI als Merge-Gate; Kernvektoren und Binding-Tests
- Entscheidungen in [00_entscheidungen.md](00_entscheidungen.md) nachführen
- Protokoll- und SDK-Versionierung von Beginn an

## Kritischer Pfad zur Kernfunktion

`M0 → M1 → M2` liefert „zwei Bots spielen, Partie ist gespeichert und ansehbar“. `M3 → M4` macht daraus einen Betrieb mit fremden Bots und automatischen Ligen. Alles Weitere erweitert Breite (Sprachen, Formate, Spielarten), nicht den Kern.
