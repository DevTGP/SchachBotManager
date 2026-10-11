import { getJson, sendJson } from "./client";
import type {
  BotEdition,
  Edition,
  EditionRounds,
  Tournament,
  TournamentDetail,
  TournamentRegistration,
} from "./types";

function tournamentPath(id: string): string {
  return `/tournaments/${encodeURIComponent(id)}`;
}

function editionPath(id: string): string {
  return `/editions/${encodeURIComponent(id)}`;
}

/** All tournaments by name, archived ones too (E180). */
export async function fetchTournaments(signal?: AbortSignal): Promise<Tournament[]> {
  const list = await getJson<{ items: Tournament[] }>("/tournaments", undefined, signal);
  return list.items;
}

/** A tournament with its editions, newest first, and its registrations (E180). */
export function fetchTournament(id: string, signal?: AbortSignal): Promise<TournamentDetail> {
  return getJson(tournamentPath(id), undefined, signal);
}

/** An edition with its table or its bracket (E177, E180). */
export function fetchEdition(id: string, signal?: AbortSignal): Promise<Edition> {
  return getJson(editionPath(id), undefined, signal);
}

/** The rounds of a round robin or Swiss edition with the state of each game (E180). */
export function fetchEditionRounds(id: string, signal?: AbortSignal): Promise<EditionRounds> {
  return getJson(`${editionPath(id)}/rounds`, undefined, signal);
}

/** The editions this bot version played in, newest first, with its place there (E180). */
export async function fetchBotEditions(botId: string, signal?: AbortSignal): Promise<BotEdition[]> {
  const path = `/bots/${encodeURIComponent(botId)}/editions`;
  const list = await getJson<{ items: BotEdition[] }>(path, undefined, signal);
  return list.items;
}

/** The tournaments a bot is registered in (E179). */
export async function fetchBotTournaments(
  botId: string,
  signal?: AbortSignal,
): Promise<TournamentRegistration[]> {
  const path = `/bots/${encodeURIComponent(botId)}/tournaments`;
  const list = await getJson<{ items: TournamentRegistration[] }>(path, undefined, signal);
  return list.items;
}

/** Owner or admin registers a verified bot; it plays from the next edition start (E179). */
export function registerTournamentBot(
  tournamentId: string,
  botId: string,
): Promise<TournamentRegistration> {
  return sendJson("POST", `${tournamentPath(tournamentId)}/registrations`, { bot_id: botId });
}

/** Leaves the tournament; its waiting games in a running edition are lost by forfeit (E179). */
export function deregisterTournamentBot(tournamentId: string, botId: string): Promise<undefined> {
  const path = `${tournamentPath(tournamentId)}/registrations/${encodeURIComponent(botId)}`;
  return sendJson("DELETE", path);
}
