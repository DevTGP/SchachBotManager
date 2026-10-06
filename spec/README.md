# Spezifikation

Quelle der Wahrheit für Referee, SDKs und Doku. Änderungen erfolgen hier zuerst, danach im Code.

## Aufbau

| Pfad | Inhalt | Entscheidung |
|------|--------|--------------|
| `protocol/v<N>/<type>.schema.json` | Ein Schema je Nachrichtentyp der Protokollversion N | E36 |
| `protocol/v<N>/examples/valid/<type>.<fall>.json` | Gültige Beispielnachrichten | E36 |
| `protocol/v<N>/examples/invalid/<type>.<fall>.json` | Nachrichten, die der Referee ablehnen muss | E36 |
| `api/` | Kanonische, sprachneutrale Bot-API | E21, E39 |
| `testvectors/` | Perft, FEN, UCI, Regeln, API-Erwartungswerte | E37 |

## Regeln

- Alle Schemas nach JSON Schema 2020-12, ohne eigenes `$id`; Verweise zwischen Schemas über relative Pfade.
- Dokumente, die einem Schema folgen (API-Definition, Testvektoren), nennen es im Feld `$schema` als relativen Pfad.
- Beispielnachrichten tragen kein `$schema`, weil sie genau so über die Leitung gehen; ihr Schema ergibt sich aus dem Dateinamen.

## Prüfung

`tools/spec-check` prüft alle Dateien unter `spec/` und läuft in der CI:

- Jede Datei ist gültiges JSON.
- Jede `*.schema.json` ist ein gültiges Schema.
- Jedes Dokument mit relativem `$schema` erfüllt dieses Schema.
- Gültige Beispielnachrichten erfüllen das Schema ihres Typs, ungültige verletzen es.
