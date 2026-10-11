import type { RatingChange } from "../api/types";

/** A side's rating around a counted match, e.g. "2500 → 2550 (+50)" (E103). */
export function formatRatingChange({ before, after }: RatingChange): string {
  const diff = after - before;
  const sign = diff > 0 ? "+" : diff < 0 ? "−" : "±";
  return `${before} → ${after} (${sign}${Math.abs(diff)})`;
}

/** A rating without a counted game is only the start value: shown as "–" (U11). */
export function ratingText({ value, games }: { value: number; games: number }): string {
  return games > 0 ? String(value) : "–";
}
