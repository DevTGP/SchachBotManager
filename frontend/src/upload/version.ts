// Bot names and version numbers as the API takes them (E91).

import type { Bot } from "../api/types";

export const FIRST_VERSION = "1.0.0";
export const NAME = /^[A-Za-z0-9][A-Za-z0-9_.-]{2,31}$/;
const VERSION = /^(0|[1-9]\d{0,2})\.(0|[1-9]\d{0,2})\.(0|[1-9]\d{0,2})$/;

type Parts = [number, number, number];

export function parseVersion(text: string): Parts | undefined {
  const match = VERSION.exec(text);
  return match ? [Number(match[1]), Number(match[2]), Number(match[3])] : undefined;
}

function compare(a: Parts, b: Parts): number {
  return a[0] - b[0] || a[1] - b[1] || a[2] - b[2];
}

/**
 * The version after the latest own bot of that name with the last part raised, 1.0.0 for a new
 * name, and empty when the last part is already 999.
 */
export function suggestVersion(ownBots: Bot[], name: string): string {
  const key = name.toLowerCase();
  let latest: Parts | undefined;
  for (const bot of ownBots) {
    const parts = bot.name.toLowerCase() === key ? parseVersion(bot.version) : undefined;
    if (parts && (!latest || compare(parts, latest) > 0)) latest = parts;
  }
  if (!latest) return FIRST_VERSION;
  const [major, minor, patch] = latest;
  return patch === 999 ? "" : `${major}.${minor}.${patch + 1}`;
}
