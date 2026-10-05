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

- Pro Sprache ein vorbereitetes Verzeichnis mit Laufzeit, SDK (inklusive Kern-Bibliothek) und freigegebenen Bibliotheken; read-only eingehängt.
- Getrennt davon ein **Build-Verzeichnis** mit Compiler und Analyzer.
- Beide werden in CI gebaut, versioniert (Tag am Bot gespeichert) und als Archiv auf den Server gebracht.
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

## Rechte von Runner und Verifier (R4, A13)

- nsjail braucht die Möglichkeit, Namespaces und cgroups anzulegen. Runner und Verifier laufen deshalb als eigene Dienste direkt auf dem Host unter einem eigenen Systemnutzer mit delegierter cgroup.
- Sie sind nicht aus dem Netz erreichbar und nehmen Aufträge nur über die DB-Queue an.
- Die Web-API hat keinerlei Möglichkeit, Prozesse zu starten.
- Alle Sandbox-Optionen stehen fest in den Konfigurationsdateien; aus Job-Daten kommt nur die Bot-ID.

## Zu beachten

- **Kernel-Voraussetzungen:** cgroup v2 und unprivilegierte User-Namespaces müssen auf dem Host aktiv sein.
- **Gemeinsamer Kernel:** Die Isolation teilt den Host-Kernel; ein Kernel-Fehler wäre ein Ausbruchsweg. Für den Nutzerkreis (Freunde, Invite-only) als ausreichend eingestuft; aktuelle Kernel-Updates bleiben relevant.
- **seccomp-Whitelists je Laufzeit** müssen einmal ermittelt und bei Laufzeit-Updates geprüft werden (JVM und .NET nutzen mehr Aufrufe als CPython).
- **Aufräumen:** Beim Runner-Start verwaiste cgroups/Prozesse entfernen.
- **Negativ-Tests:** Testbots für Netz, Datei, Fork-Bombe, Speicher, Endlosschleife, übergroße Ausgabe laufen in CI gegen die Sandbox.
