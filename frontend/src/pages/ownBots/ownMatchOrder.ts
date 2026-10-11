import type { OwnMatchOrder } from "../../api/bots";
import {
  DEFAULT_CONDITIONS,
  type MatchConditions,
  seriesConditions,
  timeConditions,
} from "../../components/matchFields/conditions";

/** The form as typed: an own bot, any verified opponent or "random" (E162), times in seconds. */
export interface OwnMatchForm extends MatchConditions {
  own: string;
  opponent: string;
  ownColor: "white" | "black";
}

export const DEFAULT_OWN_FORM = { ...DEFAULT_CONDITIONS.coder, ownColor: "white" as const };

/** The request body; the API checks the ranges and that one bot is the own one. */
export function ownMatchOrder(form: OwnMatchForm): OwnMatchOrder {
  const [white, black] =
    form.ownColor === "white" ? [form.own, form.opponent] : [form.opponent, form.own];
  return {
    white_bot_id: white,
    black_bot_id: black,
    ...timeConditions(form, "coder"),
    ...seriesConditions(form),
  };
}
