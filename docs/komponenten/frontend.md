# Frontend (SPA)

Eigenständige Anwendung (E5) in React + TypeScript, gebaut mit Vite (E9). Spricht ausschließlich mit der [Flask-API](backend-api.md). Alle Ansichten außer „Mein Bereich“ und „Admin“ sind ohne Login zugänglich (E10).

## Sprachen (E32)

Deutsch und Englisch. Alle Texte liegen von Beginn an in Übersetzungsdateien; Sprachwahl nach Browser-Einstellung mit Umschalter, die Wahl bleibt gespeichert. Fehlermeldungen der API kommen als Codes und werden im Frontend übersetzt; das gilt auch für Endgründe von Partien und Meldungen der Verifikation.

## Bereiche

| Bereich | Inhalt |
|---------|--------|
| Start | Laufende Spiele, zuletzt beendete Partien, aktuelle Saisons |
| Queue | Wartende Spiele in Reihenfolge mit geschätzter Startzeit, Wettbewerb und Disziplin |
| Partie-Viewer | siehe unten |
| Ligen | Stufen, Tabellen, Spielplan, Auf-/Abstiegszonen, frühere Saisons |
| Turniere | Teilnehmer, Runden, Tabelle bzw. K.-o.-Baum |
| Bot-Profil | Stammdaten, Besitzer, Sprache, Versionen der Abstammung, Rating-Verlauf, Liga-Verlauf, vollständige Partienliste mit Filtern, Statistik (Bilanz nach Farbe/Gegner/Endgrund) |
| Mein Bereich (Coder) | Eigene Bots, Upload, Verifikationsstatus und Report, Logs eigener Bots, Anmeldungen, API-Tokens, Einzelspiele ansetzen |
| Spielen | Für jeden Besucher (E11): Bot auswählen, Farbe/Zeitkontrolle, Partie gegen den Bot |
| Admin | Nutzer & Invites, Bots (alle), Disziplinen, Ligen, Turniere, Queue-Steuerung (pausieren, umsortieren, Parallelität, Zeitfenster), Systemeinstellungen und Limits, Systemstatus, Audit-Log |

## Partie-Viewer

| Funktion | Detail |
|----------|--------|
| Brett | Figuren, letzter Zug markiert, Brett drehbar, Koordinaten |
| Navigation | Anfang/Ende, vor/zurück, Klick in die Zugliste, Tastatur |
| Wiedergabe | Play/Pause, mehrere Geschwindigkeiten (feste Faktoren und „Echtzeit“ anhand der gespeicherten Zugzeiten) |
| Uhren | Restzeit beider Seiten zum jeweiligen Zug |
| Zugliste | SAN-Notation, verbrauchte Zeit pro Zug |
| Metadaten | Bots, Versionen, Disziplin, Ergebnis, Endgrund, Wettbewerb |
| Zusatz | Bot-`info` (Bewertung/Tiefe) als Verlauf, öffentlich sichtbar (E33), geschlagene Figuren/Materialbilanz |
| Live | Laufende Partien aktualisieren sich über den Live-Kanal; Wechsel zwischen „live folgen“ und freiem Blättern |
| Export | PGN, FEN der aktuellen Stellung, teilbarer Link auf Partie + Zugnummer |

Der Viewer rendert nur gespeicherte Stellungen (FEN pro Zug) und braucht keine eigene Regelimplementierung.

## Mensch gegen Bot

- Zugeingabe per Drag-and-drop/Klick; legale Züge kommen vom Server oder aus einer Client-Schachbibliothek (nur Komfort – der Server prüft immer).
- Umwandlungsdialog, Aufgabe, Anzeige der Bot-Bedenkzeit.
- Verbindungsabbruch: Wiederaufnahme innerhalb einer Frist, danach Abbruch.

## Zu beachten

- **Zustand über URLs:** Jede Ansicht (Partie, Zugnummer, Saison, Filter) ist verlinkbar.
- **Rechte in der UI sind nur Komfort**; maßgeblich ist die API.
- **Große Listen** paginiert/virtuell.
- **Upload-Rückmeldung:** Pipeline-Status schrittweise anzeigen, Report mit Datei/Zeile.
- **Kampflose Siege (E17)** in Tabellen und Partienlisten eigens kennzeichnen; zurückgezogene Bots in der Saisonansicht ausweisen.
- **Brett-Komponente:** Bei Fremdbibliotheken die Lizenz prüfen (einige verbreitete Schachbrett-Komponenten stehen unter GPL).
- **Admin-Formulare** für jede Einstellung (E13) mit Validierung und Laufzeitschätzung (siehe [ligen-turniere.md](ligen-turniere.md)).
- **Auslieferung:** Statischer Build im `frontend`-Container, der auch `/api` und WebSocket an die API weiterreicht; der Nginx Proxy Manager zeigt nur auf diesen Container (E29). Gleicher Ursprung, kein CORS nötig.
- **Tests:** Komponententests für den Viewer, wenige End-to-End-Tests für Login, Upload, Viewer.
