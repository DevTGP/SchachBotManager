/**
 * Durations as forms type them and as the API stores them: seconds or minutes with a decimal
 * point or comma on one side, milliseconds on the other (E168).
 */
export function secondsToMs(typed: string): number {
  return Math.round(typedNumber(typed) * 1000);
}

export function minutesToMs(typed: string): number {
  return Math.round(typedNumber(typed) * 60_000);
}

/** Milliseconds as seconds for a form field, without trailing zeros. */
export function msToSeconds(ms: number): string {
  return String(ms / 1000);
}

function typedNumber(typed: string): number {
  return Number(typed.trim().replace(",", "."));
}
