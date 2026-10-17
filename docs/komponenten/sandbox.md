# Sandbox

Die eigentliche Sicherheitsgrenze. Sie muss den Server auch dann schützen, wenn die [statische Analyse](statische-analyse.md) vollständig umgangen wird (R3).

Gewählt: **nsjail** (E18) – ein einzelnes Programm, das einen Prozess direkt in Linux-Namespaces, cgroups und einem seccomp-Filter startet. Kein Daemon, kein Docker.

## Schutzziele

| Ziel | Mittel |
|------|--------|
| Kein Datenabfluss | Kein Netzwerk, kein Zugriff auf Host-Dateien, DB oder andere Bots |
| Kein Schaden am Server | Ressourcenlimits, keine Privilegien, kein persistenter Schreibzugriff |
| Keine Beeinflussung des Gegners | Getrennte Sandboxes |
| Vergleichbare Bedingungen | Gleiche feste Schutzgrenzen für alle Sprachen (E8) |

## Konfiguration je Bot-Prozess

| Bereich | Einstellung |
|---------|-------------|
| Netzwerk | Eigener, leerer Netzwerk-Namespace |
| Dateisystem | Laufzeitverzeichnis der Sprache und Bot-Artefakt read-only eingehängt; sonst nichts sichtbar; kein Schreibbereich |
| Benutzer | Eigener User-Namespace, unprivilegierte ID |
| Prozesse | Eigener PID-Namespace, PID-Limit (gegen Fork-Bomben, begrenzt Threads) |
| Syscalls | seccomp-Whitelist je Laufzeitumgebung |
| Speicher | cgroup-Limit, kein Swap → Überschreitung beendet den Prozess (`memory_limit`) |
| CPU | cgroup: fester Kern und hohe Gewichtung gegenüber anderen Diensten (konfigurierbar) |
| Ausgabe | stdout/stderr als Pipes zum Runner, mengenbegrenzt |
| Lebensdauer | Ein Prozess pro Bot pro Spiel |

Eine Konfigurationsdatei je Sprache im Repo (`sandbox/<sprache>.cfg`) mit festen Schutzgrenzen. Diese Grenzen sind kein Spielparameter und nicht über die Website einstellbar (E23, A14).

## Warum der Overhead klein bleibt

| Aspekt | Wirkung |
|--------|---------|
| Rechenlast | Läuft nativ auf der CPU; Namespaces und cgroups kosten bei reiner Berechnung praktisch nichts |
| Syscalls | seccomp prüft jeden Aufruf mit einem kurzen Filter; Schachbots machen pro Zug nur wenige Aufrufe (lesen, schreiben, Zeit) |
| Start | Wenige Millisekunden für nsjail selbst; die Laufzeitumgebung (JVM, .NET, Node, Python) dominiert und fällt ins Startbudget, nicht in die Bedenkzeit |
| Kommunikation | Direkte Pipes zwischen Runner und Bot, kein Zwischendienst |
| Einfrieren | Schreiben in `cgroup.freeze`; deutlich unter einer Millisekunde |
| Ein Prozess pro Spiel | Kein Neustart pro Zug; JIT-Aufwärmung und Tabellen bleiben erhalten |

## Laufzeitverzeichnisse statt Images

- Pro Sprache ein vorbereitetes Verzeichnis im `runner`-Image mit Laufzeit, SDK (inklusive Kern-Bibliothek) und freigegebenen Bibliotheken; read-only in die Sandbox eingehängt.
- Datendateien eines Bots (E30) liegen neben dem Artefakt und sind ebenfalls nur lesbar.
- Getrennt davon ein **Build-Verzeichnis** mit Compiler und Analyzer.
- Beide entstehen beim Image-Build, sind versioniert (Version am Bot gespeichert); Laufzeiten in der jeweils aktuellen stabilen Version, dann gepinnt (E31).
- **Auch der Build ist nicht vertrauenswürdig** und läuft in derselben Sandbox mit Zeitlimit und einem begrenzten Schreibbereich für das Ergebnis.

## Schutzgrenzen statt Disziplin-Limits (E23)

