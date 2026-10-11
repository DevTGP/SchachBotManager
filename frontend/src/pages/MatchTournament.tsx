import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { TournamentPlace } from "../api/types";

/** Where a tournament game stands: tournament, edition, round and board or duel phase (E178). */
export function MatchTournament({ place }: { place: TournamentPlace | null }) {
  const { t } = useTranslation();
  if (place === null) return null;
  return (
    <p>
      <Link to={`/tournaments/${place.tournament_id}`}>{place.tournament_name}</Link>
      {", "}
      <Link to={`/editions/${place.edition_id}`}>
        {t("tournaments.editionNumber", { number: place.edition_number })}
      </Link>
      {", "}
      {place.phase === null
        ? t("tournaments.place", { round: place.round, board: place.board })
        : t("tournaments.duelPlace", {
            round: place.round,
            duel: place.board,
            phase: t(`duelPhase.${place.phase}`, { game: place.game }),
          })}
    </p>
  );
}
