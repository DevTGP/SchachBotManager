# Änderungen durchführen

Rezepte für Änderungen, die mehrere Pakete berühren, in der Reihenfolge, in der sie entstehen. Die Schritte innerhalb eines Pakets stehen jeweils unter „Erweitern“ in dessen Code-Karte; hier steht nur, was dazwischen passiert und wer worauf wartet.

## Grundsätze

- **Spezifikation zuerst:** Protokolle (`spec/protocol/`), Bot-API (`spec/api/`), Testvektoren (`spec/testvectors/`) und Web-API (`spec/web/openapi.json`) ändern sich vor dem Code. Der Code folgt ihnen, nicht umgekehrt.
- **Entscheidung zuerst:** Konzept- und Designfragen werden geklärt und als E… in [`00_entscheidungen.md`](../00_entscheidungen.md) eingetragen, bevor Code entsteht. Triviale Details werden pragmatisch entschieden und im Commit oder der Doku kurz benannt.
- **Eine Datei, eine Verantwortung:** Neue Logik bekommt ein eigenes Modul statt einer weiteren Funktion in einer großen Datei; Vorbilder nennen die Code-Karten.
- **Eine Regelimplementierung:** Schachregeln nur im Kern. Referee, Arena, Viewer, SDKs und Dienste rufen ihn auf.
- **Bot-Code ist nicht vertrauenswürdig:** Er läuft nur in der Sandbox, auch beim Prüfen. Die Web-API startet nie Prozesse; Arbeit mit Bot-Code wird ein Job für den Runner.
- **Doku im selben Commit:** Entscheidung, Komponenten-Datei, Code-Karte und gegebenenfalls `CLAUDE.md` (Stand, Befehle) ändern sich mit dem Code.

## Funktion durch alle Schichten

Typisch für eine neue Seite mit eigenen Daten, etwa die Serien (E155) oder das Rating je Disziplin (E163).

