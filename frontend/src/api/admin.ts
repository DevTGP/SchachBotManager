import { getJson, sendJson } from "./client";
import type {
  AuditPage,
  AuditQuery,
  BotDetail,
  BotLanguage,
  BotUpdate,
  CreatedInvite,
  DisciplineRequest,
  DisciplineUpdate,
  EnqueueRequest,
  Invite,
  OneTimeLink,
  PlaySettings,
  Role,
  StoredDiscipline,
  User,
  UserUpdate,
} from "./types";

export async function fetchUsers(signal?: AbortSignal): Promise<User[]> {
  const list = await getJson<{ items: User[] }>("/admin/users", undefined, signal);
  return list.items;
}

export function updateUser(id: string, change: UserUpdate): Promise<User> {
  return sendJson("PATCH", `/admin/users/${encodeURIComponent(id)}`, change);
}

export function createPasswordReset(id: string): Promise<OneTimeLink> {
  return sendJson("POST", `/admin/users/${encodeURIComponent(id)}/password-reset`);
}

export async function fetchInvites(signal?: AbortSignal): Promise<Invite[]> {
  const list = await getJson<{ items: Invite[] }>("/admin/invites", undefined, signal);
  return list.items;
}

export function createInvite(role: Role, validDays: number): Promise<CreatedInvite> {
  return sendJson("POST", "/admin/invites", { role, valid_days: validDays });
}

export function revokeInvite(id: string): Promise<undefined> {
  return sendJson("DELETE", `/admin/invites/${encodeURIComponent(id)}`);
}

/** The two bots and either a discipline or free times; the API fills in the rest (E100). */
export type MatchOrder = Pick<EnqueueRequest, "white_bot_id" | "black_bot_id"> &
  Partial<Omit<EnqueueRequest, "white_bot_id" | "black_bot_id">>;

export async function enqueueMatches(order: MatchOrder): Promise<string[]> {
  const result = await sendJson<{ match_ids: string[] }>("POST", "/admin/matches", order);
  return result.match_ids;
}

export async function setQueuePaused(paused: boolean): Promise<boolean> {
  const result = await sendJson<{ paused: boolean }>("PATCH", "/admin/queue", { paused });
  return result.paused;
}

export const MAX_PRIORITY = 1000;

/** Moves a waiting single game up or down the queue (E152). */
export async function setMatchPriority(id: string, priority: number): Promise<number> {
  const result = await sendJson<{ priority: number }>(
    "PATCH",
    `/admin/matches/${encodeURIComponent(id)}`,
    { priority },
  );
  return result.priority;
}

/** Aborts a waiting or running single game; it does not count (E152). */
export function cancelMatch(id: string): Promise<undefined> {
  return sendJson("POST", `/admin/matches/${encodeURIComponent(id)}/cancel`);
}

/** Queues an ended single game again with the bots and discipline as they are now (E152). */
export async function repeatMatch(id: string): Promise<string> {
  const result = await sendJson<{ match_ids: string[] }>(
    "POST",
    `/admin/matches/${encodeURIComponent(id)}/repeat`,
  );
  const [matchId] = result.match_ids;
  if (matchId === undefined) throw new Error("the repeat returned no match");
  return matchId;
}

/** Disables a verified or retired bot, or enables a disabled one (E93, E96). */
export function setBotStatus(id: string, status: BotUpdate["status"]): Promise<BotDetail> {
  return sendJson("PATCH", `/admin/bots/${encodeURIComponent(id)}`, { status });
}

/** Deletes this version for good with its files and matches (E105). */
export function deleteBot(id: string): Promise<undefined> {
  return sendJson("DELETE", `/admin/bots/${encodeURIComponent(id)}`);
}

/** Checks a bot again with the current rules; only a report is added, the status stays (E153). */
export function recheckBot(id: string): Promise<BotDetail> {
  return sendJson("POST", `/admin/bots/${encodeURIComponent(id)}/recheck`);
}

/** Checks every verified or rejected uploaded bot of a language again (E153). */
export async function recheckLanguage(language: BotLanguage): Promise<number> {
  const result = await sendJson<{ queued: number }>("POST", "/admin/bots/recheck", { language });
  return result.queued;
}

/** Verifies a rejected bot anyway; its rejection stays on record (E153). */
export function overrideBot(id: string): Promise<BotDetail> {
  return sendJson("POST", `/admin/bots/${encodeURIComponent(id)}/override`);
}

export function createDiscipline(request: DisciplineRequest): Promise<StoredDiscipline> {
  return sendJson("POST", "/admin/disciplines", request);
}

/** Changes settings or archives a discipline; disciplines are never deleted (E100). */
export function updateDiscipline(id: string, change: DisciplineUpdate): Promise<StoredDiscipline> {
  return sendJson("PATCH", `/admin/disciplines/${encodeURIComponent(id)}`, change);
}

export function fetchPlaySettings(signal?: AbortSignal): Promise<PlaySettings> {
  return getJson("/admin/play-settings", undefined, signal);
}

/** The limits of games against people and remote bots (E115). */
export function updatePlaySettings(settings: PlaySettings): Promise<PlaySettings> {
  return sendJson("PUT", "/admin/play-settings", settings);
}

/** The audit log, newest first; the filters are optional (E151). */
export function fetchAuditEntries(query: AuditQuery, signal?: AbortSignal): Promise<AuditPage> {
  return getJson("/admin/audit", query, signal);
}
