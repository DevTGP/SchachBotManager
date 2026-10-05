# Disziplinen, Ligen, Turniere, Scheduler

## Disziplin

Zentrales Konfigurationsobjekt (E8). Ligen, Turniere und Einzelspiele verweisen auf genau eine Disziplin.

| Feld | Beispiel |
|------|----------|
| Zeitkontrolle | Grundzeit, Inkrement, Startbudget, Toleranz pro Zug |
| Ressourcen | Speicherlimit, CPU-Quote, max. Quellcode-/Artefaktgröße |
| Sprachen | Erlaubte Sprachen; optional Zeit-/Speicherfaktor oder Sockel je Sprache |
| Regeln | Maximale Zugzahl, Verhalten bei Timeout mit ungenügendem Material |
| Logging | Maximale Log-Stufe und Log-Menge |

Beispiele: „Standard 30 min“, „Blitz 3+2“, „64 MB Speicher“, „Nur Python“, „Max. 10 KiB Quellcode“.

Änderungen an einer Disziplin gelten erst ab der nächsten Saison/dem nächsten Turnier; laufende Wettbewerbe arbeiten mit einem Schnappschuss.

## Ligen (E7)

### Struktur

- Eine Liga besteht aus **Stufen** (1 = oberste). Jede Stufe hat eine feste Größe.
- Reichen die Plätze der untersten Stufe nicht, entstehen dort parallele **Gruppen**; alternativ Warteliste (konfigurierbar).
- Neue Bots starten immer in der untersten Stufe und werden zum nächsten Saisonstart aufgenommen.

### Konfiguration

| Parameter | Bedeutung |
|-----------|-----------|
| Disziplin | Verweis |
| Stufenanzahl, Größe pro Stufe | Pyramide |
| Runden | Einfach oder doppelt Round-Robin (doppelt = beide Farben) |
| Auf-/Absteiger pro Stufe | Anzahl |
| Wiederholung | Saisonstart-Regel (z. B. wöchentlich, monatlich), Pause zwischen Saisons |
| Punkte | Sieg / Remis / Niederlage |
| Tiebreak-Reihenfolge | z. B. direkter Vergleich, Sonneborn-Berger, Anzahl Siege |
| Mindestteilnehmer | Sonst wird die Saison nicht gestartet |
| Max. Versionen je Abstammung | Schutz gegen R1 (O5) |

### Saison-Lebenszyklus

`planned → registration_closed → running → finished`

1. Teilnehmer festschreiben (Auf-/Absteiger, Neuanmeldungen, Abmeldungen).
2. Paarungen und Match-Jobs erzeugen.
3. Tabelle nach jedem Match fortschreiben.
4. Abschluss: Endtabelle, Auf-/Abstieg, nächste Saison planen.

### Sonderfälle

| Fall | Zu regeln |
|------|-----------|
| Bot wird während der Saison deaktiviert/zurückgezogen | Bisherige Partien annullieren oder Restpartien kampflos werten (O8) |
| Freie Plätze durch Abgänge | Zusätzliche Aufsteiger oder weniger Absteiger |
| Ungerade Teilnehmerzahl | Spielfrei-Runde |
| Zu wenige Bots für alle Stufen | Stufen von oben füllen, untere entfallen |
| Infrastrukturfehler | Match wird neu angesetzt, Saisonende verschiebt sich |

## Turniere

| Parameter | Optionen |
|-----------|----------|
| Format | Round-Robin, Schweizer System, K.-o. |
| Teilnehmer | Min/Max, Anmeldefenster, optional Zulassungsbedingung (z. B. Mindest-Liga-Stufe) |
| Wiederholung | Einmalig oder wiederkehrend |
| Disziplin | Verweis |
| Formatdetails | Rundenzahl (Schweizer), Spiele pro Begegnung, Setzliste (nach Rating oder Zufall) |

Zu beachten:

- **K.-o. braucht eine Remis-Auflösung** (z. B. Rückspiel mit vertauschten Farben, danach kürzere Zeitkontrolle, zuletzt Entscheidungspartie mit Remisvorteil).
- **Schweizer System** paart rundenweise: die nächste Runde kann erst erzeugt werden, wenn die vorige vollständig gespielt ist.
- Turniere haben keine Auswirkung auf Liga-Stufen.

## Einzelspiele

- Vom Admin oder Besitzer angesetzt (z. B. Version gegen Version), ungewertet oder nur fürs Rating.
- Laufen mit niedrigster Priorität.

## Rating

- Pro Bot und Disziplin ein Rating (Elo oder Glicko-2) als Statistik; kein Einfluss auf Auf-/Abstieg (E7).
- Verwendbar für Setzlisten und zur Anzeige der Entwicklung.
- Ungewertete Spiele (Mensch, Remote, Tests) ändern es nicht (A9).

## Scheduler

| Aufgabe | Beschreibung |
|---------|--------------|
| Zeitsteuerung | Prüft periodisch fällige Saison-/Turnierstarts und Rundenwechsel |
| Paarungserzeugung | Je Format; deterministisch und idempotent (erneuter Lauf erzeugt keine Duplikate) |
| Job-Erzeugung | Match-Jobs mit Priorität: Liga > Turnier > Einzelspiel > Verifikation > Mensch/Remote nach eigener Kapazitätsgrenze |
| Entzerrung | Kein Bot spielt zwei Partien gleichzeitig; lange Spiele werden über den Saisonzeitraum verteilt |
| Überwachung | Hängende Jobs erkennen, neu ansetzen, Admin benachrichtigen |

Genau eine aktive Scheduler-Instanz (Leader-Lock in der DB).

## Kapazitätsrechnung (R5, O4)

- Doppeltes Round-Robin mit N Bots: N·(N−1) Partien.
- Eine Partie mit 30 min Grundzeit je Seite dauert maximal ~60 min plus Inkremente und belegt einen Kern.
- Beispiel: 10 Bots → 90 Partien → bis zu 90 Kernstunden; bei 4 parallelen Spielen ~23 h pro Stufe und Saison.

Daraus folgen Saisonlänge, Liga-Größe und Anzahl paralleler Disziplinen. Die Admin-Oberfläche sollte beim Anlegen einer Liga die geschätzte Laufzeit anzeigen.
