import type { CompetitionGame } from "../api/types";

/** "Bundesliga, Season 2" or "Cup, Edition 1". */
export function competitionName(
  t: (key: string, options: { number: number }) => string,
  item: CompetitionGame,
): string {
  const { league, tournament } = item.match;
  if (league) {
    return `${league.league_name}, ${t("leagues.seasonNumber", { number: league.season_number })}`;
  }
  if (!tournament) return "";
  const edition = t("tournaments.editionNumber", { number: tournament.edition_number });
  return `${tournament.tournament_name}, ${edition}`;
}
