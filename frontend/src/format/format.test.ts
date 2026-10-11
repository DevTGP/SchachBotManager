import { describe, expect, it } from "vitest";

import { formatClock, formatSpent } from "./clock";
import { minutesToMs, msToSeconds, secondsToMs } from "./duration";
import { pairing, pairingLabel, pairingResult } from "./pairing";
import { formatPoints } from "./points";
import { formatRatingChange, ratingText } from "./rating";
import {
  fromLocalInput,
  intervalHours,
  nextFullHour,
  splitInterval,
  toLocalInput,
} from "./recurrence";
import { formatResult } from "./result";
import { formatScore } from "./score";
import { disciplineLabel, formatTimeControl } from "./timeControl";

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
  it("writes the time control with units and the locale's numbers", () => {
    const discipline = { name: "Blitz", initial_time_ms: 180_000, increment_ms: 2_000 };
    expect(formatTimeControl(discipline, "de")).toBe("3\u00a0min + 2\u00a0s");
    expect(formatTimeControl({ initial_time_ms: 90_000, increment_ms: 500 }, "de")).toBe(
      "1,5\u00a0min + 0,5\u00a0s",
    );
    expect(formatTimeControl({ initial_time_ms: 20_000, increment_ms: 500 }, "en")).toBe(
      "20\u00a0s + 0.5\u00a0s",
    );
    expect(disciplineLabel(discipline, "en")).toBe("Blitz (3\u00a0min + 2\u00a0s)");
  });

  it("writes results with typographic dashes", () => {
    expect(formatResult("1/2-1/2")).toBe("½–½");
    expect(formatResult("1-0")).toBe("1–0");
    expect(formatResult("0-0")).toBe("0–0");
    expect(formatResult(null)).toBe("");
  });
});

function bot(name: string, version: string | null = null) {
  return { kind: "bot" as const, bot_id: name, name, version, sdk: null, lang: null, rating: null };
}

describe("pairing", () => {
  it("puts the sides in alphabetical order, whatever the colours", () => {
    const match = { white: bot("Random"), black: bot("material") };
    expect(pairing(match).first.name).toBe("material");
    expect(pairing(match).flipped).toBe(true);
    expect(pairingLabel(match)).toBe("material – Random");
    expect(pairing({ white: bot("Alpha"), black: bot("Beta") }).flipped).toBe(false);
  });

  it("orders two versions of one name by version", () => {
    const match = { white: bot("Sharp", "1.10.0"), black: bot("Sharp", "1.9.0") };
    expect(pairing(match).first.version).toBe("1.9.0");
  });

  it("gives the result in the order of the pairing", () => {
    expect(pairingResult("1-0", false)).toBe("1–0");
    expect(pairingResult("1-0", true)).toBe("0–1");
    expect(pairingResult("0-0", true)).toBe("0–0");
    expect(pairingResult("1/2-1/2", true)).toBe("½–½");
    expect(pairingResult(null, true)).toBe("");
  });
});

describe("durations", () => {
  it("reads seconds and minutes with a point or a comma", () => {
    expect(secondsToMs("2,5")).toBe(2_500);
    expect(secondsToMs(" 3 ")).toBe(3_000);
    expect(minutesToMs("0.5")).toBe(30_000);
    expect(msToSeconds(1_500)).toBe("1.5");
  });
});

describe("formatRatingChange", () => {
  it("shows the rating before and after with the difference", () => {
    expect(formatRatingChange({ before: 2800, after: 2830 })).toBe("2800 → 2830 (+30)");
    expect(formatRatingChange({ before: 2400, after: 2370 })).toBe("2400 → 2370 (−30)");
    expect(formatRatingChange({ before: 2500, after: 2500 })).toBe("2500 → 2500 (±0)");
  });

  it("shows a rating without counted games as a dash", () => {
    expect(ratingText({ value: 1500, games: 0 })).toBe("–");
    expect(ratingText({ value: 1512, games: 3 })).toBe("1512");
  });
});

describe("formatPoints", () => {
  it("writes half points as ½", () => {
    expect(formatPoints(0)).toBe("0");
    expect(formatPoints(0.5)).toBe("½");
    expect(formatPoints(3)).toBe("3");
    expect(formatPoints(6.5)).toBe("6½");
  });
});

describe("recurrence", () => {
  it("splits an interval into the largest even unit", () => {
    expect(splitInterval(336)).toEqual({ amount: 2, unit: "weeks" });
    expect(splitInterval(48)).toEqual({ amount: 2, unit: "days" });
    expect(splitInterval(30)).toEqual({ amount: 30, unit: "hours" });
    expect(intervalHours(3, "days")).toBe(72);
  });

  it("converts between local input and UTC", () => {
    const local = "2026-10-12T18:30";
    expect(toLocalInput(fromLocalInput(local))).toBe(local);
    expect(nextFullHour(new Date(2026, 9, 12, 18, 30))).toBe("2026-10-12T19:00");
  });
});
