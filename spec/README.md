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
| `api/` | Kanonische, sprachneutrale Bot-API | E21, E39 |
| `testvectors/` | Perft, FEN, UCI, Regeln, API-Erwartungswerte | E37 |

## Regeln

- Alle Schemas nach JSON Schema 2020-12, ohne eigenes `$id`; Verweise zwischen Schemas über relative Pfade.
- Dokumente, die einem Schema folgen (API-Definition, Testvektoren), nennen es im Feld `$schema` als relativen Pfad.
- Beispielnachrichten tragen kein `$schema`, weil sie genau so über die Leitung gehen; ihr Schema ergibt sich aus dem Dateinamen. Sie stehen als einzelne kompakte JSON-Zeile in der Datei.
- Reguläre Ausdrücke in `pattern` müssen in allen fünf Sprachen gleich prüfen: `[0-9]` statt `\d` (Python erkennt mit `\d` auch andere Ziffern) und `(?!\n)$` statt `$` am Ende (in Python passt `$` auch vor einem abschließenden Zeilenumbruch).

## Prüfung

`tools/spec-check` prüft alle Dateien unter `spec/` und läuft in der CI:

- Jede Datei ist gültiges JSON.
- Jede `*.schema.json` ist ein gültiges Schema.
- Jedes `pattern` folgt der Regel für reguläre Ausdrücke oben.
- Jedes Dokument mit relativem `$schema` erfüllt dieses Schema.
- Gültige Beispielnachrichten erfüllen das Schema ihres Typs, ungültige verletzen es.
