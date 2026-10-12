import { startLeague } from "../../api/admin";
import { fetchLeague } from "../../api/leagues";
import type { Season } from "../../api/types";
import { StartNow } from "../../components/start/StartNow";
import { useApi } from "../../hooks/useApi";
import { NextSeason } from "./NextSeason";

/** A planned season: when it starts, and "Start now" for an admin (E191). */
export function PlannedSeason({ season, onStarted }: { season: Season; onStarted: () => void }) {
  const league = useApi(
    (signal) => fetchLeague(season.league_id, signal),
    `league:${season.league_id}`,
  );
  const data = league.data;
  if (!data || data.season?.id !== season.id) return null;
  return (
    <>
      <NextSeason league={data} />
      <StartNow
        competition={data}
        start={() => startLeague(data.id)}
        onStarted={() => {
          league.reload();
          onStarted();
        }}
      />
    </>
  );
}
