import type { EditionSummary, SeasonSummary } from "../../api/types";

/**
 * Whether an admin can start the planned season or edition now: it waits for an admin or for a
 * later calendar date (E171). A due one starts by itself once enough bots are there.
 */
export function startable(competition: {
  archived: boolean;
  season?: SeasonSummary | null;
  edition?: EditionSummary | null;
}): boolean {
  const next = competition.season ?? competition.edition;
  if (competition.archived || !next || next.status !== "planned") return false;
  return next.starts_after === null || Date.parse(next.starts_after) > Date.now();
}

/** A planned season or edition whose date has come; the runner starts it with enough bots. */
export function due(next: { status: string; starts_after: string | null } | undefined): boolean {
  return (
    next?.status === "planned" &&
    next.starts_after !== null &&
    Date.parse(next.starts_after) <= Date.now()
  );
}
