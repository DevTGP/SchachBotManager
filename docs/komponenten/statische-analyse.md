# Statische Analyse

Zweite Schutzschicht neben der [Sandbox](sandbox.md) (E1). Zweck: Regelverstöße früh und mit verständlicher Meldung ablehnen, Angriffsfläche verkleinern. Sie ist prinzipiell umgehbar und daher nie alleinige Absicherung (R3).

## Gemeinsame Regeln (alle Sprachen)

| Regel | Umsetzung |
|-------|-----------|
| Nur freigegebene Bibliotheken | Whitelist auf Typ-/Funktionsebene: Teilmenge der Standardbibliothek + SDK + freigegebene Pakete (siehe unten) |
| Keine Web-/Netzwerkzugriffe | Verbot der Netzwerk-APIs |
| Kein Dateizugriff | Verbot der Datei-APIs; hochgeladene Datendateien sind nur über `load_data` des SDK erreichbar (E30) |
| Keine Prozesse, keine nativen Aufrufe | Verbot von Prozess-APIs, FFI, Inline-Assembler. Einzige Ausnahme ist das serverseitig gestellte SDK, das den C++-Kern anbindet; es wird nicht analysiert, da es nicht aus dem Upload stammt |
| Keine dynamische Codeausführung / Reflection | Verbot von `eval`-Mechanismen und Reflection-APIs |
| Keine manuelle Speicherverwaltung | Sprachspezifisch, siehe unten |
| Keine Threads | Solange A4 gilt |
| Größenlimits | Dateianzahl, Quellcodegröße, Artefaktgröße |
| SDK-Namensräume unantastbar | Upload darf SDK-Module nicht überschreiben oder patchen |

Die Analyse erfasst alle Quelldateien eines Uploads; Importe sind nur auf Whitelist-Module, das SDK und eigene Dateien des Uploads erlaubt.

Die Regeln liegen als versionierte Konfiguration pro Sprache vor (Whitelist + Verbotsliste), nicht fest im Analyzer-Code. Der Report nennt Regel, Datei und Zeile.

## Python (umgesetzt, E90)

| Teil | Umsetzung |
|------|-----------|
| Paket | `sbm.analysis` im Python-SDK; Regeln in `python_rules.json`, Regelsatz `python-1` im Report |
| Eingabe | Alle Quelldateien des Uploads als AST, nichts wird importiert; Dateien müssen UTF-8 sein |
| Importe | Whitelist (unten, ohne numpy) plus `sbm`, `__future__`, `collections.abc` und die eigenen Module; `sitecustomize` und `usercustomize` sind als eigene Module verboten |
| Verbotene Builtins | `eval`, `exec`, `compile`, `__import__`, `open`, `getattr`, `setattr`, `delattr`, `globals`, `locals`, `vars`, `breakpoint`, `input`, `help`, `exit`, `quit` |
| Dunder | Verboten bis auf `__name__` (lesen), `__all__` und `__slots__` (zuweisen), `.__init__` und den Text `"__main__"`; auch in Zeichenketten gemeldet |
| Private Attribute | `_x` nur an `self`, `cls`, `super()` und eigenen Modulen |
| Umwege | Frame-, Code- und Traceback-Attribute (`f_globals`, `gi_frame`, `tb_frame` …), `attrgetter`, `methodcaller`, `get_type_hints`, `ForwardRef` |
| Module | Kein Modul als Wert (etwa als Argument); Attribute, die zu Modulen außerhalb der Whitelist führen (`random._os`, `dataclasses.sys`), werden über Importe, Stern-Importe und eigene Module verfolgt |
| Report | Regel, Datei, Zeile, Meldung; höchstens 100 Befunde, danach `truncated` |
| Lokal | `sbm-check [ordner] [--entry bot.py] [--exclude GLOB] [--json]`; wählt die Dateien wie die Upload-Seite, Exit-Code 0 ohne Befund, 1 mit Befunden, 2 bei falschen Argumenten |
| Auf dem Server | Der Runner startet `python -I -m sbm.analysis --json --entry … /bot` in der Sandbox mit höchstens 60 s und prüft die Ausgabe, bevor sie in den Report kommt ([verifikation.md](verifikation.md)) |

## Pro Sprache

