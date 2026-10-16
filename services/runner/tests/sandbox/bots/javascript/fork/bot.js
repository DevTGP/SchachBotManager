// Tries to start other processes and threads; exits with 42 if one starts (sandbox.md, E227).
import { execFileSync, spawnSync } from "node:child_process";
import { Worker } from "node:worker_threads";

import * as sbm from "schachbotmanager";

const NODE = "/usr/local/bin/node";

function spawn() {
  const result = spawnSync(NODE, ["-e", "0"]);
  if (result.error || result.status !== 0) {
    throw result.error ?? new Error(`exit ${result.status}`);
  }
}

function exec() {
  execFileSync(NODE, ["-e", "0"]);
}

function worker() {
  new Worker("0", { eval: true });
}

function starts(attempt) {
  try {
    attempt();
  } catch {
    return false;
  }
  return true;
}

class Fork extends sbm.Bot {
  chooseMove(board) {
    if ([spawn, exec, worker].some(starts)) {
      process.exit(42);
    }
    return board.legalMoves()[0];
  }
}

if (import.meta.main) {
  await sbm.run(Fork);
}
