import type { MatchSummary, Side } from "../api/types";

/** What orders a side: its name, then its version. */
type Sortable = Pick<Side, "name" | "version">;

/** The two sides of a game in alphabetical order; flipped when black comes first (E165). */
export interface Pairing<S extends Sortable = Side> {
  first: S;
  second: S;
  flipped: boolean;
}

export function pairing<S extends Sortable>(match: { white: S; black: S }): Pairing<S> {
  const flipped = compareSides(match.black, match.white) < 0;
  return flipped
    ? { first: match.black, second: match.white, flipped }
    : { first: match.white, second: match.black, flipped };
}

/** "Material – Random", whatever the colors. */
export function pairingLabel(match: { white: Sortable; black: Sortable }): string {
  const { first, second } = pairing(match);
  return `${first.name} – ${second.name}`;
}

const RESULTS: Record<string, [string, string]> = {
  "1-0": ["1", "0"],
  "0-1": ["0", "1"],
  "1/2-1/2": ["½", "½"],
};

/** The result in the order of the pairing: "0–1" when black won and comes first. */
export function pairingResult(result: MatchSummary["result"], flipped: boolean): string {
  if (result === null) return "";
  const points = RESULTS[result];
  if (!points) return result;
  const [white, black] = points;
  return flipped ? `${black}–${white}` : `${white}–${black}`;
}

/** Alphabetical by name, then by version: the order of every pairing (E165). */
export function compareSides(a: Sortable, b: Sortable): number {
  const byName = a.name.localeCompare(b.name, undefined, { sensitivity: "base" });
  if (byName !== 0) return byName;
  return (a.version ?? "").localeCompare(b.version ?? "", undefined, { numeric: true });
}
