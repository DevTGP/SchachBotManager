import type { CoderLimits } from "../../api/types";

/** The coder limits as numbers for the form and its texts; times in seconds (E98, E154). */
export function ownLimits(limits: CoderLimits) {
  return {
    initialSeconds: limits.max_initial_ms / 1000,
    incrementSeconds: limits.max_increment_ms / 1000,
    games: limits.games_per_request,
    gamesPerDay: limits.games_per_day,
  };
}
