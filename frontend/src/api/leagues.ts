import { getJson, sendJson } from "./client";
import type { League, LeagueDetail, LeagueRegistration, Season } from "./types";

function leaguePath(id: string): string {
  return `/leagues/${encodeURIComponent(id)}`;
}

/** All leagues by name, archived ones too (E137). */
export async function fetchLeagues(signal?: AbortSignal): Promise<League[]> {
  const list = await getJson<{ items: League[] }>("/leagues", undefined, signal);
  return list.items;
}

/** A league with its seasons, newest first, and its registrations (E137). */
export function fetchLeague(id: string, signal?: AbortSignal): Promise<LeagueDetail> {
  return getJson(leaguePath(id), undefined, signal);
}

/** A season with the tables of its tiers (E135, E137). */
export function fetchSeason(id: string, signal?: AbortSignal): Promise<Season> {
  return getJson(`/seasons/${encodeURIComponent(id)}`, undefined, signal);
}

/** The leagues a bot is registered in (E136). */
export async function fetchBotLeagues(
  botId: string,
  signal?: AbortSignal,
): Promise<LeagueRegistration[]> {
  const path = `/bots/${encodeURIComponent(botId)}/leagues`;
  const list = await getJson<{ items: LeagueRegistration[] }>(path, undefined, signal);
  return list.items;
}

/** Owner or admin registers a verified bot; it plays from the next season start (E136). */
export function registerBot(leagueId: string, botId: string): Promise<LeagueRegistration> {
  return sendJson("POST", `${leaguePath(leagueId)}/registrations`, { bot_id: botId });
}

/** Leaves the league; its waiting games in a running season are lost by forfeit (E136). */
export function deregisterBot(leagueId: string, botId: string): Promise<undefined> {
  return sendJson("DELETE", `${leaguePath(leagueId)}/registrations/${encodeURIComponent(botId)}`);
}
