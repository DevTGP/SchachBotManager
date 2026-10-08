import type { RatingChange } from "../api/types";

/** A side's rating around a counted match, e.g. "2500 → 2550 (+50)" (E103). */
export function formatRatingChange({ before, after }: RatingChange): string {
  const diff = after - before;
  const sign = diff > 0 ? "+" : diff < 0 ? "−" : "±";
  return `${before} → ${after} (${sign}${Math.abs(diff)})`;
}
