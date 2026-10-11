import { useEffect, useMemo, useRef, useState } from "react";

import { fetchMatch, matchLiveUrl } from "../api/endpoints";
import type { Match, Move } from "../api/types";
import { POLL_MATCH_MS } from "./polling";
import { type ReloadableApiState, useApi } from "./useApi";

interface Stream {
  /** The match the moves belong to. */
  id: string;
  /** Moves from the stream, contiguous by ply; some may already be in the loaded match. */
  moves: Move[];
  /** The stream is open; the page then asks the API only at the end. */
  open: boolean;
}

/**
 * A match that receives its moves from the gateway's event stream while it runs (E142).
 * Without the stream, before it opens or after it broke, the page asks the API again every
 * POLL_MATCH_MS as before; a queued match is always asked about that way.
 */
export function useLiveMatch(id: string): ReloadableApiState<Match> {
  const [stream, setStream] = useState<Stream>({ id, moves: [], open: false });
  const open = stream.id === id && stream.open;
  const match = useApi(
    (signal) => fetchMatch(id, signal),
    id,
    (data) => pollInterval(data, open),
  );
  const { data, reload } = match;
  const running = data?.status === "running";

  // The stream starts after the moves already loaded; read when it opens, not a reason to reopen.
  const known = useRef(0);
  useEffect(() => {
    known.current = data?.moves.length ?? 0;
  });

  useEffect(() => {
    if (!running || typeof EventSource === "undefined") return;
    let last = known.current;
    const source = new EventSource(matchLiveUrl(id, last));
    const update = (change: (current: Stream) => Stream) =>
      setStream((current) => change(current.id === id ? current : { id, moves: [], open: false }));

    source.onopen = () => update((current) => ({ ...current, open: true }));
    source.onerror = () => update((current) => ({ ...current, open: false }));
    source.addEventListener("move", (event) => {
      const move = JSON.parse((event as MessageEvent<string>).data) as Move;
      if (move.ply <= last) return;
      if (move.ply !== last + 1) {
        // Moves are missing: back to asking the API, which has them all.
        source.close();
        update((current) => ({ ...current, open: false }));
        return;
      }
      last = move.ply;
      update((current) => ({ ...current, moves: [...current.moves, move] }));
    });
    source.addEventListener("end", () => {
      source.close();
      update((current) => ({ ...current, open: false }));
      reload();
    });
    return () => source.close();
  }, [id, running, reload]);

  const extra = stream.id === id ? stream.moves : undefined;
  const shown = useMemo(() => data && withMoves(data, extra), [data, extra]);
  return { ...match, data: shown };
}

function pollInterval(data: Match | undefined, streaming: boolean): number | undefined {
  if (data?.status === "queued") return POLL_MATCH_MS;
  if (data?.status === "running" && !streaming) return POLL_MATCH_MS;
  return undefined;
}

/** The loaded match with the streamed moves that follow on its last one. */
function withMoves(match: Match, extra: Move[] | undefined): Match {
  if (!extra?.length) return match;
  const moves = [...match.moves];
  for (const move of extra) {
    if (move.ply === moves.length + 1) moves.push(move);
  }
  return moves.length === match.moves.length ? match : { ...match, moves };
}