| Grenze | Zweck | Durchsetzung |
|--------|-------|-------------|
| Speicher | Schutz des Servers, großzügig bemessen | cgroup |
| Prozesse/Threads | Gegen Fork-Bomben | PID-Limit |
| Ausgabemenge | Gegen volle Platten/Pipes | Runner |
| Quellcode-/Artefaktgröße | Gegen übergroße Uploads | [Verifikation](verifikation.md) |
| Bedenkzeit (Wanduhr, E19) | Spielregel der Disziplin | [Match-Runner](match-runner.md) |

Konfigurierbare Ressourcenlimits als Wettbewerbsmerkmal sind zurückgestellt. Falls sie später kommen, ist zu bedenken: Ein Speicherlimit gilt für den ganzen Prozess, und Laufzeitumgebungen haben unterschiedlichen Grundverbrauch (JVM, .NET, Node deutlich mehr als C++).

JVM, .NET und Node müssen schon jetzt auf die feste Speichergrenze eingestellt werden (Heap-Obergrenze), damit sie nicht unkontrolliert beendet werden.

## Rechte des Runners (R4, A13)

- nsjail muss Namespaces und cgroups anlegen können. Der Runner führt Partien und Verifikation aus (E81), läuft als Container im Compose-Stack und bekommt dafür gezielte Rechte statt `privileged` (E87): root im Container, nur `SYS_ADMIN`, `SETUID` und `SETGID`, seccomp und AppArmor des Containers aus, eigener cgroup-Namespace, `no-new-privileges`.
- Folge: Ein Fehler im Runner selbst wirkt wie Root auf dem Host. Der Runner führt deshalb nie Bot-Code außerhalb von nsjail aus, hängt nicht am Proxy-Netz und nimmt Aufträge nur über die DB an.
- Die Web-API hat keinerlei Möglichkeit, Prozesse zu starten.
- Alle Sandbox-Optionen stehen fest in den Konfigurationsdateien; aus Job-Daten kommt nur die Bot-ID.

## Zu beachten

- **Kernel-Voraussetzungen:** cgroup v2 auf dem Host (bei aktuellem Ubuntu Standard); der Container braucht Schreibzugriff auf seinen cgroup-Zweig, sonst funktionieren Limits und Einfrieren nicht.
- **Gemeinsamer Kernel:** Die Isolation teilt den Host-Kernel; ein Kernel-Fehler wäre ein Ausbruchsweg. Für den Nutzerkreis (Freunde, Invite-only) als ausreichend eingestuft; aktuelle Kernel-Updates bleiben relevant.
- **seccomp-Whitelists je Laufzeit** müssen einmal ermittelt und bei Laufzeit-Updates geprüft werden (JVM und .NET nutzen mehr Aufrufe als CPython).
- **Aufräumen:** Beim Runner-Start verwaiste cgroups/Prozesse entfernen.
- **Negativ-Tests:** Testbots für Netz, Datei, Fork-Bombe, Speicher, Endlosschleife, übergroße Ausgabe laufen in CI gegen die Sandbox (E88); für C# dieselben Angriffe als kompilierte Programme (E205).

## Stand M3 Schritt 2 (E86–E88)

Umgesetzt für Python und seit E227 für JavaScript; die übrigen Sprachen folgen mit ihren SDKs nach demselben Muster (eigene `sandbox/<sprache>.cfg`, eigene Whitelist, eigenes Laufzeitverzeichnis unter `/opt/sbm/runtimes/<sprache>`).

