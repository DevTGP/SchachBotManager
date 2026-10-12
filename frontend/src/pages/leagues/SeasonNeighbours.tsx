import { useTranslation } from "react-i18next";

import { fetchLeague } from "../../api/leagues";
import { NeighbourLinks } from "../../components/NeighbourLinks";
import { useApi } from "../../hooks/useApi";

/** The seasons before and after this one in its league (E188); quiet while the league loads. */
export function SeasonNeighbours({ leagueId, number }: { leagueId: string; number: number }) {
  const { t } = useTranslation();
  const league = useApi((signal) => fetchLeague(leagueId, signal), `league:${leagueId}`);
  if (!league.data) return null;
  return (
    <NeighbourLinks
      entries={league.data.seasons}
      number={number}
      path="/seasons"
      previous={(value) => t("seasons.previous", { number: value })}
      next={(value) => t("seasons.next", { number: value })}
    />
  );
}
