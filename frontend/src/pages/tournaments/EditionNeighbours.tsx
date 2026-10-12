import { useTranslation } from "react-i18next";

import { fetchTournament } from "../../api/tournaments";
import { NeighbourLinks } from "../../components/NeighbourLinks";
import { useApi } from "../../hooks/useApi";

/** The editions before and after this one of its tournament (E188); quiet while it loads. */
export function EditionNeighbours({
  tournamentId,
  number,
}: {
  tournamentId: string;
  number: number;
}) {
  const { t } = useTranslation();
  const tournament = useApi(
    (signal) => fetchTournament(tournamentId, signal),
    `tournament:${tournamentId}`,
  );
  if (!tournament.data) return null;
  return (
    <NeighbourLinks
      entries={tournament.data.editions}
      number={number}
      path="/editions"
      previous={(value) => t("editions.previous", { number: value })}
      next={(value) => t("editions.next", { number: value })}
    />
  );
}
