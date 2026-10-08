import { apiUrl, getJson } from "./client";
import type { Bot, Match, MatchPage, MatchStatus, Queue, StoredDiscipline } from "./types";

export interface MatchQuery {
  status?: MatchStatus;
  botId?: string;
  limit?: number;
  offset?: number;
}

export function fetchMatches(query: MatchQuery, signal?: AbortSignal): Promise<MatchPage> {
  const { status, botId, limit, offset } = query;
  return getJson("/matches", { status, bot_id: botId, limit, offset }, signal);
}

export function fetchMatch(id: string, signal?: AbortSignal): Promise<Match> {
  return getJson(`/matches/${encodeURIComponent(id)}`, undefined, signal);
}

export function matchPgnUrl(id: string): string {
  return apiUrl(`/matches/${encodeURIComponent(id)}/pgn`);
}

export async function fetchBots(signal?: AbortSignal): Promise<Bot[]> {
  const list = await getJson<{ items: Bot[] }>("/bots", undefined, signal);
  return list.items;
}

export function fetchQueue(signal?: AbortSignal): Promise<Queue> {
  return getJson("/queue", undefined, signal);
}

/** All disciplines by name, archived ones too (E100). */
export async function fetchDisciplines(signal?: AbortSignal): Promise<StoredDiscipline[]> {
  const list = await getJson<{ items: StoredDiscipline[] }>("/disciplines", undefined, signal);
  return list.items;
}
