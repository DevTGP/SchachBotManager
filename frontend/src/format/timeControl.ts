import type { Discipline } from "../api/types";

/**
 * Base time in minutes and increment in seconds, as players write it: 3+2.
 * A base time under a minute is given in seconds instead: 20s+0.5.
 */
export function formatTimeControl(discipline: Discipline): string {
  const base = discipline.initial_time_ms;
  const increment = trim(discipline.increment_ms / 1000);
  return base < 60_000
    ? `${trim(base / 1000)}s+${increment}`
    : `${trim(base / 60_000)}+${increment}`;
}

function trim(value: number): string {
  return String(Math.round(value * 100) / 100);
}
