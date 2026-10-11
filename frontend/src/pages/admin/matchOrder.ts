import type { MatchOrder } from "../../api/admin";
import {
  DEFAULT_CONDITIONS,
  type MatchConditions,
  seriesConditions,
  timeConditions,
} from "../../components/matchFields/conditions";

/** The admin form as typed: two bots or "random" (E162), times in seconds (E85). */
export interface MatchForm extends MatchConditions {
  white: string;
  black: string;
}

export const DEFAULT_FORM = DEFAULT_CONDITIONS.admin;

/** The request body; the API checks the ranges and the position. */
export function matchOrder(form: MatchForm): MatchOrder {
  return {
    white_bot_id: form.white,
    black_bot_id: form.black,
    ...timeConditions(form, "admin"),
    ...seriesConditions(form),
    priority: Number(form.priority),
  };
}
