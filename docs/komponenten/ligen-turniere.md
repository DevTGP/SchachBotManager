# Disziplinen, Ligen, Turniere, Queue

Alle Parameter dieser Datei sind über die Admin-Oberfläche einstellbar und liegen in der DB (E13).

## Disziplin

Zentrales Konfigurationsobjekt. Ligen, Turniere und Einzelspiele verweisen auf genau eine Disziplin. Sie enthält **keine sprachspezifischen Einstellungen** (E8).

| Feld | Beispiel |
|------|----------|
| Zeitkontrolle | Grundzeit, Inkrement, Startbudget, Toleranz pro Zug (Wanduhrzeit, E19) |
| Regeln | Maximale Zugzahl, Verhalten bei Timeout mit ungenügendem Material |
| Logging | Maximale Log-Stufe und Log-Menge |

Beispiele: „Standard 30 min“, „Blitz 3+2“, „Bullet 1+0“.

Ressourcenlimitierte Disziplinen (Speicher, CPU, Dateigröße) sind zurückgestellt (E23).

Änderungen an einer Disziplin gelten erst ab der nächsten Saison/dem nächsten Turnier; laufende Wettbewerbe arbeiten mit einem Schnappschuss.

### Stand M4, Schritt 1 (E100)

| Feld | Bereich | Standard |
|------|---------|----------|
| `name` | 1 bis 40 Zeichen ohne Steuerzeichen, ohne Rücksicht auf Groß- und Kleinschreibung eindeutig | – |
| `initial_time_ms` | 1 s bis 24 h | – |
| `increment_ms` | 0 bis 1 h | 0 |
| `startup_ms` | 1 bis 60 s | 10 s |
| `tolerance_ms` | 0 bis 1000 ms | 20 ms |
| `max_moves` | 1 bis 2000 | 500 |
| `archived` | ja/nein | nein |

- Admins legen Disziplinen auf `/admin/disciplines` an, ändern und archivieren sie. Gelöscht wird nie; archivierte Disziplinen sind für neue Partien nicht wählbar, bleiben aber lesbar.
- Eine Partie kopiert die Disziplin beim Einreihen in `discipline_snapshot` samt `discipline_id`. Änderungen wirken nur auf später eingereihte Partien.
- Noch nicht einstellbar: Log-Stufe und Log-Menge (O19) und das Verhalten bei Zeitüberschreitung mit ungenügendem Material (immer Remis).

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
| Wiederholung | Kalender: erster Termin und Intervall (E171) |
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
| Tiebreaks | Kampflose Siege zählen als Punkte, fließen aber nicht in Sonneborn-Berger und direkten Vergleich ein (E25) |
| Abstieg | In dieser Stufe steigt ein Bot weniger ab |
| Nachrücken | Der frei gewordene Platz wird zur nächsten Saison durch einen zusätzlichen Aufsteiger aus der Stufe darunter gefüllt |

Auslöser (E136): Abmeldung durch Besitzer oder Admin, Zurückziehen des Bots durch den Besitzer (E96), Sperre oder Löschen durch einen Admin (E93, E105). Wiederholte technische Fehler sind kein Auslöser.

### Weitere Sonderfälle

| Fall | Regel |
|------|-------|
| Ungerade Teilnehmerzahl | Spielfrei-Runde |
| Zu wenige Bots für alle Stufen | Stufen von oben füllen, untere entfallen |
| Infrastrukturfehler | Match wird neu in die Queue gestellt |

### Stand M4, Schritt 3 (E130–E137)

Die Abschnitte oben beschreiben das Ziel; umgesetzt ist es so:

