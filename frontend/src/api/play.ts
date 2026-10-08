import { sendJson } from "./client";
import type { PlayRequest, PlaySeat } from "./types";

/** Bot and color, and either a discipline or free times; the API fills in the rest. */
export type PlayOrder = Pick<PlayRequest, "bot_id" | "color"> &
  Partial<Omit<PlayRequest, "bot_id" | "color">>;

/** A game of the person against a verified bot; the answer names the seat (E114). */
export function startGame(order: PlayOrder): Promise<PlaySeat> {
  return sendJson("POST", "/play", order);
}