| Datei | Inhalt |
|-------|--------|
| `sandbox/python.cfg` | nsjail-Konfiguration eines Python-Bots: Namespaces, Nutzer-Abbildung, Umgebung, Mounts, rlimits; setzt `SBM_NO_VIEWER`, damit kein Viewer-Fenster aufgeht (E108) |
| `sandbox/python.policy` | seccomp-Whitelist in kafel-Syntax; erlaubt `restart_syscall`, damit ein Warten mit Zeitgrenze nach dem Auftauen weiterläuft |
| `sandbox/javascript.cfg`, `sandbox/javascript.policy` | Dasselbe für Node (E227) mit derselben Whitelist |
| `services/runner/src/sbm_runner/sandbox/` | `settings` (`SBM_SANDBOX`), `runtimes` (Start, Selbstprüfung, Analyse bzw. Build und Konfiguration je Sprache, E205, E227), `limits` (feste Grenzen), `cgroup_tree` (Aufteilung des Baums beim Start), `cgroup` (cgroup eines Bots), `jail_player` (Spieler über nsjail), `stderr_tail`, `jail` (Selbstprüfung, Spieler je Bot) |
| `services/runner/tests/sandbox/` | Negativ-Suite mit Testbots, `suite.Dockerfile` (Runner-Image plus die mit dem .NET-SDK gebauten C#-Testbots) und `run-in-docker.sh` |

**Feste Grenzen** (`limits.py`, A14): 1 GiB Speicher ohne Swap, 128 Prozesse und Threads, 256 Dateideskriptoren (bis E205 64), keine beschreibbare Datei außer `/dev/null`, für Python kein `/dev/urandom` (Zufall über `getrandom`), Zeilen bis 64 KiB, von stderr bleiben die letzten 4 KiB im Log des Runners.

**Ablauf eines Bots:** Runner legt `bots/bot-<zufall>/` mit den Grenzen an → `sh` schreibt sich in deren `cgroup.procs` und wird zu nsjail → nsjail baut die Namespaces, hängt Laufzeit und Bot-Dateien ein, setzt den seccomp-Filter und startet `python3`. Außerhalb seines Zuges ist die cgroup eingefroren. Am Ende: auftauen, stdin schließen, nach `game_over` bis 2 s warten, `cgroup.kill`, cgroup entfernen.

**Endet ein Bot:** Zählt `memory.events` einen OOM-Kill, ist das Ende `memory_limit`, sonst `crash` mit dem Exit-Code. stderr landet nur im Log des Runners, gespeichert wird es noch nicht (O19).

**Lokal:** Unter Windows und ohne Runner-Image gilt `SBM_SANDBOX=none`; dann spielen nur die Referenzbots als gewöhnliche Prozesse. Die Negativ-Suite braucht einen Linux-Host mit cgroup v2 (`bash services/runner/tests/sandbox/run-in-docker.sh`); Docker Desktop unter WSL2 bietet nur cgroup v1.

**Offen:** Fester Kern und CPU-Gewichtung (siehe [match-runner.md](match-runner.md)) sind noch nicht umgesetzt; der Bot läuft mit derselben Priorität wie der Runner.

## Stand M3 Schritt 3 (E90, E92, E94)

- **Dateien eines Uploads:** `checkout.py` schreibt sie für jede Analyse, jeden Test und jede Partie in ein neues Verzeichnis unter `/tmp/sbm-bots` (Verzeichnisse 0755, Dateien 0644), prüft dabei Pfad, Art und SHA-256 erneut und löscht es danach. nsjail hängt es als `/bot` ein (read-only, `noexec`); der Bot startet mit `python /bot/<entry>`.
- **Analyse in der Sandbox:** `sandbox/run_once.py` startet einen Befehl, der bis zu seinem Ende läuft, in derselben Umgebung wie einen Bot: die Selbstprüfung und `python -I -m sbm.analysis --json --entry … /bot` bzw. für JavaScript `node <Flags> /node_modules/schachbotmanager/dist/analysis/bin.js --json --entry … /bot` (höchstens 60 s, Ausgabe höchstens 1 MiB).
- **Selbstprüfung:** Sie läuft beim Start des Runners für jede Laufzeit und meldet die Versionen von Python bzw. Node und SDK als JSON; der Runner trägt sie in Report und Bot ein.
- **stderr:** Zusätzlich zu den letzten 4 KiB zählt der Runner die Gesamtmenge; über 1 MiB scheitert ein Mindesttest (E92).

## Stand M5 Schritt 4: C# (E203–E205)

| Datei | Inhalt |
|-------|--------|
| `sandbox/csharp.cfg` | nsjail-Konfiguration eines C#-Bots und von `sbm-build`: wie Python, dazu .NET-Umgebung (invariante Globalisierung, keine Diagnose, `DOTNET_GCHeapHardLimit` 768 MiB), `/dev/urandom` read-only und das Programm als `/program` (read-only, `noexec`) |
| `sandbox/csharp.policy` | seccomp-Whitelist wie Python, zusätzlich `membarrier` (drei Befehle) und `sched_setaffinity` für den eigenen Prozess; `open`/`openat` nur mit `O_RDONLY`, weil `/dev/urandom` trotz read-only-Mount beschreibbar wäre |
| `services/runner/src/sbm_runner/sandbox/runtimes.py` | je Sprache Konfiguration, Startbefehl, Selbstprüfung und Build |
| `sdk/csharp/server/Sbm.Host/sbm-host.c` | nativer Starter: hostfxr in einem zweiten Thread mit 8 MiB Stack, weil glibc ohne `/proc` den Stack des Hauptthreads nicht bestimmen kann |

**Laufzeitverzeichnis** `/opt/sbm/runtimes/csharp` (Stufe `bot-csharp` in `deploy/python.Dockerfile`): .NET-Runtime 10.0.13 ohne SDK, darin `/sbm/host`, `/sbm/build/sbm-build.dll`, `/sbm/launch/sbm-launch.dll` und die Referenz-Assemblies unter `/sbm/refs/net` und `/sbm/refs/sdk`. Gebaut wird in der Stufe `bot-csharp-build` mit dem .NET-SDK 10.0.402; ins Runner-Image kommt nur das Ergebnis.

**Ablauf:** Bei der Verifikation läuft `/sbm/host /sbm/build/sbm-build.dll --entry … --references /sbm/refs/net --references /sbm/refs/sdk /bot` in der Sandbox (höchstens 120 s, Ausgabe höchstens 16 MiB, `/program` leer). Für jeden Test und jede Partie schreibt `checkout.py` das gespeicherte Programm in ein eigenes Verzeichnis (Hash geprüft), nsjail hängt es als `/program` ein, und `/sbm/host /sbm/launch/sbm-launch.dll` lädt es aus dem Speicher. Die Selbstprüfung startet den Launcher mit `--versions`.

**Speicher:** Verwalteter Speicher endet an `DOTNET_GCHeapHardLimit` mit einer `OutOfMemoryException` unterhalb der cgroup-Grenze, also als `crash`; nativer Speicher (`NativeMemory.Alloc`) läuft bis zur cgroup-Grenze und endet als `memory_limit`. Beides prüft die Negativ-Suite.

**Negativ-Suite für C#** (`test_sandbox_csharp.py`, `test_sandbox_verification_csharp.py`): Die Testbots unter `services/runner/tests/sandbox/bots/csharp/` (Netz, Dateien, Prozesse, Systemaufrufe, Threads, verwalteter und nativer Speicher) baut `suite.Dockerfile` mit dem .NET-SDK und legt sie als Programme neben das Runner-Image; sie laufen wie hochgeladene Bots über den Launcher. Dazu `sbm-build` in der echten Sandbox: `csharp_forbidden` scheitert an der Analyse, `csharp_uploaded` wird kompiliert, liest seine Datendatei und besteht die Mindesttests.

## Stand JavaScript (E227)

- **Laufzeit:** Read-only-Wurzelbaum `/opt/sbm/runtimes/javascript` aus `node:24.22.0-trixie-slim` mit `/usr/local/bin/node`, den nötigen Bibliotheken und dem npm-Paket samt Addon unter `/node_modules/schachbotmanager`. acorn liegt verschachtelt im Paket, ein Bot findet also nur das SDK. Ohne `package.json` in der Wurzel liest Node jede Datei des Bots nach ihrer Syntax als ES-Modul.
- **Start:** `node --permission --allow-fs-read=* --allow-addons --disable-warning=SecurityWarning --disallow-code-generation-from-strings --no-expose-wasm --max-old-space-size=768 /bot/<entry>`. Die Flags verbieten Kindprozesse, Worker, WASI, Inspector, Schreibrechte, Code aus Zeichenketten und WebAssembly; der Heap bleibt unter der Speichergrenze, sodass ein voller Heap als JavaScript-Fehler endet. Sie sind eine weitere Schicht, die Sandbox muss allein reichen.
- **Grenzen:** dieselben wie für Python (A14).
- **Negativ-Suite:** prüft Netz, Dateien und Prozesse wie für Python, für Node zusätzlich Code aus Zeichenketten und WebAssembly (`tests/sandbox/bots/javascript/`).
