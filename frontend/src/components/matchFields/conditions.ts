import { minutesToMs, secondsToMs } from "../../format/duration";

/**
 * Who sets the game: admins with priority and move limit, coders within their limits, people on
 * /play with time in minutes and nothing else (E167).
 */
export type MatchFieldsVariant = "admin" | "coder" | "play";

/** The conditions of a game as typed, the same for every form that sets games (E167). */
export interface MatchConditions {
  /** The id of a discipline, or "" for free times (E100). */
  discipline: string;
  /** Seconds, on /play minutes. */
  initial: string;
  incrementSeconds: string;
  maxMoves: string;
  games: string;
  alternate: boolean;
  priority: string;
  /** FEN, or "" for the standard position; another one makes the games unrated (E159). */
  startFen: string;
  /** The wish for a rated game; the API decides (E158). */
  rated: boolean;
}

const COMMON = { discipline: "", maxMoves: "500", priority: "100", startFen: "", rated: true };

export const DEFAULT_CONDITIONS: Record<MatchFieldsVariant, MatchConditions> = {
  admin: { ...COMMON, initial: "180", incrementSeconds: "2", games: "1", alternate: false },
  coder: { ...COMMON, initial: "60", incrementSeconds: "1", games: "2", alternate: true },
  play: { ...COMMON, initial: "5", incrementSeconds: "3", games: "1", alternate: false },
};

export type TimeConditions =
  { discipline_id: string } | { initial_time_ms: number; increment_ms: number; max_moves?: number };

/** A discipline, or free times in milliseconds; only admins set a move limit. */
export function timeConditions(form: MatchConditions, variant: MatchFieldsVariant): TimeConditions {
  if (form.discipline) return { discipline_id: form.discipline };
  const initial = variant === "play" ? minutesToMs(form.initial) : secondsToMs(form.initial);
  const times = { initial_time_ms: initial, increment_ms: secondsToMs(form.incrementSeconds) };
  return variant === "admin" ? { ...times, max_moves: Number(form.maxMoves) } : times;
}

/** Number of games, alternation, rating wish and a trimmed start position if one is set. */
export function seriesConditions(form: MatchConditions) {
  const fen = form.startFen.trim();
  return {
    games: Number(form.games),
    alternate: form.alternate,
    rated: form.rated,
    ...(fen ? { start_fen: fen } : {}),
  };
}
