# Coding-Standards

Gilt für alle Pakete im Monorepo. Werkzeug-Konfigurationen liegen jeweils im Paket, sobald es entsteht.

## Allgemein

| Punkt | Regel |
|-------|-------|
| Sprache | Code, Bezeichner, Kommentare und Commit-Nachrichten auf Englisch; Doku auf Deutsch |
| Dateien | UTF-8, LF-Zeilenenden, abschließender Zeilenumbruch (`.editorconfig`, `.gitattributes`) |
| Aufteilung | Eine Datei, eine Verantwortung; keine Sammeldateien wie `utils` oder `helpers` |
| Tests | Jede Änderung mit Tests; CI ist das Merge-Gate |
| Commits | Imperativ, kurze Betreffzeile, thematisch getrennt |
| Secrets | Nie im Repo; nur `.env.example` mit Platzhaltern |

## Je Sprache

| Sprache | Version | Format / Lint | Tests |
|---------|---------|---------------|-------|
| C++ (Kern) | C++20, CMake (E38) | clang-format 19 (`sdk/core/.clang-format`: LLVM, 4 Leerzeichen, 100 Zeichen), Warnungen als Fehler (`-Wall -Wextra -Wpedantic -Werror` bzw. `/W4 /WX`) | Testvektoren aus `spec/testvectors/` und Unit-Tests über CTest (E56) |
| C (Schnittstelle des Kerns) | C11-kompatible Header | wie C++ | über die Bindings |
| Python (Werkzeuge, Backend, Dienste) | 3.12 | ruff (Lint und Format), Typannotationen | pytest |
| TypeScript (Frontend) | strict | ESLint, Prettier | ab M2 festgelegt |
| JSON (Spezifikation) | JSON Schema 2020-12 | 2 Leerzeichen Einrückung, von `tools/spec-check` geprüft; erzeugte Testvektoren mit einem Vektor je Zeile, Layout durch `tools/testvector-gen` festgelegt | – |

Die unterstützte Python-Spanne des Python-SDK wird in M1 festgelegt.
