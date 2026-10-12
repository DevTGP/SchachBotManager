import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { MatchSummary } from "../api/types";
import { editionPlaceLink, seasonPlaceLink } from "../format/anchors";
import { competitionName } from "../format/competition";

/** The header of the competition column of a game list (E188). */
export function CompetitionHeader() {
  const { t } = useTranslation();
  return <th className="optional">{t("matchTable.competition")}</th>;
}

/**
 * The season, edition or series of a game, linked to its round or score (E188); empty for a
 * single game.
 */
export function CompetitionCell({ match }: { match: MatchSummary }) {
  const { t } = useTranslation();
  return (
    <td className="optional">
      <CompetitionLink match={match} label={competitionName(t, match)} />
    </td>
  );
}

function CompetitionLink({ match, label }: { match: MatchSummary; label: string }) {
  const { t } = useTranslation();
  if (match.league) return <Link to={seasonPlaceLink(match.league)}>{label}</Link>;
  if (match.tournament) return <Link to={editionPlaceLink(match.tournament)}>{label}</Link>;
  if (!match.series) return null;
  return (
    <Link to={`/series/${match.series.id}`}>
      {t("series.place", { index: match.series.index, games: match.series.games })}
    </Link>
  );
}