| Feld | Bereich | Standard |
|------|---------|----------|
| `name` | 1 bis 40 Zeichen, ohne Rücksicht auf Groß- und Kleinschreibung eindeutig | – |
| `discipline_id` | nicht archivierte Disziplin | – |
| `tiers` | 1 bis 10 | 1 |
| `tier_size` | 2 bis 32 | 10 |
| `games_per_pairing` | 1 bis 10 | 2 |
| `promotions` | 0 bis ⌊`tier_size`/2⌋ je Grenze, ebenso viele Absteiger | 2 |
| `points` | `win`, `draw`, `loss` je 0 bis 10 in halben Punkten, Sieg > Niederlage, Sieg ≥ Remis ≥ Niederlage | 1, ½, 0 |
| `tiebreaks` | Liste aus `wins`, `head_to_head`, `sonneborn_berger`, `fewer_moves` ohne Doppelte | die ersten drei |
| `min_participants` | 2 bis 320 | 2 |
| `recurrence` | Kalender nach E171: keiner oder `first_start` und `interval_hours` (1 bis 8760); bis E171 stattdessen `pause_minutes` | keiner |
| `priority` | 0 bis 1000 | 50 |
| `ready_hours` | 1 bis 336; Frist für die Bereitschaft von Spielern (E183) | 48 |
| `archived` | ja/nein | nein |

- **Struktur:** Alle Stufen sind gleich groß, Auf- und Abstieg gelten an jeder Grenze gleich (E131). Statt paralleler Gruppen gibt es die Warteliste; eine neue unterste Stufe entsteht durch eine höhere Stufenzahl. Änderungen der Einstellungen wirken ab dem nächsten Saisonstart.
- **Saison:** `planned → running → finished` (E132). Die erste Saison gibt ein Admin auf `/admin/leagues` frei; jede weitere plant der Runner beim Abschluss nach dem Kalender (E171, bis dahin mit `pause_minutes` Abstand). Eine fällige Saison startet, sobald genug Bots da sind. `registration_closed` entfällt, weil der Start Aufstellung und Spielplan in einem Schritt festschreibt.
- **Aufstellung (E133):** Setzliste aus der vorigen Saison, danach die Warteliste nach Anmeldezeit; von oben in Stufen geschnitten. Am Ende steigen je Grenze `promotions` Bots ab, weniger um die Zahl der Rückzüge in der Stufe; aufgefüllt wird von unten mit den Besten.
- **Spielplan (E134):** Rundenturnier nach dem Kreisverfahren je Stufe, bei `games_per_pairing` > 1 wiederholt mit getauschten Farben. Alle Partien entstehen beim Start.
- **Takt (E189):** Je Stufe läuft nur die aktuelle Runde, die früheste mit einer wartenden oder laufenden Partie. Nur ihre Partien zwischen Bots bekommen Jobs, nur ihre Partien mit Konten werden freigegeben; die nächste Runde folgt, wenn alle Partien der Runde beendet sind (gespielt, kampflos oder abgebrochen). So ist kein Teilnehmer mehr als eine Partie voraus, auch in Ligen nur mit Bots.
- **Tabelle (E135):** aus den beendeten Partien berechnet; danach entscheiden die Kriterien aus `tiebreaks` und zuletzt ein beim Start gespeichertes Los. Beim Abschluss speichert die Saison die Endtabelle.
- **Anmeldung (E136, E181, E182):** Besitzer und Admins melden `verified` Bots auf der Bot-Seite an und ab, auf der Liga-Seite an, Admins dort auch ab. Admins melden jeden geprüften Bot an, auch die Referenzbots. Konten melden sich auf der Liga-Seite selbst an und ab, Admins jedes aktive Konto (Abschnitt „Spieler in Wettbewerben“). Ein Rückzug während der Saison macht aus den wartenden Partien des Bots kampflose Siege des Gegners (`finished`, `termination` `forfeit_withdrawn`, ungewertet).

### Stand M4, Schritt 4 (E138–E141)

