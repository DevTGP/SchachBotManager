# SchachBotManager

Website, auf der Schachbots (Python, C++, Java, C#, JavaScript) in Ligen, Turnieren und Einzelspielen gegeneinander antreten. Partien werden gespeichert und sind öffentlich ansehbar. Eingeladene Nutzer laden Bots hoch; diese werden geprüft und laufen isoliert auf dem Server.

## Stand

**M0** laut `docs/roadmap.md` läuft. Erledigt: Festlegungen E34–E53, Repo-Gerüst, CI mit `tools/spec-check`, Protokoll-Schema v1 (`spec/protocol/v1/`), kanonische Bot-API (`spec/api/`), C-Schnittstelle des Kerns (`sdk/core/include/sbm/`). Offen: Testvektoren. Danach M1 (C++-Kern, Python-Binding, lokale Arena).

## Zuerst lesen

| Datei | Wofür |
|-------|-------|
| `docs/00_entscheidungen.md` | Alle Entscheidungen (E…), Annahmen (A…), offene Punkte (O…), Risiken (R…). Maßgeblich bei Widersprüchen |
| `docs/roadmap.md` | Meilensteine, Reihenfolge, Abnahmekriterien |
| `docs/architektur/systemuebersicht.md` | Komponenten, Vertrauensgrenzen, Repo-Struktur |
| `docs/architektur/ablaeufe.md` | Zusammenspiel der Komponenten |
| `docs/komponenten/*.md` | Eine Datei je Komponente; vor Arbeit an einer Komponente die passende Datei lesen |

`docs/_archiv/` enthält überholte Stände und ist nicht maßgeblich.

## Kernentscheidungen in Kurzform

- **Stack:** Flask als reine API, React + TypeScript + Vite als SPA, MongoDB, Deployment über GitHub Actions.
- **Schachregeln:** Ein gemeinsamer C++-Kern mit flacher C-Schnittstelle. Referee, Arena und alle fünf SDKs nutzen ihn; die SDKs sind dünne Bindings. Keine zweite Regelimplementierung anlegen.
- **Bot-API:** Callback-Modell (`choose_move(board, clock)`), hohe Ebene plus Rohzugriff aufs Brett, gleiche Wörter in idiomatischer Schreibweise je Sprache. Jeder Bot hat sein eigenes Brett im eigenen Prozess.
- **Bot ↔ Server:** Zeilenweises JSON über stdin/stdout. Bots sprechen nie direkt miteinander. Der Referee ist allein maßgeblich für Legalität, Zeit und Ergebnis.
- **Zeit:** Wanduhrzeit. Außerhalb des eigenen Zuges ist der Bot-Prozess eingefroren.
- **Fairness:** Keine Sprachfaktoren; alle Sprachen haben identische Bedingungen.
- **Sicherheit:** nsjail als Sandbox plus statische Analyse je Sprache. Die Sandbox muss allein ausreichen; die Analyse ist die zweite Schicht.
- **Bots:** Upload als Quellcode (mehrere Dateien, Datendateien bis 1 MB über `load_data`). Neue Version = neuer Bot. Quellcode nur für Besitzer und Admin sichtbar.
- **Wettbewerbe:** Ligen mit Saisons, Tabellen, Auf-/Abstieg; Turniere; eine gemeinsame Spiel-Queue ohne feste Startzeiten. Alles über die Website konfigurierbar, Konfiguration in der DB.
- **Zugang:** Lesen und Spielen gegen Bots ohne Account; Upload nur für eingeladene Nutzer.
- **Oberfläche:** Deutsch und Englisch, Texte von Beginn an in Übersetzungsdateien.
- **Zurückgestellt:** Konfigurierbare Ressourcenlimits (Speicher, CPU, Dateigröße). Nicht einbauen.

## Betrieb

- Server: Ubuntu x86-64, nicht dediziert, schwach. Standard ist ein Spiel gleichzeitig.
- Ein Docker-Compose-Stack. Nur der `frontend`-Container hängt am externen Netz `local-web`; der vorhandene Nginx Proxy Manager zeigt darauf. Der Stack veröffentlicht keine Ports.
- Adresse: `schachbotmanager.devtgp.net` (als Konfigurationswert, nicht fest im Code).
- Deploy: GitHub Actions per SSH, Stack setzen, Container bauen auf dem Server.
- `runner` und `verifier` laufen als Container mit erweiterten Rechten (für nsjail) und hängen nicht am Proxy-Netz.

## Regeln für die Arbeit im Repo

- **Öffentliches Repo:** Keine Secrets, SSH-Zugangsdaten oder Serverpfade einchecken. Dafür GitHub-Secrets bzw. Umgebungsdateien auf dem Server; im Repo nur eine Beispiel-Umgebungsdatei.
- **Kleine, thematisch getrennte Dateien:** Eine Datei, eine Verantwortung. Keine Sammeldateien. Struktur laut `docs/architektur/systemuebersicht.md`.
- **Tests vor Abschluss:** Jede Änderung mit Tests, Linting und Diff-Durchsicht abschließen. Der Kern muss die Vektoren unter `spec/testvectors/` bestehen, jedes Binding die API-Vektoren.
- **Spezifikation zuerst:** Protokoll und Bot-API werden unter `spec/` definiert und sind die Quelle für Referee, SDKs und Doku. Änderungen dort zuerst, dann im Code.
- **Bot-Code ist nicht vertrauenswürdig**, auch beim Kompilieren. Er läuft ausschließlich in der Sandbox. Die Web-API startet nie Prozesse.
- **Entscheidungen nachführen:** Neue oder geänderte Entscheidungen in `docs/00_entscheidungen.md` eintragen und die betroffene Komponenten-Datei anpassen.
- **Rückfragen:** Bei Konzept- und Designentscheidungen nachfragen statt annehmen. Triviale Details pragmatisch entscheiden und kurz benennen.
- **Doku-Sprache:** Deutsch. Code, Bezeichner und Commit-Nachrichten auf Englisch.

## Befehle

Build-, Test- und Lint-Befehle hier eintragen, sobald sie entstehen.

| Zweck | Befehl (aus dem Repo-Wurzelverzeichnis) |
|-------|------------------------------------------|
| Werkzeuge einrichten | `python -m venv .venv` und dann `.venv/Scripts/pip install -e "tools/spec-check[dev]"` (Linux: `.venv/bin/`) |
| Spezifikation prüfen | `spec-check spec` |
| Tests spec-check | `pytest tools/spec-check` |
| Lint/Format spec-check | `ruff check tools/spec-check` und `ruff format --check tools/spec-check` |
| Header des Kerns prüfen | `gcc -std=c11 -Wall -Wextra -Wpedantic -Werror -fsyntax-only -Isdk/core/include sdk/core/tests/header_check.c`, ebenso `g++ -std=c++20 … header_check.cpp` |

CI: `.github/workflows/ci.yml` (Job `spec` für spec-check, Job `core-headers` für die Header).

## Offen (erst für M2 nötig)

SSH-Zugangsdaten, Zielpfad auf dem Server, Anwendungs-Secrets.
