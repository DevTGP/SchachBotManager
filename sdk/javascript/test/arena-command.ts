// The sbm-arena of the Python SDK for tests that play real games: SBM_ARENA or sbm-arena on the
// PATH. Without it those tests are skipped; with SBM_REQUIRE_ARENA=1 they fail instead.
import { spawnSync } from "node:child_process";

export const ARENA = process.env.SBM_ARENA ?? "sbm-arena";

/** Terminations of a game that ended by the rules, not by an error. */
export const REGULAR = [
  "checkmate",
  "stalemate",
  "threefold_repetition",
  "fifty_move_rule",
  "insufficient_material",
  "max_moves",
];

function available(): boolean {
  const probe = spawnSync(ARENA, ["--help"], { encoding: "utf-8" });
  return probe.status === 0;
}

/** The reason to skip, or false when the arena is there. */
export const arenaMissing: string | false = available() ? false : `${ARENA} is missing`;
if (arenaMissing && process.env.SBM_REQUIRE_ARENA === "1") {
  throw new Error(`${arenaMissing}, but SBM_REQUIRE_ARENA=1`);
}

/** Plays with the arena and returns the terminations of the games; fails on exit code != 0. */
export function playInArena(args: readonly string[], cwd?: string): string[] {
  const arena = spawnSync(ARENA, [...args, "--quiet"], {
    cwd,
    encoding: "utf-8",
    timeout: 120_000,
    env: { ...process.env, NODE_NO_WARNINGS: "1" },
  });
  if (arena.status !== 0) {
    throw new Error(`sbm-arena ended with ${arena.status}: ${arena.stderr}`);
  }
  return [...arena.stdout.matchAll(/^ {2}(?:1-0|0-1|1\/2-1\/2) (\w+):/gm)].map((match) => match[1]);
}