- **Spielplan (E138):** Die Saisonseite zeigt unter jeder Tabelle die Runden der Stufe mit allen Brettern, Ergebnissen, kampflosen Partien und dem spielfreien Bot (`GET /seasons/{id}/schedule?tier=n`).
- **Liga-Verlauf (E139):** Die Bot-Seite listet die Saisons genau dieser Version mit Stufe, Platz, Punkten und Ausgang; eine laufende Saison mit dem aktuellen Platz.
- **Historie (E140, E141):** Dazu kommen auf der Bot-Seite der Rating-Verlauf je Disziplin als Kurve und die Bilanz nach Ergebnis gesamt und je Disziplin.

## Kalender (E171)

Ligen und Turniere haben denselben Kalender `recurrence`: keiner (`null`) oder `first_start` (UTC) und `interval_hours` (1 bis 8760). Die Termine sind `first_start + k · interval_hours`.

| Fall | Start der nächsten Saison oder Ausgabe |
|------|----------------------------------------|
| Mit Kalender, erste | Erster Termin ab jetzt |
| Mit Kalender, weitere | Erster Termin nach dem Start der vorigen; ist er beim Ende der vorigen schon vorbei, sofort |
| Ohne Kalender | Wartet auf einen Admin (`POST /admin/leagues/{id}/start` bzw. `/admin/tournaments/{id}/start`); 409, wenn nichts wartet oder die geplante schon fällig ist |
| Kalender geändert | Start der geplanten Saison oder Ausgabe wird neu berechnet; ohne Kalender wartet sie wieder auf den Admin |

- Der Start durch den Admin zieht auch einen späteren Termin vor.
- Der Kalender gehört nicht zum Schnappschuss der laufenden Saison oder Ausgabe.
- Er ersetzt `pause_minutes`; Migration `0154` rechnet bestehende Ligen um (`first_start` = Zeitpunkt der Migration, `interval_hours` = ⌈`pause_minutes`/60⌉, mindestens 1).
- Die Oberfläche zeigt und nimmt Ortszeit; das Intervall wird in Stunden, Tagen oder Wochen eingegeben und in Stunden gespeichert.
- Eine Liga, deren erste Saison noch nicht freigegeben ist, wartet weiter auf den Admin, auch wenn sie einen Kalender hat (E132).

## Turniere

### Ziel

| Parameter | Optionen |
|-----------|----------|
| Format | Round-Robin, Schweizer System, K.-o. |
| Teilnehmer | Min/Max, Anmeldefenster, optional Zulassungsbedingung |
| Wiederholung | Einmalig oder wiederkehrend |
| Disziplin | Verweis |
| Formatdetails | Rundenzahl (Schweizer), Spiele pro Begegnung, Setzliste (Rating oder Zufall) |
| Priorität in der Queue | Gewicht |

- Turniere haben keine Auswirkung auf Liga-Stufen.
- Zieht sich ein Bot zurück, gilt die Regel aus E17 sinngemäß.

### Stand M6, Schritt 3 (E170–E180)

Ein Turnier ist wie eine Liga eine dauerhafte Konfiguration mit Anmeldungen; gespielt wird in **Ausgaben** (`editions`), so wie eine Liga in Saisons (E170). Keine Höchstzahl an Teilnehmern, keine Zulassungsbedingung, Setzliste immer nach Rating.

| Feld | Bereich | Standard |
|------|---------|----------|
| `name` | 1 bis 40 Zeichen, ohne Rücksicht auf Groß- und Kleinschreibung eindeutig unter den Turnieren | – |
| `discipline_id` | nicht archivierte Disziplin | – |
| `format` | `round_robin`, `swiss`, `knockout`; nach dem Anlegen fest | – |
| `games_per_pairing` | 1 bis 10; Rundenturnier und K.-o.-Duell | 2 |
| `rounds` | 1 bis 20; nur Schweizer System, höchstens Teilnehmer − 1 gespielt | 5 |
| `tiebreaks` | `wins`, `head_to_head`, `sonneborn_berger`, `fewer_moves`, `buchholz`; nicht bei K.-o. | je Format (E177) |
| `tiebreak_discipline_id` | Disziplin für Tiebreak und Armageddon (nur K.-o.); leer = Turnierdisziplin | leer |
| `tiebreak_pairs` | 0 bis 5 (nur K.-o.) | 1 |
| `min_participants` | 2 bis 1024 | 2 |
| `priority` | 0 bis 1000 | 40 |
| `recurrence` | Kalender (E171) | keiner |
| `ready_hours` | 1 bis 336; Frist für die Bereitschaft von Spielern (E183) | 48 |
| `archived` | ja/nein | nein |

