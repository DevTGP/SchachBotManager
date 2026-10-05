# Statische Analyse

Zweite Schutzschicht neben der [Sandbox](sandbox.md) (E1). Zweck: Regelverstöße früh und mit verständlicher Meldung ablehnen, Angriffsfläche verkleinern. Sie ist prinzipiell umgehbar und daher nie alleinige Absicherung (R3).

## Gemeinsame Regeln (alle Sprachen)

| Regel | Umsetzung |
|-------|-----------|
| Nur freigegebene Bibliotheken | Import-/Include-Whitelist: Teilmenge der Standardbibliothek + SDK + explizit freigegebene Pakete (O7) |
| Keine Web-/Netzwerkzugriffe | Verbot der Netzwerk-APIs |
| Kein Dateizugriff | Verbot der Datei-APIs |
| Keine Prozesse, keine nativen Aufrufe | Verbot von Prozess-APIs, FFI, Inline-Assembler |
| Keine dynamische Codeausführung / Reflection | Verbot von `eval`-Mechanismen und Reflection-APIs |
| Keine manuelle Speicherverwaltung | Sprachspezifisch, siehe unten |
| Keine Threads | Solange A4 gilt |
| Größenlimits | Dateianzahl, Quellcodegröße, Artefaktgröße |
| SDK-Namensräume unantastbar | Upload darf SDK-Module nicht überschreiben oder patchen |

Die Regeln liegen als versionierte Konfiguration pro Sprache vor (Whitelist + Verbotsliste), nicht fest im Analyzer-Code. Der Report nennt Regel, Datei und Zeile.

## Pro Sprache

| Sprache | Analyseebene | Spezifische Verbote | Grenzen |
|---------|-------------|---------------------|---------|
| Python | AST des Quellcodes | `eval`, `exec`, `compile`, `__import__`, `open`, `ctypes`, Zugriff auf Dunder-Attribute (`__class__`, `__subclasses__`, `__globals__` …), `importlib`, `sys.modules` | Dynamik der Sprache erlaubt Umgehungen über Attributketten; Whitelist-Ansatz reduziert, beseitigt das nicht |
| C++ | Clang-AST nach dem Präprozessor | `new`/`delete`, `malloc`-Familie, Zeigerarithmetik, `reinterpret_cast`, C-Casts auf Zeiger, Inline-Assembler, `<fstream>`, `<filesystem>`, `<thread>`, `<cstdlib>`-Prozessfunktionen, POSIX-Header, `#pragma`/Attribute mit Linker-Wirkung | Speichersicherheit ist statisch nicht beweisbar (z. B. Indexzugriffe außerhalb von Containern, hängende Referenzen); erlaubt bleiben STL-Container und Smart Pointer über Factory-Funktionen |
| Java | Bytecode nach dem Build (referenzierte Klassen/Methoden) | `java.io`-Dateiklassen, `java.nio.file`, `java.net`, `java.lang.reflect`, `java.lang.invoke`, `Runtime`, `ProcessBuilder`, `ClassLoader`, `Unsafe`, `native`-Methoden, `Thread` | Bytecode-Prüfung ist verlässlicher als Quelltext-Prüfung; Reflection muss vollständig gesperrt sein, sonst wirkungslos |
| C# | Roslyn-Analyzer beim Build + Prüfung der referenzierten Assemblies | `unsafe` (Compiler-Option aus), `DllImport`/P/Invoke, `System.IO`, `System.Net`, `System.Reflection`, `System.Diagnostics.Process`, `System.Runtime.InteropServices`, `Span`-Tricks über `MemoryMarshal`, Threads/Tasks | Projektdatei wird vom Server gestellt, nicht vom Upload (sonst Build-Tasks als Angriffsweg) |
| JavaScript | AST des Quellcodes | `require`/`import` außer SDK, `eval`, `Function`-Konstruktor, `process`, `globalThis`-Zugriffe per berechnetem Schlüssel, `child_process`, `fs`, `net`, `worker_threads`, WebAssembly | Berechnete Eigenschaftszugriffe erlauben Umgehungen; zusätzlich Laufzeit-Rechtemodell von Node aktivieren |

## Zu „keine manuelle Speicherverwaltung“

| Sprache | Bedeutung |
|---------|-----------|
| Python, Java, JavaScript | Durch die Sprache gegeben; es bleiben nur FFI/`Unsafe` zu sperren |
| C# | `unsafe`, Zeiger, Interop sperren |
| C++ | Nur als Stilregel durchsetzbar (keine rohen Allokationen, keine Zeigerarithmetik). Echte Speichersicherheit kann die Analyse nicht garantieren; Fehlzugriffe führen in der Sandbox höchstens zum Absturz des eigenen Bots |

## Zu beachten

- **Fehlablehnungen** sind bei strikten Regeln unvermeidbar. Der Report muss so konkret sein, dass Autoren den Code anpassen können; ein Admin-Override pro Upload ist als Option vorzusehen.
- **Lokale Prüfung:** Derselbe Analyzer wird als CLI im SDK/Tooling ausgeliefert, damit Autoren vor dem Upload prüfen können.
- **Regeländerungen** betreffen nur neue Uploads; verifizierte Bots behalten ihren Status, bis ein Admin eine Neuprüfung auslöst.
- **Aufwand:** Fünf Analyzer sind neben den fünf SDK-Kernen der größte Einzelposten des Projekts; C++ ist am aufwendigsten.
