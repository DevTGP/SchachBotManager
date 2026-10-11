import type { Discipline } from "../api/types";

// Number and unit stay on one line.
const UNIT_SPACE = " ";

/**
 * Base time and increment with their units, numbers in the reader's locale: "3 min + 2 s".
 * A base time under a minute is given in seconds: "20 s + 0,5 s" (E168).
 */
export function formatTimeControl(
  discipline: Pick<Discipline, "initial_time_ms" | "increment_ms">,
  locale: string,
): string {
  const number = new Intl.NumberFormat(locale, { maximumFractionDigits: 2 });
  const base = discipline.initial_time_ms;
  const head =
    base < 60_000
      ? `${number.format(base / 1000)}${UNIT_SPACE}s`
      : `${number.format(base / 60_000)}${UNIT_SPACE}min`;
  return `${head} + ${number.format(discipline.increment_ms / 1000)}${UNIT_SPACE}s`;
}

/** A discipline as "Name (3 min + 2 s)" for selects and facts. */
export function disciplineLabel(
  discipline: Pick<Discipline, "name" | "initial_time_ms" | "increment_ms">,
  locale: string,
): string {
  return `${discipline.name} (${formatTimeControl(discipline, locale)})`;
}
