// A JavaScript bot against the reference bots of the Python SDK in sbm-arena (M5 step 1).
import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";

import { arenaMissing, playInArena, REGULAR } from "./arena-command.ts";
import { writeBot } from "./bot-process.ts";

test("plays against the reference bots", { skip: arenaMissing }, () => {
  const directory = mkdtempSync(path.join(tmpdir(), "sbm-arena-"));
  try {
    const bot = writeBot(directory, { turn: 'sbm.Log.info("thinking");' });
    for (const opponent of ["random", "material"]) {
      const terminations = playInArena([bot, opponent, "--games", "2", "--max-moves", "30"]);
      assert.equal(terminations.length, 2);
      for (const termination of terminations) {
        assert.ok(REGULAR.includes(termination), termination);
      }
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
