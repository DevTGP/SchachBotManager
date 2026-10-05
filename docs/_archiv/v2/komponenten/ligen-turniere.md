# Disziplinen, Ligen, Turniere, Queue

Alle Parameter dieser Datei sind über die Admin-Oberfläche einstellbar und liegen in der DB (E13).

## Disziplin

Zentrales Konfigurationsobjekt. Ligen, Turniere und Einzelspiele verweisen auf genau eine Disziplin. Sie enthält **keine sprachspezifischen Einstellungen** (E8).

| Feld | Beispiel |
|------|----------|
| Zeitkontrolle | Grundzeit, Inkrement, Startbudget, Toleranz pro Zug (Wanduhrzeit, E19) |
| Ressourcen | Speicherlimit, CPU-Anteil, max. Quellcode-/Artefaktgröße |
| Regeln | Maximale Zugzahl, Verhalten bei Timeout mit ungenügendem Material |
| Logging | Maximale Log-Stufe und Log-Menge |

Beispiele: „Standard 30 min“, „Blitz 3+2“, „64 MB Speicher“, „Max. 10 KiB Quellcode“.

Änderungen an einer Disziplin gelten erst ab der nächsten Saison/dem nächsten Turnier; laufende Wettbewerbe arbeiten mit einem Schnappschuss.

## Ligen (E7)

### Struktur

- Eine Liga besteht aus **Stufen** (1 = oberste) mit fester Größe.
- Reichen die Plätze der untersten Stufe nicht: parallele Gruppen oder Warteliste (einstellbar).
- Neue Bots starten in der untersten Stufe und werden zum nächsten Saisonstart aufgenommen.
- Keine Begrenzung der Versionen einer Abstammung (E14).

### Konfiguration

| Parameter | Bedeutung |
|-----------|-----------|
| Disziplin | Verweis |
| Stufenanzahl, Größe pro Stufe | Pyramide |
| Spiele pro Paarung | 1, 2 (beide Farben) oder mehr |
| Auf-/Absteiger pro Stufe | Anzahl |
| Wiederholung | Saisonstart-Regel, Pause zwischen Saisons |
| Punkte | Sieg / Remis / Niederlage |
| Tiebreak-Reihenfolge | z. B. direkter Vergleich, Sonneborn-Berger, Anzahl Siege |
| Mindestteilnehmer | Sonst startet die Saison nicht |
| Priorität in der Queue | Gewicht gegenüber anderen Wettbewerben |

### Saison-Lebenszyklus

`planned → registration_closed → running → finished`

1. Teilnehmer festschreiben (Auf-/Absteiger, Neuanmeldungen, Abmeldungen).
2. Paarungen erzeugen und in die Queue stellen.
3. Tabelle nach jedem Match fortschreiben.
4. Abschluss, sobald alle Spiele gespielt sind: Endtabelle, Auf-/Abstieg, nächste Saison planen.

Da es keine festen Termine gibt (E20), endet eine Saison, wenn ihre Spiele durch sind – nicht an einem Datum. Die Wiederholungsregel legt fest, wann frühestens die nächste beginnt.

### Bot verlässt die Liga während der Saison (E17)

| Schritt | Regel |
|---------|-------|
| Tabelle | Der Bot wird aus der Tabelle entfernt und als „zurückgezogen“ geführt |
| Gespielte Partien | Bleiben unverändert gewertet |
| Ausstehende Partien | Werden nicht gespielt; der Gegner erhält einen **kampflosen Sieg**, als solcher markiert und in Tabelle wie Partienliste erkennbar |
| Rating | Kampflose Siege ändern kein Rating |
| Tiebreaks | Zu klären bei der Umsetzung: kampflose Siege zählen als Punkte, fließen aber nicht in Sonneborn-Berger/direkten Vergleich ein |
| Abstieg | In dieser Stufe steigt ein Bot weniger ab |
| Nachrücken | Der frei gewordene Platz wird zur nächsten Saison durch einen zusätzlichen Aufsteiger aus der Stufe darunter gefüllt |

Auslöser: Besitzer oder Admin deaktiviert den Bot, oder der Bot fällt wiederholt durch technische Fehler aus (Schwelle einstellbar).

### Weitere Sonderfälle

| Fall | Regel |
|------|-------|
| Ungerade Teilnehmerzahl | Spielfrei-Runde |
| Zu wenige Bots für alle Stufen | Stufen von oben füllen, untere entfallen |
| Infrastrukturfehler | Match wird neu in die Queue gestellt |

