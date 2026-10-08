import type { OwnMatchRequest } from "../../api/types";
import { secondsToMs } from "../admin/matchOrder";

/** The limits for games set by coders (E98). */
export const OWN_LIMITS = { initialSeconds: 300, incrementSeconds: 5, games: 10 };

/** The form as typed: an own bot, any verified opponent, times in seconds. */
export interface OwnMatchForm {
  own: string;
  opponent: string;
  ownColor: "white" | "black";
  initialSeconds: string;
  incrementSeconds: string;
  games: string;
  alternate: boolean;
}

export const DEFAULT_OWN_FORM: Omit<OwnMatchForm, "own" | "opponent"> = {
  ownColor: "white",
  initialSeconds: "60",
  incrementSeconds: "1",
  games: "2",
  alternate: true,
};

/** The request body; the API checks the ranges and that one bot is the own one. */
export function ownMatchOrder(form: OwnMatchForm): OwnMatchRequest {
  const [white, black] =
    form.ownColor === "white" ? [form.own, form.opponent] : [form.opponent, form.own];
  return {
    white_bot_id: white,
    black_bot_id: black,
    initial_time_ms: secondsToMs(form.initialSeconds),
    increment_ms: secondsToMs(form.incrementSeconds),
    games: Number(form.games),
    alternate: form.alternate,
  };
}
