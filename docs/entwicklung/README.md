# Entwicklerdokumentation

Wie der Code aufgebaut ist, wie man ihn einrichtet, ändert und prüft. Das *Was* und *Warum* steht in den Entscheidungen ([`00_entscheidungen.md`](../00_entscheidungen.md)), der Architektur ([`architektur/`](../architektur/)) und den Komponenten-Dateien ([`komponenten/`](../komponenten/)); dieser Ordner beschreibt das *Wie* im Code. Bei Widersprüchen gelten die Entscheidungen.

## Einstieg

| Datei | Inhalt |
|-------|--------|
| [einrichtung.md](einrichtung.md) | Voraussetzungen, Einrichtung Schritt für Schritt, Stack lokal mit und ohne Docker, häufige Probleme |
| [aenderungen.md](aenderungen.md) | Rezepte für Änderungen über mehrere Pakete: neue Funktion durch alle Schichten, Protokoll, Einstellung, Job-Art, Nummernkreise, Release, Checkliste |
| [tests-und-ci.md](tests-und-ci.md) | Tests je Paket, Fixtures, Schalter, CI-Jobs und ihre Bereiche, Deploy, Release des SDK |

## Code-Karten

Je Paket eine Karte: Einstieg, Module mit ihrer Aufgabe, Abläufe im Code, Tests und Rezepte unter „Erweitern“.

| Datei | Paket | Ort |
|-------|-------|-----|
| [code-kern.md](code-kern.md) | C++-Kern mit C-Schnittstelle | `sdk/core` |
| [code-python-sdk.md](code-python-sdk.md) | Python-SDK `schachbotmanager` (Binding, Laufzeit, Referee, Arena, Analyse, Remote) | `sdk/python` |
| [code-javascript-sdk.md](code-javascript-sdk.md) | JavaScript-SDK `schachbotmanager` auf npm (Addon, Laufzeit, Vorlage) | `sdk/javascript` |
| [code-viewer.md](code-viewer.md) | Grafischer Viewer `sbm-viewer` | `sdk/viewer` |
| [code-store.md](code-store.md) | Datenbankzugriff, Queue, Ratings, Einstellungen, Migrationen | `services/store` |
| [code-runner.md](code-runner.md) | Runner für Partien, Verifikation und interaktive Partien | `services/runner` |
| [code-gateway.md](code-gateway.md) | WebSocket-Gateway | `services/gateway` |
| [code-backend.md](code-backend.md) | Web-API (Flask) | `backend` |
| [code-frontend.md](code-frontend.md) | SPA (React, TypeScript, Vite) | `frontend` |

## Lesepfade

| Vorhaben | Lesen |
|----------|-------|
| Erstmals im Repo | [systemuebersicht.md](../architektur/systemuebersicht.md), [einrichtung.md](einrichtung.md), dann die Karte des Pakets |
| Neue Seite oder neuer Endpunkt | [aenderungen.md](aenderungen.md#funktion-durch-alle-schichten), [code-store.md](code-store.md), [code-backend.md](code-backend.md), [code-frontend.md](code-frontend.md) |
| Partien, Queue, Verifikation | [ablaeufe.md](../architektur/ablaeufe.md), [code-runner.md](code-runner.md), [match-runner.md](../komponenten/match-runner.md) |
| Sandbox | [sandbox.md](../komponenten/sandbox.md), [code-runner.md](code-runner.md), Negativ-Suite in [tests-und-ci.md](tests-und-ci.md) |
| Schachregeln oder Bot-API | [aenderungen.md](aenderungen.md#protokoll-oder-bot-api-ändern), [code-kern.md](code-kern.md), [code-python-sdk.md](code-python-sdk.md), [code-javascript-sdk.md](code-javascript-sdk.md) |
| Mensch gegen Bot, Remote-Bots | [gateway.md](../komponenten/gateway.md), [code-gateway.md](code-gateway.md), [code-runner.md](code-runner.md) |
| Viewer | [viewer.md](../komponenten/viewer.md), [code-viewer.md](code-viewer.md) |
| CI rot | [tests-und-ci.md](tests-und-ci.md#typische-fehler-in-der-ci) |
| Deploy oder Release | [deployment.md](../komponenten/deployment.md), [tests-und-ci.md](tests-und-ci.md#deploy-deployyml), [aenderungen.md](aenderungen.md#sdk-veröffentlichen) |

## Pflege

Code-Karten ändern sich im selben Commit wie der Code: neues Modul, neue Datei in der Karte; neuer Befehl, neue Zeile in der Tabelle „Befehle“ der [`CLAUDE.md`](../../CLAUDE.md). Die Checkliste steht in [aenderungen.md](aenderungen.md#checkliste-vor-dem-commit).
