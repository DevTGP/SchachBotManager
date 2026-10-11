import type { RatingPoint } from "../../api/types";

export interface ChartBox {
  width: number;
  height: number;
  padding: number;
}

export interface ChartPoint {
  x: number;
  y: number;
  value: number;
}

export interface Chart {
  points: ChartPoint[];
  /** The values at the bottom and the top edge of the plot. */
  low: number;
  high: number;
}

/** The smallest span shown, so that a flat history does not fill the height with noise. */
const MIN_SPAN = 20;

/** The rating before the first counted game, then after each one (E140). */
export function ratingValues(games: RatingPoint[]): number[] {
  if (games.length === 0) return [];
  return [games[0]!.before, ...games.map((game) => game.after)];
}

/** Places the values from left to right in the box, the highest at the top. */
export function chart(values: number[], box: ChartBox): Chart {
  if (values.length === 0) return { points: [], low: 0, high: 0 };
  let low = Math.min(...values);
  let high = Math.max(...values);
  if (high - low < MIN_SPAN) {
    const middle = (low + high) / 2;
    low = middle - MIN_SPAN / 2;
    high = middle + MIN_SPAN / 2;
  }
  const inner = { width: box.width - 2 * box.padding, height: box.height - 2 * box.padding };
  const step = values.length > 1 ? inner.width / (values.length - 1) : 0;
  const points = values.map((value, index) => ({
    x: box.padding + (values.length > 1 ? index * step : inner.width / 2),
    y: box.padding + ((high - value) / (high - low)) * inner.height,
    value,
  }));
  return { points, low, high };
}
