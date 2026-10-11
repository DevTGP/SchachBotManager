import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { LeaguePlace } from "../api/types";

/** Where a league game stands: league, season, tier, round and board (E137). */
export function MatchLeague({ place }: { place: LeaguePlace | null }) {
  const { t } = useTranslation();
  if (place === null) return null;
  return (
    <p>
      <Link to={`/leagues/${place.league_id}`}>{place.league_name}</Link>
      {", "}
      <Link to={`/seasons/${place.season_id}`}>
        {t("leagues.seasonNumber", { number: place.season_number })}
      </Link>
      {", "}
      {t("seasons.place", { tier: place.tier, round: place.round, board: place.board })}
    </p>
  );
}
