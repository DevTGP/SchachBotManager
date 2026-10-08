import type { Bot, MatchSummary, Side } from "../api/types";

/** Uploaded bots have versions of one name (E91); a reference bot goes by its name. */
export function botLabel(bot: Pick<Bot, "name" | "version" | "builtin">): string {
  return bot.builtin ? bot.name : `${bot.name} ${bot.version}`;
}

/** A side as "Name Version" (E95); games queued before versions were kept show the name. */
export function sideLabel(side: Pick<Side, "name" | "version">): string {
  return side.version ? `${side.name} ${side.version}` : side.name;
}

export function playersLabel(match: Pick<MatchSummary, "white" | "black">): string {
  return `${sideLabel(match.white)} – ${sideLabel(match.black)}`;
}
