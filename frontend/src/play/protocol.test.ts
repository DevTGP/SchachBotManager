import { describe, expect, it } from "vitest";

import {
  movesBetween,
  parseServerMessage,
  type PlayState,
  remainingMs,
  splitMoves,
} from "./protocol";

const STATE = {
  type: "state",
  v: 1,
  color: "white",
  white: "Guest",
  black: "Material",
  start_fen: "8/4P3/8/8/8/8/k7/4K3 w - - 0 1",
  fen: "8/4P3/8/8/8/8/k7/4K3 w - - 0 1",
  moves: "",
  san: "",
  clock: { white: 60_000, black: 50_000 },
  running: "white",
  increment_ms: 0,
  legal_moves: "e7e8q e7e8r e7e8b e7e8n e1d1",
  result: null,
  termination: null,
} satisfies PlayState;

describe("play protocol", () => {
  it("reads only the messages it knows", () => {
    expect(parseServerMessage(JSON.stringify(STATE))).toEqual(STATE);
    expect(parseServerMessage('{"type":"joined","v":1}')?.type).toBe("joined");
    expect(parseServerMessage('{"type":"turn"}')).toBeUndefined();
    expect(parseServerMessage("not json")).toBeUndefined();
    expect(parseServerMessage("[]")).toBeUndefined();
  });

  it("finds a single move or the four promotions between two squares", () => {
    const legal = splitMoves(STATE.legal_moves);
    expect(movesBetween(legal, "e1", "d1")).toEqual(["e1d1"]);
    expect(movesBetween(legal, "e7", "e8")).toHaveLength(4);
    expect(movesBetween(legal, "e1", "e2")).toEqual([]);
    expect(splitMoves("")).toEqual([]);
  });

  it("counts down only the running clock and never below zero", () => {
    expect(remainingMs(STATE, "white", 1500)).toBe(58_500);
    expect(remainingMs(STATE, "black", 1500)).toBe(50_000);
    expect(remainingMs(STATE, "white", 90_000)).toBe(0);
  });
});
