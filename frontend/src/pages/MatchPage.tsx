import { useParams } from "react-router";

import { fetchMatch } from "../api/endpoints";
import type { Match } from "../api/types";
import { ApiContent } from "../components/ApiContent";
import { useApi } from "../hooks/useApi";
import { POLL_MATCH_MS } from "../hooks/polling";
import { Viewer } from "../viewer/Viewer";

/** Moves can still come; only then the viewer asks again (E76). */
function isLive(match: Match | undefined): boolean {
  return match?.status === "queued" || match?.status === "running";
}

export function MatchPage() {
  const { id = "" } = useParams();
  const match = useApi(
    (signal) => fetchMatch(id, signal),
    id,
    (data) => (isLive(data) ? POLL_MATCH_MS : undefined),
  );
  return (
    <ApiContent state={match}>{(data) => <Viewer match={data} live={isLive(data)} />}</ApiContent>
  );
}
