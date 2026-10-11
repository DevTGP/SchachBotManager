import { getJson, sendJson } from "./client";
import type {
  BotSeason,
  League,
  LeagueDetail,
  LeagueRegistration,
  Season,
  SeasonSchedule,
} from "./types";

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

/** The rounds of one tier of a started season with the state of each game (E138). */
export function fetchSeasonSchedule(
  id: string,
  tier: number,
  signal?: AbortSignal,
): Promise<SeasonSchedule> {
  return getJson(`/seasons/${encodeURIComponent(id)}/schedule`, { tier }, signal);
}

/** The seasons this bot version played in, newest first, with its place there (E139). */
export async function fetchBotSeasons(botId: string, signal?: AbortSignal): Promise<BotSeason[]> {
  const path = `/bots/${encodeURIComponent(botId)}/seasons`;
  const list = await getJson<{ items: BotSeason[] }>(path, undefined, signal);
  return list.items;
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

/** An account joins itself, an admin any active account (E182). */
export function registerAccount(leagueId: string, userId: string): Promise<LeagueRegistration> {
  return sendJson("POST", `${leaguePath(leagueId)}/registrations`, { user_id: userId });
}

/**
 * A bot or an account leaves the league by its participant id; its waiting games in a running
 * season are lost by forfeit (E136, E182).
 */
export function deregisterParticipant(leagueId: string, participantId: string): Promise<undefined> {
  const path = `${leaguePath(leagueId)}/registrations/${encodeURIComponent(participantId)}`;
  return sendJson("DELETE", path);
}