Alle Felder werden unabhängig vom Format gespeichert; was das Format nicht nutzt, bleibt wirkungslos. Punkte sind fest 1, ½, 0. Änderungen wirken ab der nächsten Ausgabe.

- **Ausgaben (E173):** `planned → running → finished`. Ausgabe 1 entsteht mit dem Turnier. Eine fällige Ausgabe startet mit mindestens `min_participants` (und zwei) angemeldeten `verified` Bots und schreibt Schnappschuss (Einstellungen samt Disziplinen) und Teilnehmer fest: Setzliste nach Rating der Version in der Turnierdisziplin, bei Gleichstand nach Los. Spätere Anmeldungen spielen ab der nächsten Ausgabe. Am Ende entsteht die nächste `planned` nach dem Kalender. `revision` macht jeden Schritt des Runners bedingt, so dass ein Absturz nichts doppelt anlegt.
- **Rundenturnier (E174):** Kreisverfahren wie bei Ligen, `games_per_pairing` Durchgänge mit getauschten Farben, alle Partien beim Start angelegt, Jobs nur für die aktuelle Runde wie bei Ligen (E189).
- **Schweizer System (E175):** Runde für Runde; die nächste wird gelost, wenn die laufende beendet ist. Eine Partie je Paarung. Paarung nach Punkten, dann Setzplatz, per Backtracking ohne Wiederholung (in der Punktgruppe obere gegen untere Hälfte), nur notfalls mit so wenigen Wiederholungen wie möglich. Freilos: 1 Punkt für den am schlechtesten stehenden Bot ohne bisheriges Freilos. Farben nach Ausgleich, dann Wechsel, dann Rang. Abgebrochene Partien zählen nicht und werden nicht wiederholt. Die vereinfachte Paarung ersetzt nicht die FIDE-Regel (Dutch).
- **K.-o. (E176):** Baum mit der nächsten Zweierpotenz an Plätzen in Standard-Setzreihenfolge, Freilose für die Bestgesetzten. Ein Duell hat `games_per_pairing` Partien (der besser Gesetzte beginnt mit Weiß), bei Gleichstand 2 · `tiebreak_pairs` Partien in der Tiebreak-Disziplin, dann Armageddon mit Farben per Los, bei dem Schwarz ein Remis genügt. Abgebrochene Partien eines Duells werden neu angesetzt, ohne Grenze. Wer sich zurückzieht, verliert sein Duell; ein zurückgezogener Sieger kommt nicht weiter. Platz nach erreichter Runde (1, 2, 3, 5, 9 …).
- **Tabellen (E177):** wie E135 mit Punkten 1, ½, 0; ein Freilos ist ein Punkt ohne Partie. Zusätzlich `buchholz` (Punkte der Gegner aus gespielten Partien). Standard im Rundenturnier `wins`, `head_to_head`, `sonneborn_berger`, im Schweizer System `buchholz`, `sonneborn_berger`, `wins`; danach das Los. Beim Ende speichert die Ausgabe Tabelle bzw. Platzierung.
- **Partien (E178):** Typ `tournament`, `context` mit Turnier, Ausgabe, Format, Runde, Brett und beim K.-o. `phase` und `game`; alle gewertet (Tiebreak und Armageddon in ihrer Disziplin). Jobs tragen `competition` `tournament:<id>`. Eingriffe in die Queue (E152) bleiben auf Einzelspiele beschränkt.
- **Anmeldung (E179, E181, E182):** wie bei Ligen über die Bot- und die Turnierseite, Admins für jeden geprüften Bot samt Referenzbots, Konten selbst auf der Turnierseite; sie gilt für alle folgenden Ausgaben. Abmelden, Zurückziehen, Sperren und Löschen beenden sie; in einer laufenden Ausgabe enden die wartenden Partien des Bots kampflos. Partien eines gelöschten Bots werden nicht neu angelegt, der Gegner bekommt dafür keinen kampflosen Sieg.
- **Seiten (E180):** Navigationspunkt „Turniere“ mit `/tournaments` und `/tournaments/:id`, Ausgabe `/editions/:id` mit Tabelle und Runden bzw. Turnierbaum und Platzierung, Admin-Seite `/admin/tournaments`, auf der Bot-Seite Anmeldungen und Turnierverlauf, unter `/matches` Filter nach Ausgabe.

