import type { Move } from "../api/types";

/** Fixed factors and "real", which waits as long as the bot thought about the move. */
export const SPEEDS = [0.5, 1, 2, 4, "real"] as const;
export type Speed = (typeof SPEEDS)[number];

/** One move per second at factor 1. */
export const BASE_DELAY_MS = 1_000;

/** Real time still shows instant moves for a moment. */
export const MIN_REAL_DELAY_MS = 50;

/** How long playback waits before showing `next`. */
export function playbackDelay(speed: Speed, next: Move | undefined): number {
  if (speed === "real") return Math.max(MIN_REAL_DELAY_MS, next?.spent_ms ?? 0);
  return BASE_DELAY_MS / speed;
}
