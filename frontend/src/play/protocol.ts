/**
 * The messages of a game in the browser: gateway-v1 to take the seat, then play-v1
 * (spec/protocol/gateway-v1, play-v1). The browser has no chess rules; it offers only the legal
 * moves the server sends (E114).
 */

export const SOCKET_PATH = "/api/v1/play/socket";

export type PlayColor = "white" | "black";

export interface PlayState {
  type: "state";
  v: 1;
  color: PlayColor;
  white: string;
  black: string;
  start_fen: string;
  fen: string;
  /** UCI moves separated by spaces. */
  moves: string;
  /** The same moves in SAN, separated by spaces. */
  san: string;
  clock: Record<PlayColor, number>;
  running: PlayColor | null;
  increment_ms: number;
  /** The person's legal moves in UCI, separated by spaces; empty unless it is their turn. */
  legal_moves: string;
  result: string | null;
  termination: string | null;
}

export type ServerMessage =
  | { type: "joined" }
  | { type: "refused"; code: string }
  | { type: "error"; code: string }
  | PlayState;

/** The message, or undefined for anything the browser does not know. */
export function parseServerMessage(text: string): ServerMessage | undefined {
  let message: unknown;
  try {
    message = JSON.parse(text);
  } catch {
    return undefined;
  }
  if (typeof message !== "object" || message === null) return undefined;
  const { type } = message as { type?: unknown };
  if (type === "joined" || type === "refused" || type === "error" || type === "state") {
    return message as ServerMessage;
  }
  return undefined;
}

export function joinMessage(matchId: string, seat: string): string {
  return JSON.stringify({ type: "join", v: 1, match_id: matchId, seat });
}

export function moveMessage(uci: string): string {
  return JSON.stringify({ type: "move", v: 1, move: uci });
}

export function resignMessage(): string {
  return JSON.stringify({ type: "resign", v: 1 });
}

export function splitMoves(list: string): string[] {
  return list ? list.split(" ") : [];
}

/** The legal moves from one square to another: one move, or four for a promotion. */
export function movesBetween(legal: string[], from: string, to: string): string[] {
  return legal.filter((move) => move.slice(0, 4) === `${from}${to}`);
}

/** The remaining time of a side now, counting down the running clock since the state came. */
export function remainingMs(state: PlayState, color: PlayColor, elapsedMs: number): number {
  const remaining = state.clock[color] - (state.running === color ? elapsedMs : 0);
  return Math.max(0, remaining);
}
