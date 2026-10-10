import { apiUrl, getJson } from "./client";
import type {
  Bot,
  Match,
  MatchKind,
  MatchPage,
  MatchStatus,
  Opponent,
  PlayerRating,
  Queue,
  Series,
  StoredDiscipline,
} from "./types";

export interface MatchQuery {
  status?: MatchStatus;
  kind?: MatchKind;
  botId?: string;
  /** Only with botId: the games of both bots against each other (E156). */
  opponentId?: string;
  disciplineId?: string;
  /** Only the games the signed-in account set; needs a session (E156). */
  mine?: boolean;
  limit?: number;
  offset?: number;
}

export function fetchMatches(query: MatchQuery, signal?: AbortSignal): Promise<MatchPage> {
  const { status, kind, botId, opponentId, disciplineId, mine, limit, offset } = query;
  return getJson(
    "/matches",
    {
      status,
      kind,
      bot_id: botId,
      opponent_id: opponentId,
      discipline_id: disciplineId,
      mine: mine ? "true" : undefined,
      limit,
      offset,
    },
    signal,
  );
}

/** The games of one request with two or more games and its score (E155). */
export function fetchSeries(id: string, signal?: AbortSignal): Promise<Series> {
  return getJson(`/series/${encodeURIComponent(id)}`, undefined, signal);
}

/** Every opponent bot of a bot with wins, draws and losses from its side (E161). */
export async function fetchOpponents(botId: string, signal?: AbortSignal): Promise<Opponent[]> {
  const path = `/bots/${encodeURIComponent(botId)}/opponents`;
  const list = await getJson<{ items: Opponent[] }>(path, undefined, signal);
  return list.items;
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
