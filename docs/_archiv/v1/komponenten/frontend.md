# Frontend (SPA)

Eigenständige Anwendung (E5), spricht ausschließlich mit der [Flask-API](backend-api.md). Framework offen (O1).

## Bereiche

| Bereich | Inhalt |
|---------|--------|
| Start | Laufende Spiele, zuletzt beendete Partien, aktuelle Saisons |
| Partie-Viewer | siehe unten |
| Ligen | Stufen, Tabellen, Spielplan, Auf-/Abstiegszonen, frühere Saisons |
| Turniere | Teilnehmer, Runden, Tabelle bzw. K.-o.-Baum |
| Bot-Profil | Stammdaten, Besitzer, Sprache, Versionen der Abstammung, Rating-Verlauf, Liga-Verlauf, vollständige Partienliste mit Filtern, Statistik (Bilanz nach Farbe/Gegner/Endgrund) |
| Mein Bereich (Coder) | Eigene Bots, Upload, Verifikationsstatus und Report, Logs eigener Bots, Anmeldungen, API-Tokens, Einzelspiele ansetzen |
| Spielen | Bot auswählen, Farbe/Zeitkontrolle, Partie gegen den Bot |
| Admin | Nutzer & Invites, Bots (alle), Disziplinen, Ligen, Turniere, Job-Queue/Systemstatus, Audit-Log |

## Partie-Viewer

| Funktion | Detail |
|----------|--------|
| Brett | Figuren, letzter Zug markiert, Brett drehbar, Koordinaten |
| Navigation | Anfang/Ende, vor/zurück, Klick in die Zugliste, Tastatur |
| Wiedergabe | Play/Pause, mehrere Geschwindigkeiten (feste Faktoren und „Echtzeit“ anhand der gespeicherten Zugzeiten) |
| Uhren | Restzeit beider Seiten zum jeweiligen Zug |
| Zugliste | SAN-Notation, verbrauchte Zeit pro Zug |
| Metadaten | Bots, Versionen, Disziplin, Ergebnis, Endgrund, Wettbewerb |
| Zusatz | Optionale Bot-`info` (Bewertung/Tiefe) als Verlauf, geschlagene Figuren/Materialbilanz |
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
- **Admin-Formulare** für Ligen/Disziplinen mit Validierung und Laufzeitschätzung (siehe [ligen-turniere.md](ligen-turniere.md)).
- **Auslieferung:** Statischer Build, vom Reverse Proxy ausgeliefert; API unter eigenem Pfad (`/api`), dadurch gleicher Ursprung und kein CORS nötig.
- **Tests:** Komponententests für den Viewer, wenige End-to-End-Tests für Login, Upload, Viewer.
