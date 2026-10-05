# Sandbox

Die eigentliche Sicherheitsgrenze. Sie muss den Server auch dann schützen, wenn die [statische Analyse](statische-analyse.md) vollständig umgangen wird (R3).

## Schutzziele

| Ziel | Mittel |
|------|--------|
| Kein Datenabfluss | Kein Netzwerk, kein Zugriff auf Host-Dateien, DB oder andere Bots |
| Kein Schaden am Server | Ressourcenlimits, keine Privilegien, kein persistenter Schreibzugriff |
| Keine Beeinflussung des Gegners | Getrennte Container, getrennte Kerne |
| Faire Messung | Feste CPU-/Speicherzuteilung je Disziplin |

## Container-Konfiguration je Bot

| Bereich | Einstellung |
|---------|-------------|
| Netzwerk | `none` |
| Dateisystem | Root read-only; Bot-Artefakt read-only eingehängt; kein oder minimales `tmpfs` mit Größenlimit |
| Benutzer | Unprivilegiert, kein root im Container |
| Privilegien | Alle Capabilities entfernt, `no-new-privileges` |
| Syscalls | Restriktives seccomp-Profil (Whitelist je Laufzeitumgebung) |
| Speicher | Hartes Limit, kein Swap → Überschreitung beendet den Prozess (`memory_limit`) |
| CPU | Ein fest zugewiesener Kern, optional Quote für CPU-limitierte Disziplinen |
| Prozesse | PID-Limit (verhindert Fork-Bomben, begrenzt Threads) |
| Ausgabe | stdout/stderr mengenbegrenzt |
| Lebensdauer | Ein Container pro Bot pro Spiel, danach gelöscht |

## Images

- Pro Sprache ein **Build-Image** (Compiler, Analyzer) und ein schlankes **Run-Image** (nur Laufzeit + SDK + freigegebene Bibliotheken).
- Versionen von Laufzeit, SDK und Bibliotheken sind fest gepinnt; Image-Tag wird am Bot gespeichert (Reproduzierbarkeit alter Partien).
- **Auch der Build ist nicht vertrauenswürdig** (Compile-Zeit-Ausführung, Build-Plugins) und läuft mit denselben Einschränkungen plus Zeitlimit.

## Ressourcenlimitierte Disziplinen

| Limit | Durchsetzung |
|-------|-------------|
| Speicher | cgroup-Speicherlimit |
| CPU | cgroup-Quote / Kernzuteilung |
| Dateigröße | Prüfung von Quellcode- und Artefaktgröße in der [Verifikation](verifikation.md) |
| Bedenkzeit | [Match-Runner](match-runner.md) |

Zu beachten: Laufzeitumgebungen (JVM, .NET, Node, CPython) haben einen Grundverbrauch. Speicherlimits pro Disziplin brauchen deshalb entweder einen Sockel je Sprache oder werden als „Nutzlast über Grundverbrauch“ definiert – sonst sind sehr kleine Limits für manche Sprachen unerreichbar. JVM/.NET/Node müssen zusätzlich auf das Containerlimit konfiguriert werden (Heap-Obergrenze), damit sie nicht unkontrolliert beendet werden.

## Isolationsstärke – Optionen (O9)

| Variante | Eigenschaft |
|----------|-------------|
| Standard-Container (runc) mit obiger Härtung | Geringster Aufwand; teilt den Host-Kernel |
| gVisor (`runsc`) | Abgefangene Syscalls, kleinere Kernel-Angriffsfläche; messbarer Laufzeit-Overhead, Freezer-/Timing-Verhalten zu prüfen |
| Rootless-Runtime | Ausbruch landet bei unprivilegiertem Host-Nutzer; Einschränkungen bei cgroup-Funktionen möglich |
| Eigene VM / eigener Host für Runner | Stärkste Trennung von DB und Web; höherer Betriebsaufwand |

## Runner-Zugriff auf die Runtime (R4)

- Zugriff auf die Container-Runtime ist root-äquivalent. Nur Runner und Verifier bekommen ihn, nie die Web-API.
- Runner und Verifier sind nicht aus dem Internet erreichbar und nehmen Aufträge nur über die DB-Queue an.
- Der Sandbox-Treiber setzt alle Container-Optionen fest im Code; aus Job-Daten kommen nur Bot-ID und Disziplin-Limits (validiert, mit Obergrenzen).
