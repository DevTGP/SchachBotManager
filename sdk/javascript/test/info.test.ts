// Info in the move message: limits of the protocol, truncation and dropped fields (E43, E63).
import assert from "node:assert/strict";
import { test } from "node:test";

import { Board, Move, NULL_MOVE, RESIGN } from "../src/index.ts";
import type { Info } from "../src/index.ts";
import { move } from "../src/protocol.ts";
import { captureLog } from "./capture.ts";

const lines = captureLog();

function sent(info: Info): Record<string, unknown> {
  return move("e2e4", info).info as Record<string, unknown>;
}

function warnings(): string {
  return lines.join("");
}

test("full info", () => {
  const board = new Board();
  const pv = [board.parseMove("e2e4"), Move.parse("e7e5")];
  assert.deepEqual(
    sent({ depth: 12, seldepth: 18, scoreCp: -35, nodes: 1_534_211, pv, text: "book" }),
    {
      depth: 12,
      seldepth: 18,
      score_cp: -35,
      nodes: 1_534_211,
      pv: ["e2e4", "e7e5"],
      text: "book",
    },
  );
});

test("empty info and no info", () => {
  assert.deepEqual(sent({}), {});
  assert.ok(!("info" in move("e2e4", undefined)));
  assert.deepEqual(sent({ depth: undefined, text: null as unknown as string }), {});
});

test("limits are inclusive and bigints count", () => {
  assert.deepEqual(
    sent({ depth: 1024, seldepth: 0, scoreMate: -1024, nodes: Number.MAX_SAFE_INTEGER }),
    { depth: 1024, seldepth: 0, score_mate: -1024, nodes: Number.MAX_SAFE_INTEGER },
  );
  assert.deepEqual(sent({ scoreCp: 100_000 }), { score_cp: 100_000 });
  assert.deepEqual(sent({ nodes: 12n as unknown as number }), { nodes: 12 });
  assert.equal(warnings(), "");
});

const INVALID: [keyof Info, unknown][] = [
  ["depth", -1],
  ["depth", 1025],
  ["seldepth", 2.5],
  ["scoreCp", -100_001],
  ["scoreMate", 0],
  ["scoreMate", 1025],
  ["nodes", 2 ** 53],
  ["nodes", 2n ** 53n],
  ["nodes", "many"],
  ["depth", Number.NaN],
];

for (const [name, value] of INVALID) {
  test(`${name}=${String(value)} is left out`, () => {
    assert.deepEqual(sent({ [name]: value, text: "kept" } as Info), { text: "kept" });
    assert.match(warnings(), new RegExp(`WARN  report: ${name}=`));
  });
}

test("both scores keep mate", () => {
  assert.deepEqual(sent({ scoreCp: 500, scoreMate: 3 }), { score_mate: 3 });
  assert.match(warnings(), /only scoreMate/);
});

test("pv is truncated and may be any iterable", () => {
  const moves = Array.from({ length: 20 }, () => [Move.parse("g1f3"), Move.parse("f3g1")]).flat();
  assert.deepEqual(sent({ pv: moves }).pv, Array(16).fill(["g1f3", "f3g1"]).flat());
  const set = new Set([Move.parse("e2e4"), Move.parse("e7e5")]);
  assert.deepEqual(sent({ pv: set as unknown as Move[] }).pv, ["e2e4", "e7e5"]);
});

for (const bad of [NULL_MOVE, RESIGN, "e2e4", null]) {
  test(`pv ends before ${String(bad)}`, () => {
    const pv = [Move.parse("e2e4"), bad, Move.parse("e7e5")] as Move[];
    assert.deepEqual(sent({ pv }).pv, ["e2e4"]);
    assert.match(warnings(), /report: pv ends/);
  });
}

test("pv that is no list", () => {
  assert.deepEqual(sent({ pv: 5 as unknown as Move[] }).pv, []);
  assert.deepEqual(sent({ pv: "e2e4" as unknown as Move[] }).pv, []);
  assert.match(warnings(), /not a list/);
});

test("text is truncated by code points", () => {
  assert.equal(sent({ text: "♞".repeat(300) }).text, "♞".repeat(256));
  assert.equal(sent({ text: "😀".repeat(300) }).text, "😀".repeat(256));
});

test("text without UTF-8 form", () => {
  assert.equal(sent({ text: "a\ud800b" }).text, "a�b");
});

test("text that is no string", () => {
  assert.deepEqual(sent({ text: 7 as unknown as string }), {});
  assert.match(warnings(), /text=7/);
});