### Verknüpfungen (E188)

- Listen und Admin-Seiten verlinken den Stand der letzten Saison bzw. Ausgabe, Liga- und Turnierseite nennen sie unter dem Titel.
- Die Saisonseite springt zu den Stufen (`#tier-N`); Saison- und Ausgabeseite verlinken die vorige und die nächste.
- Runden tragen Anker (`#tier-N-round-R`, `#round-R`). Partieseite, Partielisten, Queue und `/play/:id` verlinken den Platz einer Partie auf ihre Runde; die Runde öffnet sich dort.
- `/matches` mit Filter nach Saison oder Ausgabe verlinkt zurück.

## Spieler in Wettbewerben (E182–E186, Migration `0155`)

Konten jeder Rolle (`player`, `coder`, `admin`) nehmen wie Bots an Ligen und Turnieren teil, in gemischten Feldern.

- **Teilnehmer (E182):** Eine Anmeldung hat `bot_id` oder `user_id`; Schlüssel eines Teilnehmers ist seine Bot- oder Konto-Id (`sbm_store.participants`). Damit bleiben Spielplan, Tabellen, Auf- und Abstieg und Setzliste unverändert. Turniere setzen Konten nach ihrem Rating in der Disziplin (E163). In der Partie ist ein Konto die Seite `kind` `human`; gewertet nach E100, auch Mensch gegen Mensch. Abmelden und Deaktivieren des Kontos ziehen es zurück wie einen Bot.
- **Freigabe (E183):** Partien mit einem Menschen bekommen beim Start keinen Job. Der Runner gibt sie je Saison oder Ausgabe in der Reihenfolge (Stufe,) Runde, Brett frei, in Ligen und Rundenturnieren nur aus der aktuellen Runde (E189), solange kein beteiligtes Konto schon eine freigegebene, nicht beendete Wettbewerbspartie hat. Die Freigabe setzt `readiness` mit Frist `released_at` + `ready_hours`.
- **Bereitschaft (E183):** Auf `/play/:id` klickt das Konto „Bereit“ (`POST /matches/{id}/ready`, Antwort ein Sitz) und bleibt anwesend, solange die Seite offen ist (alle 15 s erneuert, 45 s gültig). Sind alle Menschen bereit und anwesend, startet die Partie mit einem Job `play`; zur Frist auch ohne Anwesenheit, wenn alle bereit waren. Der Runner prüft das nur zwischen zwei Jobs; `/play/:id` zeigt daher den geschätzten Start nach seiner laufenden Partie mit Countdown und Balken (E187).
- **Abwesenheit (E184):** Wer zur Frist nicht bereit ist, verliert kampflos und ungewertet (`termination` `forfeit_absent`); fehlen beide, `result` `0-0`. Tabellen zählen das wie `forfeit_withdrawn`. Beim K.-o. entscheidet die Partie das Duell (`decided_by` `absence`); fehlen beide, scheiden beide aus. Die Anmeldung bleibt.
- **Spiel (E185):** Der Play-Runner spielt die Partie über den Gateway wie E114. Er beginnt nach `connect_wait` auch ohne Sitze, die Uhr eines fehlenden oder getrennten Menschen läuft weiter. Ein Infrastrukturfehler setzt die Partie zurück: `queued` ohne Züge, neue Frist, sie wartet wieder auf „Bereit“.
- **Seiten (E186):** Knopf zum Anmelden und Abmelden des eigenen Kontos auf Liga- und Turnierseite, für Admins Auswahl eines Kontos; `/play` listet die eigenen Wettbewerbspartien mit Frist (`GET /account/competition-games`), `/play/:id` wartet, meldet Bereitschaft und spielt dann. Namen von Konten sind nicht verlinkt.
- **Offen (O25):** Ein abwesender Mensch hält eine Saison oder Ausgabe bis zu `ready_hours` je Partie auf, mit E189 auch die übrigen Partien seiner Stufe.

