import { sendJson } from "./client";
import type { Tournament, TournamentRequest, TournamentUpdate } from "./types";

function adminPath(id: string): string {
  return `/admin/tournaments/${encodeURIComponent(id)}`;
}

/** A new tournament with its first edition planned (E170, E171). */
export function createTournament(request: TournamentRequest): Promise<Tournament> {
  return sendJson("POST", "/admin/tournaments", request);
}

/** Changes settings from the next edition start, or archives a tournament (E172). */
export function updateTournament(id: string, change: TournamentUpdate): Promise<Tournament> {
  return sendJson("PATCH", adminPath(id), change);
}

/** Starts the planned edition now instead of at its calendar date (E171). */
export function startTournament(id: string): Promise<Tournament> {
  return sendJson("POST", `${adminPath(id)}/start`);
}
