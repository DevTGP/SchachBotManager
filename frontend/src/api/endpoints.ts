import { apiUrl, getJson } from "./client";
import type {
  Bot,
  Match,
  MatchKind,
  MatchPage,
  MatchStatus,
  PlayerRating,
  Queue,
  StoredDiscipline,
} from "./types";

export interface MatchQuery {
  status?: MatchStatus;
  kind?: MatchKind;
  botId?: string;
  limit?: number;
  offset?: number;
}

export function fetchMatches(query: MatchQuery, signal?: AbortSignal): Promise<MatchPage> {
  const { status, kind, botId, limit, offset } = query;
  return getJson("/matches", { status, kind, bot_id: botId, limit, offset }, signal);
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

/** Public bots with at least one counted match, highest rating first (E103). */
export async function fetchRatings(signal?: AbortSignal): Promise<Bot[]> {
  const list = await getJson<{ items: Bot[] }>("/ratings", undefined, signal);
  return list.items;
}

/** Active accounts with at least one counted game against bots, highest rating first (E118). */
export async function fetchPlayerRatings(signal?: AbortSignal): Promise<PlayerRating[]> {
  const list = await getJson<{ items: PlayerRating[] }>("/ratings/players", undefined, signal);
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
