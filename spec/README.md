# Spezifikation

Quelle der Wahrheit für Referee, SDKs und Doku. Änderungen erfolgen hier zuerst, danach im Code.

## Aufbau

| Pfad | Inhalt | Entscheidung |
|------|--------|--------------|
| `protocol/v<N>/<type>.schema.json` | Ein Schema je Nachrichtentyp der Protokollversion N | E36 |
| `protocol/v<N>/common.schema.json` | Gemeinsame Definitionen (Version, UCI, FEN, Farbe, Zeiten) | E36 |
| `protocol/v<N>/bot_message.schema.json`, `referee_message.schema.json` | Jede Nachricht einer Richtung; der Referee prüft jede Zeile eines Bots gegen `bot_message` | E36 |
| `protocol/v<N>/examples/valid/<type>.<fall>.json` | Gültige Beispielnachrichten | E36 |
| `protocol/v<N>/examples/invalid/<type>.<fall>.json` | Nachrichten, die gegen das Schema verstoßen; je Datei genau ein Verstoß | E36 |
| `api/api.schema.json` | Schema der API-Dateien | E39 |
| `api/<modul>.json` | Kanonische, sprachneutrale Bot-API, je Thema eine Datei (Grundtypen, Typen, Konstanten, Fehler, `Move`, `Board` in Gruppen, `Clock`, `Bot`, `Log`, Laufzeit) | E21, E39, E45–E49 |
| `testvectors/` | Perft, FEN, UCI, Regeln, API-Erwartungswerte | E37 |

## Regeln

- Alle Schemas nach JSON Schema 2020-12, ohne eigenes `$id`; Verweise zwischen Schemas über relative Pfade.
- Dokumente, die einem Schema folgen (API-Definition, Testvektoren), nennen es im Feld `$schema` als relativen Pfad.
- Beispielnachrichten tragen kein `$schema`, weil sie genau so über die Leitung gehen; ihr Schema ergibt sich aus dem Dateinamen. Sie stehen als einzelne kompakte JSON-Zeile in der Datei.
- API-Dateien nennen `api.schema.json` als `$schema`, und ihr Feld `module` entspricht dem Dateinamen. Namen sind kanonisch: `snake_case` für Funktionen, Felder und Parameter, `PascalCase` für Typen und Fehler, `UPPER_SNAKE` für Konstanten (E47). Jedes Binding übersetzt sie in die Schreibweise seiner Sprache.
- Reguläre Ausdrücke in `pattern` müssen in allen fünf Sprachen gleich prüfen: `[0-9]` statt `\d` (Python erkennt mit `\d` auch andere Ziffern) und `(?!\n)$` statt `$` am Ende (in Python passt `$` auch vor einem abschließenden Zeilenumbruch).

## Prüfung

`tools/spec-check` prüft alle Dateien unter `spec/` und läuft in der CI:

- Jede Datei ist gültiges JSON.
- Jede `*.schema.json` ist ein gültiges Schema.
- Jedes `pattern` folgt der Regel für reguläre Ausdrücke oben.
- Jedes Dokument mit relativem `$schema` erfüllt dieses Schema.
- Gültige Beispielnachrichten erfüllen das Schema ihres Typs, ungültige verletzen es.