| Sprache | Analyseebene | Spezifische Verbote | Grenzen |
|---------|-------------|---------------------|---------|
| Python | AST des Quellcodes | `eval`, `exec`, `compile`, `__import__`, `open`, `ctypes`, Zugriff auf Dunder-Attribute (`__class__`, `__subclasses__`, `__globals__` …), `importlib`, `sys.modules` | Dynamik der Sprache erlaubt Umgehungen über Attributketten; Whitelist-Ansatz reduziert, beseitigt das nicht |
| C++ | Clang-AST nach dem Präprozessor | `new`/`delete`, `malloc`-Familie, Zeigerarithmetik, `reinterpret_cast`, C-Casts auf Zeiger, Inline-Assembler, `<fstream>`, `<filesystem>`, `<thread>`, `<cstdlib>`-Prozessfunktionen, POSIX-Header, `#pragma`/Attribute mit Linker-Wirkung | Speichersicherheit ist statisch nicht beweisbar (z. B. Indexzugriffe außerhalb von Containern, hängende Referenzen); erlaubt bleiben STL-Container und Smart Pointer über Factory-Funktionen |
| Java | Bytecode nach dem Build (referenzierte Klassen/Methoden) | `java.io`-Dateiklassen, `java.nio.file`, `java.net`, `java.lang.reflect`, `java.lang.invoke`, `Runtime`, `ProcessBuilder`, `ClassLoader`, `Unsafe`, `native`-Methoden, `Thread` | Bytecode-Prüfung ist verlässlicher als Quelltext-Prüfung; Reflection muss vollständig gesperrt sein, sonst wirkungslos |
| C# | Roslyn-Analyzer beim Build + Prüfung der referenzierten Assemblies | `unsafe` (Compiler-Option aus), `DllImport`/P/Invoke, `System.IO`, `System.Net`, `System.Reflection`, `System.Diagnostics.Process`, `System.Runtime.InteropServices`, `Span`-Tricks über `MemoryMarshal`, Threads/Tasks | Projektdatei wird vom Server gestellt, nicht vom Upload (sonst Build-Tasks als Angriffsweg) |
| JavaScript | AST des Quellcodes | `require`/`import` außer SDK, `eval`, `Function`-Konstruktor, `process`, `globalThis`-Zugriffe per berechnetem Schlüssel, `child_process`, `fs`, `net`, `worker_threads`, WebAssembly | Berechnete Eigenschaftszugriffe erlauben Umgehungen; zusätzlich Laufzeit-Rechtemodell von Node aktivieren |

## Freigegebene Bibliotheken (E16)

| Sprache | Standardbibliothek | Zusätzlich |
|---------|--------------------|------------|
| Python | `math`, `random`, `itertools`, `functools`, `collections`, `heapq`, `bisect`, `dataclasses`, `enum`, `typing`, `array`, `operator`, `copy`, `time` | `numpy` (noch nicht in der Laufzeit, O20) |
| C++ | `<vector>`, `<array>`, `<algorithm>`, `<bit>`, `<cstdint>`, `<unordered_map>`, `<map>`, `<string>`, `<string_view>`, `<optional>`, `<random>`, `<chrono>`, `<numeric>`, `<limits>`, `<memory>` (nur Smart Pointer), `<bitset>`, `<cmath>`, `<span>`, `<tuple>` | – |
| Java | `java.util`, `java.util.function`, `java.util.stream`; aus `java.lang` nur `Math`, `Long`, `Integer`, `String`, `StringBuilder`, `System.nanoTime` und die Basistypen | – |
| C# | `System.Collections.Generic`, `System.Linq`, `System.Numerics` (`BitOperations`), `System.Text`; aus `System.Diagnostics` nur `Stopwatch` | – |
| JavaScript | Nur Built-ins: `Math`, `BigInt`, Typed Arrays, `Map`, `Set`, `performance.now` | Keine npm-Pakete |

Die Liste liegt als versionierte Konfiguration vor und ist erweiterbar; jede Erweiterung braucht eine neue Version des Laufzeitverzeichnisses, wenn ein Paket hinzukommt.

## Zu „keine manuelle Speicherverwaltung“

| Sprache | Bedeutung |
|---------|-----------|
| Python, Java, JavaScript | Durch die Sprache gegeben; es bleiben nur FFI/`Unsafe` zu sperren |
| C# | `unsafe`, Zeiger, Interop sperren |
| C++ | Nur als Stilregel durchsetzbar (keine rohen Allokationen, keine Zeigerarithmetik). Echte Speichersicherheit kann die Analyse nicht garantieren; Fehlzugriffe führen in der Sandbox höchstens zum Absturz des eigenen Bots |

## Zu beachten

- **Fehlablehnungen** sind bei strikten Regeln unvermeidbar. Der Report muss so konkret sein, dass Autoren den Code anpassen können; ein Admin kann jede Ablehnung per Override aufheben (E153).
- **Lokale Prüfung:** Derselbe Analyzer wird als CLI im SDK/Tooling ausgeliefert, damit Autoren vor dem Upload prüfen können; für Python ist das `sbm-check`.
- **Regeländerungen** betreffen nur neue Uploads; verifizierte Bots behalten ihren Status. Eine Neuprüfung durch einen Admin zeigt, wie ein Bot mit den aktuellen Regeln abschneidet, ändert den Status aber nicht (E153); sperren muss der Admin selbst.
- **Aufwand:** Fünf Analyzer sind neben den fünf SDK-Kernen der größte Einzelposten des Projekts; C++ ist am aufwendigsten.
