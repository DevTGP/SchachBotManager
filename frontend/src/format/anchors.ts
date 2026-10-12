import type { LeaguePlace, TournamentPlace } from "../api/types";

/** The id of a tier's section on the season page. */
export function tierAnchor(tier: number): string {
  return `tier-${tier}`;
}

/** The id of a round of a tier on the season page. */
export function seasonRoundAnchor(tier: number, round: number): string {
  return `tier-${tier}-round-${round}`;
}

/** The id of a round or knockout round on the edition page. */
export function editionRoundAnchor(round: number): string {
  return `round-${round}`;
}

/** The season page opened at the round of a league game (E188). */
export function seasonPlaceLink(place: LeaguePlace): string {
  return `/seasons/${place.season_id}#${seasonRoundAnchor(place.tier, place.round)}`;
}

/** The edition page opened at the round of a tournament game (E188). */
export function editionPlaceLink(place: TournamentPlace): string {
  return `/editions/${place.edition_id}#${editionRoundAnchor(place.round)}`;
}
