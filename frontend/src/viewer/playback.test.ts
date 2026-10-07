import { describe, expect, it } from "vitest";

import { OPENING } from "../test/fixtures";
import { BASE_DELAY_MS, MIN_REAL_DELAY_MS, playbackDelay } from "./playback";

describe("playbackDelay", () => {
  it("divides the base delay by the factor", () => {
    expect(playbackDelay(1, OPENING[0])).toBe(BASE_DELAY_MS);
    expect(playbackDelay(4, OPENING[0])).toBe(BASE_DELAY_MS / 4);
    expect(playbackDelay(0.5, OPENING[0])).toBe(BASE_DELAY_MS * 2);
  });

  it("waits as long as the bot thought in real time", () => {
    expect(playbackDelay("real", OPENING[1])).toBe(OPENING[1]?.spent_ms);
    expect(playbackDelay("real", { ...OPENING[0]!, spent_ms: 3 })).toBe(MIN_REAL_DELAY_MS);
  });
});
