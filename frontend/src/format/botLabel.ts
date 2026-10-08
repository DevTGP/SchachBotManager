import type { Bot } from "../api/types";

/** Uploaded bots have versions of one name (E91); a reference bot goes by its name. */
export function botLabel(bot: Pick<Bot, "name" | "version" | "builtin">): string {
  return bot.builtin ? bot.name : `${bot.name} ${bot.version}`;
}
