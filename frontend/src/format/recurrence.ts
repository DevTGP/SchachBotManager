export type IntervalUnit = "hours" | "days" | "weeks";

const HOURS: Record<IntervalUnit, number> = { hours: 1, days: 24, weeks: 168 };

/** An interval in hours as the largest unit it fills evenly (E180). */
export function splitInterval(hours: number): { amount: number; unit: IntervalUnit } {
  if (hours % HOURS.weeks === 0) return { amount: hours / HOURS.weeks, unit: "weeks" };
  if (hours % HOURS.days === 0) return { amount: hours / HOURS.days, unit: "days" };
  return { amount: hours, unit: "hours" };
}

export function intervalHours(amount: number, unit: IntervalUnit): number {
  return amount * HOURS[unit];
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

/** A point in time as the value of a datetime-local input, in local time (E171). */
export function toLocalInput(iso: string): string {
  const date = new Date(iso);
  const day = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  return `${day}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

/** The value of a datetime-local input, read as local time, as an RFC 3339 timestamp. */
export function fromLocalInput(local: string): string {
  return new Date(local).toISOString();
}

/** The next full hour from now, the first start a new calendar suggests. */
export function nextFullHour(now: Date = new Date()): string {
  const next = new Date(now);
  next.setMinutes(0, 0, 0);
  next.setHours(next.getHours() + 1);
  return toLocalInput(next.toISOString());
}
