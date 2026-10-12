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

/** A game in the viewer; its series, season or edition comes first, above the board (E188). */
export function MatchPage() {
  const { id = "" } = useParams();
  const match = useLiveMatch(id);
  return (
    <ApiContent state={match}>
      {(data) => (
        <>
          <MatchSeries place={data.series} />
          <MatchLeague place={data.league} />
          <MatchTournament place={data.tournament} />
          <Viewer match={data} live={isLive(data)} />
          <MatchRepeat match={data} />
        </>
      )}
    </ApiContent>
  );
}