| Schritt | Ort | Details |
|---------|-----|---------|
| 1. Entscheidung | `docs/00_entscheidungen.md` | Nummer aus dem Kreis des Meilensteins (siehe [unten](#nummern-für-entscheidungen-und-migrationen)); Thema, Entscheidung, Konsequenz |
| 2. Datenmodell | [datenmodell.md](../komponenten/datenmodell.md) | Neue Collection oder neue Felder beschreiben |
| 3. Vertrag | `spec/web/openapi.json` | Pfade, Schemas, Fehlerantworten; danach `spec-check spec` |
| 4. Store | `services/store` | [Neue Collection oder neues Feld](code-store.md#neue-collection-oder-neues-feld), bei Bedarf [neue Migration](code-store.md#neue-migration) und [Rechte der Mongo-Nutzer](code-store.md#rechte-der-mongo-nutzer-deploymongousersjs) |
| 5. Runner | `services/runner` | Nur wenn Partien, Verifikation oder Ratings betroffen sind ([Code-Karte Runner](code-runner.md#erweitern)) |
| 6. Web-API | `backend` | [Neuer Endpunkt](code-backend.md#neuer-endpunkt); Tests prüfen jede Antwort gegen den Vertrag |
| 7. API-Typen | `frontend/src/api/schema.d.ts` | `npm run api-types` in `frontend/`, Ergebnis einchecken |
| 8. Frontend | `frontend/src` | [Neuer API-Aufruf](code-frontend.md#erweitern), [neue Seite](code-frontend.md#erweitern); Texte in `de.json` **und** `en.json` |
| 9. Doku | `docs/komponenten/*.md`, `docs/entwicklung/code-*.md`, `CLAUDE.md` | Tabellen der Komponenten, neue Module in der Code-Karte, Absatz „Stand“ |
| 10. Prüfen | alle betroffenen Pakete | Siehe [Checkliste](#checkliste-vor-dem-commit) |

Store, API und Frontend lassen sich nacheinander committen, solange jeder Commit für sich grün ist; üblich ist hier ein Commit je Funktion.

## Protokoll oder Bot-API ändern

| Was | Spezifikation | Danach |
|-----|---------------|--------|
| Bot ↔ Referee (v1) | `spec/protocol/v1/` mit Beispielen unter `examples/valid` und `examples/invalid` | Referee `sbm.referee` (strenge Prüfung, E66), Bot-Seite in `sbm/runtime`, Doku [bot-protokoll.md](../komponenten/bot-protokoll.md); alle SDKs müssen folgen |
| Bot-API (`Board`, `Move`, …) | `spec/api/*.json`, dann Vektoren mit `testvector-gen spec` | [Kern](code-kern.md#neue-funktion-der-c-schnittstelle), dann [Binding](code-python-sdk.md#erweitern) und [C#-Binding](code-csharp-sdk.md#erweitern); `test_vectors.py` und `test_api_surface.py` bzw. `VectorTests` und `ApiSurfaceTests` fordern die neue Funktion ein |
| Schachregel | Beschreibung in `spec/api/*.json` bzw. Entscheidung, Fälle im Generator | [Regeländerung im Kern](code-kern.md#regeländerung); alle Vektoren neu erzeugen und mit `--perft all` prüfen |
| Gateway, Relay, Browser | `spec/protocol/gateway-v1/`, `relay-v1/`, `play-v1/` | [Gateway](code-gateway.md#erweitern), Runner (`play/`), Remote-Transport im SDK, `frontend/src/play/` |
| Viewer | `spec/protocol/viewer-v1/` | [Viewer](code-viewer.md#neues-feld-in-einer-nachricht): Python-Seite, Modell, Anzeige |

- `spec-check spec` prüft Schemas und Beispiele; jede neue Nachricht oder jedes neue Feld bekommt mindestens ein gültiges und ein ungültiges Beispiel.
- Eine inkompatible Änderung bekommt eine neue Protokollversion (Ordner `v2`) statt einer Änderung in `v1`; sie ist eine Konzeptentscheidung.
- Testvektoren werden nie von Hand bearbeitet; die Quelle ist `tools/testvector-gen`. `testvector-gen spec --check` in der CI findet Abweichungen.

## Neue Einstellung

Einstellungen der Website liegen in der Collection `settings`, eine Gruppe je Dokument (E154). Grenzen der Sandbox sind ausdrücklich nicht einstellbar (E23, A14).

1. Gehört der Wert in eine bestehende Gruppe, Feld in deren Modul unter `sbm_store` ergänzen (`coder_settings.py` mit Dokument `coders`, `account_settings.py` mit `accounts` samt Einladungen, `rating_settings.py` mit `rating_rule`, `estimate_settings.py` mit `estimate`; dazu `play_settings.py` für `/admin/play` und `queue_settings.py` für die Pause der Queue): Dataclass-Feld mit Standard, Bereich in `LIMITS`, Prüfung in `problem`. Fehlt es im Dokument, gilt der Standard; eine Migration ist nicht nötig.
2. Neue Gruppe: [Rezept in der Code-Karte Store](code-store.md#neue-einstellungsgruppe) und [in der Code-Karte Web-API](code-backend.md#neue-einstellungsgruppe).
3. Vertrag: Feld im Schema der Gruppe (etwa `CoderSettings`), bei einer neuen Gruppe zusätzlich Eintrag in `AdminSettings` und Pfad `/admin/settings/<gruppe>`; dann `npm run api-types`.
4. Frontend: Feld in `frontend/src/pages/admin/settingsFields.ts`, Texte in beiden Sprachdateien.
5. Leser: Der Code, der den Wert braucht, liest ihn mit `get(db)` aus dem Gruppenmodul, nicht aus einer Umgebungsvariable.
6. Doku: E154 erweitern oder eine neue Entscheidung, Zeile `settings` in [datenmodell.md](../komponenten/datenmodell.md).

Werte, die nur den Betrieb betreffen (Ports, Pfade, Anzahl Plätze), bleiben Umgebungsvariablen der Dienste; Rezepte in den Code-Karten [Runner](code-runner.md#neue-umgebungsvariable-oder-einstellung) und [Gateway](code-gateway.md#neue-grenze-oder-umgebungsvariable).

## Neue Job-Art

Alles, was Bot-Code ausführt oder lange dauert, ist ein Job in der Queue, den der Runner abholt. Die Web-API legt nur das Job-Dokument an.

1. Entscheidung: Wer legt den Job an, welche Priorität, was passiert bei Abbruch und Neustart, gibt es Wiederholungen.
2. Store: Konstante und Fabrik in `jobs.py`, Felder in [datenmodell.md](../komponenten/datenmodell.md).
3. Runner: [Rezept „Neue Job-Art“](code-runner.md#neue-job-art).
4. Web-API: Endpunkt zum Anlegen, falls Nutzer ihn auslösen; Anzeige in der Queue (`GET /queue`, `/admin/queue`) prüfen.
5. Frontend: Queue-Seiten zeigen Art und Status; Texte ergänzen.
6. Doku: [match-runner.md](../komponenten/match-runner.md), [ablaeufe.md](../architektur/ablaeufe.md).

## Nummern für Entscheidungen und Migrationen

Parallel laufende Meilensteine haben getrennte Nummernkreise, damit sich gleichzeitige Arbeit nicht überschneidet.

| Meilenstein | Entscheidungen | Migrationen | Stand |
|-------------|----------------|-------------|-------|
| M0–M3 | E1–E98 und E105 | `0001`–`0004` | abgeschlossen |
| M4 | E99–E108 (E106–E108 Viewer), danach E130–E149 (E130) | unterhalb `0110`, zuletzt `0008` | läuft (alle fünf Schritte umgesetzt, zuletzt der Live-Kanal mit E142; Abnahme auf dem Server steht aus) |
| M7 | E110–E129 | `0110`–`0149` | abgeschlossen |
| M6 | E150–E169 | ab `0150`, zuletzt `0153` | läuft |
| M5 | E192–E219 (C#), E220–E239 (JavaScript) | ab `0220` | läuft (C# und JavaScript je Schritt 1 umgesetzt) |

- Freie Nummern im Kreis des eigenen Meilensteins nehmen, der Reihe nach. Ist ein Kreis voll oder kommt ein neuer Meilenstein parallel dazu, legt eine eigene Entscheidung einen neuen Kreis fest (wie E110, E130 und E150).
- Migrationen tragen ihre Nummer im Dateinamen (`m0154_<thema>.py`) und in der Id (`0154_<thema>`); die Reihenfolge der Ausführung ist die Liste `MIGRATIONS`, nicht die Nummer ([Code-Karte Store](code-store.md#neue-migration)).
- Eine geänderte Entscheidung wird in ihrer Zeile angepasst, mit Hinweis „geändert mit E…, vorher: …“. Ein offener Punkt (O…), den eine Entscheidung löst, verschwindet aus der Tabelle „Offene Punkte“; die Entscheidung nennt ihn („Löst O21“).
- Annahmen (A…) sind von der Entwicklung gesetzte Festlegungen mit Alternative; Risiken (R…) bekommen eine Einordnung. Beide werden fortlaufend nummeriert.

## SDK veröffentlichen

1. Änderungen am SDK, am Kern oder am Viewer sind auf `master` und die CI ist grün.
2. Version in `sdk/core/CMakeLists.txt` (`project(sbm_core VERSION X.Y.Z …)`) setzen; Paket und `sbm.__version__` übernehmen sie. Im selben Commit `version` in `sdk/javascript/package.json` und `package-lock.json` gleichziehen (`npm version X.Y.Z --no-git-tag-version` in `sdk/javascript`); `version.test.ts` prüft das. Semantische Versionen: neue Funktionen erhöhen die mittlere Stelle.
3. Im selben Commit `CLAUDE.md` (Absatz „Stand“) und die Nutzerdoku unter `sdk/python/docs/` nachführen.
4. `git tag vX.Y.Z` und `git push origin master vX.Y.Z`. `wheels.yml` baut, testet und veröffentlicht auf PyPI (E70), `npm.yml` das JavaScript-SDK auf npm (E226); Ablauf in [tests-und-ci.md](tests-und-ci.md#release-des-sdk-wheelsyml).
5. Die Vorlage `templates/python/requirements.txt` nennt das Paket ohne Version, `templates/javascript/package.json` mit Untergrenze; beide installieren also die neueste; nutzt die Vorlage eine neue Funktion, erst nach der Veröffentlichung auf `master` bringen.

Das Deploy der Website ist davon unabhängig: `deploy/python.Dockerfile` baut das SDK aus dem Repo (ohne Viewer), nicht von PyPI.

## Checkliste vor dem Commit

- [ ] Entscheidung eingetragen bzw. angepasst, Komponenten-Datei und Code-Karte nachgeführt.
- [ ] `spec-check spec` bei Änderungen unter `spec/`; `testvector-gen spec --check --perft fast` bei Änderungen an Vektoren oder Generator.
- [ ] Tests aller Pakete, die laut [Bereichstabelle](tests-und-ci.md#bereiche-und-jobs) betroffen sind; Python-SDK vorher neu installiert.
- [ ] `ruff check` und `ruff format --check` für jedes geänderte Python-Paket; `npm run lint`, `npm run format:check`, `npm run build` im Frontend; `clang-format --dry-run --Werror` für nativen Code.
- [ ] `npm run api-types:check` nach Änderungen an `openapi.json`.
- [ ] Neue Texte in `de.json` und `en.json`.
- [ ] Neue Befehle in die Tabelle „Befehle“ der `CLAUDE.md`, neue Verzeichnisse in [`changed-areas.sh`](../../.github/scripts/changed-areas.sh).
- [ ] Diff durchgesehen: keine Secrets, Zugangsdaten oder Serverpfade (öffentliches Repo), keine auskommentierten Reste, keine Sammeldateien.
- [ ] Commit-Nachricht auf Englisch, im Imperativ, eine Zeile Zusammenfassung.
