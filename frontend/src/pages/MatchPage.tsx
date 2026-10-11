import { useParams } from "react-router";

import type { Match } from "../api/types";
import { ApiContent } from "../components/ApiContent";
import { useLiveMatch } from "../hooks/useLiveMatch";
import { Viewer } from "../viewer/Viewer";
import { MatchRepeat } from "./admin/MatchRepeat";
import { MatchLeague } from "./MatchLeague";
import { MatchTournament } from "./MatchTournament";
import { MatchSeries } from "./MatchSeries";

/** Moves can still come; the viewer follows them (E76, E142). */
function isLive(match: Match | undefined): boolean {
  return match?.status === "queued" || match?.status === "running";
}

export function MatchPage() {
  const { id = "" } = useParams();
  const match = useLiveMatch(id);
  return (
    <ApiContent state={match}>
      {(data) => (
        <>
          <Viewer match={data} live={isLive(data)} />
          <MatchSeries place={data.series} />
          <MatchLeague place={data.league} />
          <MatchTournament place={data.tournament} />
          <MatchRepeat match={data} />
        </>
      )}
    </ApiContent>
  );
}