## Einzelspiele

Vom Admin oder Besitzer angesetzt (z. B. Version gegen Version), ungewertet oder nur fürs Rating.

Seit E100 wählt man eine Disziplin oder freie Zeiten. Nur Partien mit Disziplin aus der Grundstellung sind `rated` und zählen fürs Rating (E103); freie Zeiten und andere Startstellungen nicht. Für Coder gilt die Grenze von 5 min + 5 s nur bei freien Zeiten (E98); die Grenzen stehen seit E154 in den Einstellungen.

Seit M6 Schritt 2 (E155–E161):

- **Serie:** Mehrere Partien einer Anfrage bilden eine Serie mit eigener Seite `/series/:id` und Stand (Sieg 1, Remis ½); jede Partie verlinkt sie (E155).
- **Ungewertet wählbar:** Kästchen „Gewertet“ in beiden Formularen; abgewählt bleibt jede Partie der Anfrage ungewertet (E158).
- **Startstellungen** auch für Coder, als FEN oder aus einer PGN über `POST /positions/from-pgn`; solche Partien sind ungewertet (E159).
- **Zurückziehen:** Coder nehmen wartende eigene Partien unter „Meine Bots“ aus der Queue und bekommen sie aufs Tageslimit zurück (E157).
- **Filter** unter `/matches` nach Disziplin, Gegner und eigenen Partien (E156); **Bilanz** gegen jeden Gegner auf der Bot-Seite (E161).
- **Schnellstart:** Links „Spielen“ und „Gegen Vorgänger spielen“ in der Versionstabelle führen zum vorbelegten Formular (E160).
- **Zufälliger Gegner:** „Zufall“ statt eines Bots, für Admins auf beiden Seiten (auch Zufall gegen Zufall), für Coder als Gegner, auf `/play` als Bot. Je Partie neu gezogen aus allen geprüften Bots, nie gegen sich selbst; solche Anfragen bilden keine Serie (E162).

## Rating

Regel laut E103:

- Ein Punktestand je Bot und Disziplin, Start 2500 (seit E163; vorher einer über alle Disziplinen); jede Version beginnt neu. Ab M7 haben auch angemeldete Konten einen Stand.
- Gesamtrating: nach Partien gewichteter Durchschnitt über die Disziplinen, Σ(Rating · Partien) / Σ Partien (3000 bei 8 und 2000 bei 92 Partien ergibt 2080). Die Rangliste zeigt es unter „Gesamt“, dazu je Disziplin eine eigene (E163).
- Abstand d der Stände in der Disziplin vor der Partie, s = ⌊d / 20⌋. Sieg des Stärkeren: max(1, 50 − s). Sieg des Schwächeren: min(100, 50 + s). Remis: Der Schwächere bekommt min(50, s). Der Gegner verliert genau so viel.
- Es zählen nur Partien mit `rated` (Disziplin und Grundstellung). Freie Zeiten, andere Startstellungen, Remote-Partien, Partien gegen Gäste, kampflose Siege und abgebrochene Partien ändern nichts.
- Nur Statistik, kein Einfluss auf Auf- und Abstieg (E7).
- Der Runner verbucht die Partien in der Reihenfolge ihres Endes (E104); die Rangliste steht unter `/ratings`.
- Löscht ein Admin einen Bot mit verbuchten Partien, verbucht der Runner alle Ratings neu aus den verbliebenen Partien (E105).

