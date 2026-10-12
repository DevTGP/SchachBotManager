import { startTournament } from "../../api/adminTournaments";
import { fetchTournament } from "../../api/tournaments";
import type { Edition } from "../../api/types";
import { StartNow } from "../../components/start/StartNow";
import { useApi } from "../../hooks/useApi";
import { NextEdition } from "./NextEdition";

/** A planned edition: when it starts, and "Start now" for an admin (E191). */
export function PlannedEdition({
  edition,
  onStarted,
}: {
  edition: Edition;
  onStarted: () => void;
}) {
  const tournament = useApi(
    (signal) => fetchTournament(edition.tournament_id, signal),
    `tournament:${edition.tournament_id}`,
  );
  const data = tournament.data;
  if (!data || data.edition?.id !== edition.id) return null;
  return (
    <>
      <NextEdition tournament={data} />
      <StartNow
        competition={data}
        start={() => startTournament(data.id)}
        onStarted={() => {
          tournament.reload();
          onStarted();
        }}
      />
    </>
  );
}
