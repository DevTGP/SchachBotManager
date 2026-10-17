// Tries to read and write outside its jail; exits with 42 if anything works (sandbox.md).
import { readFileSync, readdirSync, writeFileSync } from "node:fs";

import * as sbm from "schachbotmanager";

const READ = [
  "/etc/passwd",
  "/etc/shadow",
  "/proc/self/environ",
  "/opt/sbm/sandbox/javascript.cfg",
  "/sys/fs/cgroup/cgroup.procs",
  "/root/.bashrc",
];
const WRITE = [
  "/bot/written",
  "/tmp/written",
  "/written",
  "/node_modules/written",
  "/dev/urandom",
];
// The read-only root of the jail: Node, the SDK, the loader and the mount points.
const ROOT = new Set([
  "bot",
  "dev",
  "etc",
  "lib",
  "lib64",
  "node_modules",
  "usr",
]);

function works(attempt) {
  try {
    attempt();
  } catch {
    return false;
  }
  return true;
}

class Files extends sbm.Bot {
  chooseMove(board) {
    const breached =
      READ.some((path) => works(() => readFileSync(path))) ||
      WRITE.some((path) => works(() => writeFileSync(path, "x"))) ||
      !readdirSync("/").every((name) => ROOT.has(name)) ||
      process.getuid() !== 1000;
    if (breached) {
      process.exit(42);
    }
    return board.legalMoves()[0];
  }
}

if (import.meta.main) {
  await sbm.run(Files);
}