| Stand vorher | Sieg A | Sieg B | Remis |
|--------------|--------|--------|-------|
| A 2500, B 2500 | 2550 / 2450 | 2450 / 2550 | unverändert |
| A 2800, B 2400 | 2830 / 2370 | 2730 / 2470 | 2780 / 2420 |
| A 3600, B 2500 | 3601 / 2499 | 3500 / 2600 | 3550 / 2550 |

## Spiel-Queue (E20)

Eine gemeinsame Queue für alle Spiele aller Wettbewerbe.

| Eigenschaft | Verhalten |
|-------------|-----------|
| Abarbeitung | Sobald ein Spiel endet, startet sofort das nächste; kein Leerlauf, keine festen Startzeiten |
| Parallelität | Anzahl gleichzeitiger Spiele einstellbar; Standard 1 (E12) |
| Reihenfolge | Nach Priorität des Wettbewerbs, innerhalb gleicher Priorität abwechselnd zwischen den Wettbewerben, damit kein Wettbewerb die Queue blockiert. Umgesetzt mit `competition` und `claimed_at` am Job: Bei gleicher Priorität kommt der Wettbewerb zum Zug, dessen letzter Abruf am längsten zurückliegt (E134) |
| Überschneidungen | Mehrere Ligen und Turniere dürfen gleichzeitig laufen; sie teilen sich die Queue |
| Bot-Sperre | Ein Bot spielt nie zwei Partien gleichzeitig (relevant bei Parallelität > 1) |
| Pausieren | Admin kann die Queue anhalten (z. B. wenn der Server anderweitig gebraucht wird); optional Zeitfenster, in denen keine Spiele starten |
| Eingriff | Admin kann Spiele vorziehen, zurückstellen, abbrechen, neu ansetzen |

### Geschätzte Startzeiten

- Für jedes wartende Spiel wird eine voraussichtliche Startzeit berechnet und online angezeigt.
- Grundlage: Position in der Queue und erwartete Dauer der davorliegenden Spiele (gleitender Durchschnitt der tatsächlichen Dauer je Disziplin, ersatzweise ein Anteil der Maximaldauer).
- Die Schätzung wird nach jedem beendeten Spiel neu berechnet und ist als Schätzung gekennzeichnet.

### Prioritäten (Standard, einstellbar)

Liga > Turnier > Einzelspiel > Verifikation. Spiele gegen Menschen und Remote-Bots laufen außerhalb dieser Reihenfolge mit eigener Kapazitätsgrenze (E24), weil ein wartender Mensch nicht hinter einer 60-Minuten-Partie anstehen kann; sie belegen dann zusätzlich Rechenzeit (R10).

Umgesetzt sind die Standardwerte Admin-Einzelspiele 100, Ligen 50, Einzelspiele der Coder 50, Turniere 40 (E172); Turniere stehen damit hinter den Einzelspielen. Je Wettbewerb ist die Priorität einstellbar.

### Überwachung

Hängende Spiele erkennen (Lease abgelaufen), neu ansetzen, im Adminbereich anzeigen. Genau eine aktive Scheduler-Instanz.

## Kapazitätsrechnung (R5)

- Zwei Spiele pro Paarung mit N Bots: N·(N−1) Partien.
- Eine Partie mit 30 min Grundzeit je Seite dauert maximal ~60 min plus Inkremente.
- Beispiel: 10 Bots → 90 Partien → bei einem Spiel gleichzeitig bis zu ~4 Tage pro Stufe, wenn jede Partie die Zeit ausschöpft.

Die Admin-Oberfläche zeigt beim Anlegen oder Ändern eines Wettbewerbs die geschätzte Gesamtlaufzeit und die Auswirkung auf die bestehende Queue.
