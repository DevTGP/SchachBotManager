import type { OwnMatchOrder } from "../../api/bots";
import { secondsToMs } from "../admin/matchOrder";

/** The limits for games set by coders (E98). */
export const OWN_LIMITS = { initialSeconds: 300, incrementSeconds: 5, games: 10 };

/** The form as typed: an own bot, any verified opponent, times in seconds. */
export interface OwnMatchForm {
  own: string;
  opponent: string;
  ownColor: "white" | "black";
  /** The id of a discipline, or "" for free times within OWN_LIMITS (E100). */
  discipline: string;
  initialSeconds: string;
  incrementSeconds: string;
  games: string;
  alternate: boolean;
}

export const DEFAULT_OWN_FORM: Omit<OwnMatchForm, "own" | "opponent"> = {
  ownColor: "white",
  discipline: "",
  initialSeconds: "60",
  incrementSeconds: "1",
  games: "2",
  alternate: true,
};

/** The request body; the API checks the ranges and that one bot is the own one. */
export function ownMatchOrder(form: OwnMatchForm): OwnMatchOrder {
  const [white, black] =
    form.ownColor === "white" ? [form.own, form.opponent] : [form.opponent, form.own];
  const conditions = form.discipline
    ? { discipline_id: form.discipline }
    : {
        initial_time_ms: secondsToMs(form.initialSeconds),
        increment_ms: secondsToMs(form.incrementSeconds),
      };
  return {
    white_bot_id: white,
    black_bot_id: black,
    ...conditions,
    games: Number(form.games),
    alternate: form.alternate,
  };
}
