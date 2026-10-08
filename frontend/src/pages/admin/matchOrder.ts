import type { MatchOrder } from "../../api/admin";

/** The match form as typed: times in seconds, like the discipline names (E85). */
export interface MatchForm {
  white: string;
  black: string;
  initialSeconds: string;
  incrementSeconds: string;
  games: string;
  alternate: boolean;
  priority: string;
  maxMoves: string;
  startFen: string;
}

export const DEFAULT_FORM: Omit<MatchForm, "white" | "black"> = {
  initialSeconds: "180",
  incrementSeconds: "2",
  games: "1",
  alternate: false,
  priority: "100",
  maxMoves: "500",
  startFen: "",
};

/** The request body; the API checks the ranges and the position. */
export function matchOrder(form: MatchForm): MatchOrder {
  const fen = form.startFen.trim();
  return {
    white_bot_id: form.white,
    black_bot_id: form.black,
    initial_time_ms: secondsToMs(form.initialSeconds),
    increment_ms: secondsToMs(form.incrementSeconds),
    games: Number(form.games),
    alternate: form.alternate,
    priority: Number(form.priority),
    max_moves: Number(form.maxMoves),
    ...(fen ? { start_fen: fen } : {}),
  };
}

export function secondsToMs(seconds: string): number {
  return Math.round(Number(seconds.replace(",", ".")) * 1000);
}
