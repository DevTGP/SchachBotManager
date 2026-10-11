import { getJson } from "./client";
import type { BotRecord, DisciplineRatingHistory } from "./types";

function botPath(botId: string): string {
  return `/bots/${encodeURIComponent(botId)}`;
}

/** The rating before and after each counted game per discipline, most games first (E140). */
export async function fetchRatingHistory(
  botId: string,
  signal?: AbortSignal,
): Promise<DisciplineRatingHistory[]> {
  const path = `${botPath(botId)}/rating-history`;
  const list = await getJson<{ items: DisciplineRatingHistory[] }>(path, undefined, signal);
  return list.items;
}

/** Wins, draws and losses in total and per discipline (E141). */
export function fetchBotRecord(botId: string, signal?: AbortSignal): Promise<BotRecord> {
  return getJson(`${botPath(botId)}/record`, undefined, signal);
}
