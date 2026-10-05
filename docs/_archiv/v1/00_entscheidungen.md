# Entscheidungen, Annahmen, offene Punkte

## 1. Getroffene Entscheidungen (von dir bestätigt)

| ID | Thema | Entscheidung | Konsequenz |
|----|-------|--------------|------------|
| E1 | Sicherheit | Sandbox **und** strikte statische Analyse | Pro Sprache ein eigener Analyzer; Sandbox bleibt die eigentliche Sicherheitsgrenze |
| E2 | Schachlogik | SDK liefert alles (Brett, legale Züge, make/undo, Endbedingungen) | Vollständiger Schachkern in jedem SDK |
| E3 | SDK-Kern | Nativ pro Sprache | 5 Implementierungen, gemeinsame Konformitätstests (Perft) zwingend |
| E4 | Legitimierung | Invite-only | Keine offene Registrierung; Invite-Verwaltung im Adminbereich |
| E5 | Frontend | Flask als reine API + separate SPA | Zwei Codebasen, Build-Schritt fürs Frontend |
| E6 | Bot-Bearbeitung | Neue Version = neuer Bot; Versionen können gegeneinander antreten | Jede Version ist eigener Teilnehmer, startet in der untersten Liga, eigene Historie; Verknüpfung über Abstammung (`lineage`) |
| E7 | Liga-Modus | Saisons mit Tabellen (Round-Robin, Auf-/Abstieg) | Rating (Elo/Glicko) nur als Statistik |
| E8 | Fairness | Limits, Sprachfaktoren und erlaubte Sprachen pro Disziplin konfigurierbar | Disziplin ist zentrales Konfigurationsobjekt |

Aus dem Anforderungstext fix: MongoDB, Flask, GitHub Actions, Sprachen Python / C++ / Java / C# / JavaScript.

## 2. Annahmen (von mir gesetzt, bitte widersprechen falls falsch)

| ID | Annahme | Alternative |
|----|---------|-------------|
| A1 | Nur Standardschach (kein Chess960 o. Ä.) | Varianten als Disziplin-Attribut |
| A2 | Ein einzelner Linux-Host, alles über Docker Compose | Getrennter Worker-Host für Bot-Ausführung |
| A3 | Kein Pondering: Bots sind außerhalb ihres Zuges eingefroren (ergibt sich aus „nur in eigener Zeit rechnen“) | – |
| A4 | Ein Bot = ein Thread, ein CPU-Kern; Bedenkzeit wird als Wanduhrzeit gemessen | CPU-Zeit-Messung, Mehrkern-Disziplinen |
| A5 | Bot-Upload = Quellcode (einzelne Datei oder Archiv), Build erfolgt serverseitig | Upload fertiger Binaries (sicherheitlich deutlich schlechter prüfbar) |
| A6 | Server ist alleiniger Schiedsrichter; das Brett im SDK ist nur Komfort für den Bot | – |
| A7 | Kommunikation Bot ↔ Server über stdin/stdout (zeilenweises JSON); Bots sprechen nie direkt miteinander | Lokale Sockets, gRPC |
| A8 | Job-Queue in MongoDB (kein zusätzlicher Broker) | Redis + RQ/Celery |
| A9 | Spiele gegen Menschen und Remote-Bots sind ungewertet | Eigene gewertete Kategorie |
| A10 | Idiomatische Schreibweise pro Sprache bei identischen Wörtern (`legal_moves` / `legalMoves` / `LegalMoves`) | Exakt gleiche Schreibweise in allen Sprachen |

## 3. Offene Punkte (vor dem jeweiligen Meilenstein zu klären)

| ID | Frage | Relevant ab |
|----|-------|-------------|
| O1 | SPA-Framework (React / Vue / Svelte) | M2 |
| O2 | Sind Partien, Tabellen und Bot-Profile öffentlich oder nur für eingeloggte Nutzer sichtbar? | M2 |
| O3 | Darf jeder Besucher gegen Bots spielen oder nur Accounts? | M7 |
| O4 | Server-Hardware (Kerne, RAM) → bestimmt parallele Spiele und Saisonlänge | M4 |
| O5 | Obergrenze aktiver Versionen derselben Abstammung pro Liga (siehe Risiko R1) | M4 |
| O6 | Ist der Quellcode eines Bots für andere einsehbar? | M3 |
| O7 | Whitelist der erlaubten Bibliotheken pro Sprache (z. B. numpy) | M3/M5 |
| O8 | Was passiert mit bereits gespielten Partien, wenn ein Bot mitten in der Saison deaktiviert wird (annullieren / kampflos werten)? | M4 |
| O9 | Stärkere Isolation (gVisor, rootless Docker, eigene VM) nötig? | M3/M8 |

## 4. Risiken

| ID | Risiko | Einordnung |
|----|--------|-----------|
| R1 | E6 erlaubt, eine Liga mit vielen eigenen Versionen zu füllen (Punkteschieberei, Verdrängen anderer) | Begrenzbar über O5 und Admin-Freigabe |
| R2 | 5 native Schachkerne (E3) divergieren im Verhalten | Gemeinsame Testvektoren als Merge-Gate in CI |
| R3 | Statische Analyse ist umgehbar (v. a. Python, JS, C++) | Darf nie alleinige Schutzschicht sein; Sandbox muss allein ausreichen |
| R4 | Runner benötigt Zugriff auf die Container-Runtime (root-äquivalent) | Runner strikt von der öffentlichen Web-API trennen |
| R5 | Rechenbedarf: eine 30+30-min-Partie belegt bis zu ~1 h einen Kern | Kapazitätsrechnung in [ligen-turniere.md](komponenten/ligen-turniere.md) |
| R6 | Laufzeitmessung in Containern schwankt (Scheduling, GC, JIT-Warmup) | Kern-Pinning, Toleranz pro Zug, Startbudget getrennt von Bedenkzeit |
