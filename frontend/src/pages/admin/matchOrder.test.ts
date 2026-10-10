import { describe, expect, it } from "vitest";

import { DEFAULT_FORM, matchOrder } from "./matchOrder";

describe("matchOrder", () => {
  it("turns seconds into milliseconds and leaves out an empty position", () => {
    expect(matchOrder({ ...DEFAULT_FORM, white: "w", black: "b" })).toEqual({
      white_bot_id: "w",
      black_bot_id: "b",
      initial_time_ms: 180_000,
      increment_ms: 2_000,
      games: 1,
      alternate: false,
      priority: 100,
      max_moves: 500,
      rated: true,
    });
  });

  it("accepts a decimal comma and keeps a trimmed position", () => {
    const order = matchOrder({
      ...DEFAULT_FORM,
      white: "w",
      black: "b",
      initialSeconds: "20",
      incrementSeconds: "0,5",
      startFen: "  8/8/8/8/8/8/8/K6k w - - 0 1 ",
    });
    expect(order.initial_time_ms).toBe(20_000);
    expect(order.increment_ms).toBe(500);
    expect(order.start_fen).toBe("8/8/8/8/8/8/8/K6k w - - 0 1");
  });

  it("passes the wish for an unrated game", () => {
    expect(matchOrder({ ...DEFAULT_FORM, white: "w", black: "b", rated: false }).rated).toBe(false);
  });
});
