import { describe, expect, it } from "vitest";

import { chart, ratingValues } from "./ratingChart";

const BOX = { width: 120, height: 60, padding: 10 };

function point(before: number, after: number) {
  return { match_id: "m", finished_at: "2026-05-01T10:00:00.000Z", before, after };
}

describe("ratingValues", () => {
  it("starts with the rating before the first game", () => {
    expect(ratingValues([point(1500, 1510), point(1510, 1490)])).toEqual([1500, 1510, 1490]);
    expect(ratingValues([])).toEqual([]);
  });
});

describe("chart", () => {
  it("spreads the values over the box with the highest at the top", () => {
    const { points, low, high } = chart([1500, 1600, 1550], BOX);
    expect([low, high]).toEqual([1500, 1600]);
    expect(points.map((p) => [p.x, p.y])).toEqual([
      [10, 50],
      [60, 10],
      [110, 30],
    ]);
  });

  it("keeps a flat history in the middle and centres a single value", () => {
    const { points, low, high } = chart([1500], BOX);
    expect([low, high]).toEqual([1490, 1510]);
    expect(points).toEqual([{ x: 60, y: 30, value: 1500 }]);
  });
});
