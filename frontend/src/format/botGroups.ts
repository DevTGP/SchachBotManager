import type { Bot } from "../api/types";

/** The versions of one bot name, newest first; a new version is a new bot (E165). */
export interface BotGroup {
  name: string;
  versions: Bot[];
}

/** Groups bots by name in the order the names come first; versions newest first. */
export function botGroups(bots: Bot[]): BotGroup[] {
  const groups = new Map<string, Bot[]>();
  for (const bot of bots) {
    const versions = groups.get(bot.name);
    if (versions) versions.push(bot);
    else groups.set(bot.name, [bot]);
  }
  return [...groups].map(([name, versions]) => ({
    name,
    versions: [...versions].sort((a, b) => b.created_at.localeCompare(a.created_at)),
  }));
}
