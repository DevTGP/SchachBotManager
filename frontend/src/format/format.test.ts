import { describe, expect, it } from "vitest";

import { playersLabel, sideLabel } from "./botLabel";
import { formatClock, formatSpent } from "./clock";
import { formatRatingChange } from "./rating";
import { formatResult } from "./result";
import { formatScore } from "./score";
import { formatTimeControl } from "./timeControl";

describe("formatClock", () => {
  it("shows minutes and seconds, hours when needed", () => {
    expect(formatClock(180_000)).toBe("3:00");
    expect(formatClock(61_999)).toBe("1:01");
    expect(formatClock(3_725_000)).toBe("1:02:05");
  });

  it("shows tenths below ten seconds and never goes negative", () => {
    expect(formatClock(9_870)).toBe("0:09.8");
    expect(formatClock(-50)).toBe("0:00.0");
  });
});

describe("formatSpent", () => {
  it("uses the locale's decimal separator", () => {
    expect(formatSpent(1_234, "en")).toBe("1.2 s");
    expect(formatSpent(1_234, "de")).toBe("1,2 s");
  });

  it("gives short thinking times in milliseconds", () => {
    expect(formatSpent(16, "de")).toBe("16 ms");
    expect(formatSpent(999, "en")).toBe("999 ms");
    expect(formatSpent(1_000, "en")).toBe("1.0 s");
  });
});

describe("formatScore", () => {
  it("turns Black's scores to White's point of view", () => {
    expect(formatScore({ score_cp: 35 }, "w")).toBe("+0.35");
    expect(formatScore({ score_cp: 35 }, "b")).toBe("-0.35");
    expect(formatScore({ score_cp: 0 }, "w")).toBe("0.00");
  });

  it("prefers mate scores and is empty without a score", () => {
    expect(formatScore({ score_cp: 900, score_mate: 3 }, "w")).toBe("#3");
    expect(formatScore({ score_mate: 2 }, "b")).toBe("#-2");
    expect(formatScore({ depth: 5 }, "w")).toBeUndefined();
  });
});

describe("formatTimeControl and formatResult", () => {
  it("writes the time control as players do", () => {
    const discipline = {
      name: "x",
      initial_time_ms: 180_000,
      increment_ms: 2_000,
      startup_ms: 0,
      tolerance_ms: 0,
      max_moves: 1,
    };
    expect(formatTimeControl(discipline)).toBe("3+2");
    expect(formatTimeControl({ ...discipline, initial_time_ms: 90_000, increment_ms: 500 })).toBe(
      "1.5+0.5",
    );
    expect(formatTimeControl({ ...discipline, initial_time_ms: 20_000, increment_ms: 500 })).toBe(
      "20s+0.5",
    );
  });

  it("writes results with typographic dashes", () => {
    expect(formatResult("1/2-1/2")).toBe("½–½");
    expect(formatResult("1-0")).toBe("1–0");
    expect(formatResult(null)).toBe("");
  });
});

describe("sideLabel and playersLabel", () => {
  it("names a side with its version, games before versions by name only", () => {
    expect(sideLabel({ name: "Sharp", version: "1.2.0" })).toBe("Sharp 1.2.0");
    expect(sideLabel({ name: "Sharp", version: null })).toBe("Sharp");
    expect(
      playersLabel({
        white: {
          kind: "bot",
          bot_id: "a",
          name: "Sharp",
          version: "1.2.0",
          sdk: null,
          lang: null,
          rating: null,
        },
        black: {
          kind: "bot",
          bot_id: "b",
          name: "Random",
          version: null,
          sdk: null,
          lang: null,
          rating: null,
        },
      }),
    ).toBe("Sharp 1.2.0 – Random");
  });
});

describe("formatRatingChange", () => {
  it("shows the rating before and after with the difference", () => {
    expect(formatRatingChange({ before: 2800, after: 2830 })).toBe("2800 → 2830 (+30)");
    expect(formatRatingChange({ before: 2400, after: 2370 })).toBe("2400 → 2370 (−30)");
    expect(formatRatingChange({ before: 2500, after: 2500 })).toBe("2500 → 2500 (±0)");
  });
});
