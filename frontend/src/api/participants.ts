import type { LeagueBot } from "./types";

/** The id a registration goes by: the bot's for a bot, the account's for a person (E182). */
export function participantId(participant: LeagueBot): string {
  return participant.bot_id ?? participant.user_id ?? "";
}
