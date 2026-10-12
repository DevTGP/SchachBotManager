import type { MatchSummary } from "../api/types";

/** "Bundesliga, Season 2" or "Cup, Edition 1"; empty for a game of neither. */
export function competitionName(
  t: (key: string, options: { number: number }) => string,
  match: Pick<MatchSummary, "league" | "tournament">,
): string {
  const { league, tournament } = match;
  if (league) {
    return `${league.league_name}, ${t("leagues.seasonNumber", { number: league.season_number })}`;
  }
  if (!tournament) return "";
  const edition = t("tournaments.editionNumber", { number: tournament.edition_number });
  return `${tournament.tournament_name}, ${edition}`;
}
