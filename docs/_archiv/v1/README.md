# SchachBotManager – Konzeptdokumentation

Stand: 2026-10-05 · Status: Konzept, vor Implementierungsbeginn

## Lesereihenfolge

| # | Datei | Inhalt |
|---|-------|--------|
| 1 | [00_entscheidungen.md](00_entscheidungen.md) | Getroffene Entscheidungen, Annahmen, offene Punkte |
| 2 | [architektur/systemuebersicht.md](architektur/systemuebersicht.md) | Komponenten, Vertrauensgrenzen, Repo-Struktur |
| 3 | [architektur/ablaeufe.md](architektur/ablaeufe.md) | Zusammenspiel der Komponenten (Upload, Match, Saison, Live) |
| 4 | [roadmap.md](roadmap.md) | Meilensteine, Prioritäten, Reihenfolge |

## Komponenten

| Datei | Inhalt |
|-------|--------|
| [komponenten/bot-protokoll.md](komponenten/bot-protokoll.md) | Sprachunabhängiges Protokoll Referee ↔ Bot |
| [komponenten/sdk-api.md](komponenten/sdk-api.md) | Bot-API in 5 Sprachen, Debug-Bibliothek, Konformität |
| [komponenten/match-runner.md](komponenten/match-runner.md) | Referee, Uhren, Einfrieren, Spielende-Regeln |
| [komponenten/sandbox.md](komponenten/sandbox.md) | Container-Isolation, Ressourcenlimits |
| [komponenten/statische-analyse.md](komponenten/statische-analyse.md) | Code-Regeln pro Sprache |
| [komponenten/verifikation.md](komponenten/verifikation.md) | Upload-Pipeline, Mindestanforderungen |
| [komponenten/ligen-turniere.md](komponenten/ligen-turniere.md) | Disziplinen, Saisons, Auf-/Abstieg, Turnierformate, Scheduler |
| [komponenten/datenmodell.md](komponenten/datenmodell.md) | MongoDB-Collections und Indizes |
| [komponenten/backend-api.md](komponenten/backend-api.md) | Flask-API, Auth, Rollen, Live-Kanal |
| [komponenten/frontend.md](komponenten/frontend.md) | SPA: Viewer, Tabellen, Admin, Mensch-gegen-Bot |
| [komponenten/lokale-entwicklung.md](komponenten/lokale-entwicklung.md) | Lokale Arena, Debugging, lokaler Bot gegen Web-API |
| [komponenten/deployment.md](komponenten/deployment.md) | GitHub Actions, Docker Compose, Betrieb |