## Turniere

| Parameter | Optionen |
|-----------|----------|
| Format | Round-Robin, Schweizer System, K.-o. |
| Teilnehmer | Min/Max, Anmeldefenster, optional Zulassungsbedingung |
| Wiederholung | Einmalig oder wiederkehrend |
| Disziplin | Verweis |
| Formatdetails | Rundenzahl (Schweizer), Spiele pro Begegnung, Setzliste (Rating oder Zufall) |
| Priorität in der Queue | Gewicht |

Zu beachten:

- **K.-o. braucht eine Remis-Auflösung** (z. B. Rückspiel mit vertauschten Farben, danach kürzere Zeitkontrolle, zuletzt Entscheidungspartie mit Remisvorteil) – einstellbar.
- **Schweizer System** paart rundenweise: die nächste Runde entsteht erst, wenn die vorige vollständig gespielt ist.
- Turniere haben keine Auswirkung auf Liga-Stufen.
- Zieht sich ein Bot zurück, gilt die Regel aus E17 sinngemäß.

## Einzelspiele

Vom Admin oder Besitzer angesetzt (z. B. Version gegen Version), ungewertet oder nur fürs Rating.

## Rating

- Pro Bot und Disziplin ein Rating (Elo oder Glicko-2) als Statistik; kein Einfluss auf Auf-/Abstieg.
- Ungewertete Spiele (Mensch, Remote, Tests) und kampflose Siege ändern es nicht.

## Spiel-Queue (E20)

Eine gemeinsame Queue für alle Spiele aller Wettbewerbe.

| Eigenschaft | Verhalten |
|-------------|-----------|
| Abarbeitung | Sobald ein Spiel endet, startet sofort das nächste; kein Leerlauf, keine festen Startzeiten |
| Parallelität | Anzahl gleichzeitiger Spiele einstellbar; Standard 1 (E12) |
| Reihenfolge | Nach Priorität des Wettbewerbs, innerhalb gleicher Priorität abwechselnd zwischen den Wettbewerben, damit kein Wettbewerb die Queue blockiert |
| Überschneidungen | Mehrere Ligen und Turniere dürfen gleichzeitig laufen; sie teilen sich die Queue |
| Bot-Sperre | Ein Bot spielt nie zwei Partien gleichzeitig (relevant bei Parallelität > 1) |
| Pausieren | Admin kann die Queue anhalten (z. B. wenn der Server anderweitig gebraucht wird); optional Zeitfenster, in denen keine Spiele starten |
| Eingriff | Admin kann Spiele vorziehen, zurückstellen, abbrechen, neu ansetzen |

### Geschätzte Startzeiten

- Für jedes wartende Spiel wird eine voraussichtliche Startzeit berechnet und online angezeigt.
- Grundlage: Position in der Queue und erwartete Dauer der davorliegenden Spiele (gleitender Durchschnitt der tatsächlichen Dauer je Disziplin, ersatzweise ein Anteil der Maximaldauer).
- Die Schätzung wird nach jedem beendeten Spiel neu berechnet und ist als Schätzung gekennzeichnet.

### Prioritäten (Standard, einstellbar)

Liga > Turnier > Einzelspiel > Verifikation. Spiele gegen Menschen und Remote-Bots laufen außerhalb dieser Reihenfolge mit eigener Kapazitätsgrenze, weil ein wartender Mensch nicht hinter einer 60-Minuten-Partie anstehen kann; sie belegen dann zusätzlich Rechenzeit (R10).

### Überwachung

Hängende Spiele erkennen (Lease abgelaufen), neu ansetzen, im Adminbereich anzeigen. Genau eine aktive Scheduler-Instanz.

## Kapazitätsrechnung (R5)

- Zwei Spiele pro Paarung mit N Bots: N·(N−1) Partien.
- Eine Partie mit 30 min Grundzeit je Seite dauert maximal ~60 min plus Inkremente.
- Beispiel: 10 Bots → 90 Partien → bei einem Spiel gleichzeitig bis zu ~4 Tage pro Stufe, wenn jede Partie die Zeit ausschöpft.

Die Admin-Oberfläche zeigt beim Anlegen oder Ändern eines Wettbewerbs die geschätzte Gesamtlaufzeit und die Auswirkung auf die bestehende Queue.
