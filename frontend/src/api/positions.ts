import { sendJson } from "./client";
import type { PgnPositionRequest, Position } from "./types";

/** The FEN after some half-moves of a game in a PGN, as a start position (E159). */
export async function positionFromPgn(request: PgnPositionRequest): Promise<string> {
  const position = await sendJson<Position>("POST", "/positions/from-pgn", request);
  return position.fen;
}
