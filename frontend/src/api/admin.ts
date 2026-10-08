import { getJson, sendJson } from "./client";
import type {
  BotDetail,
  BotUpdate,
  CreatedInvite,
  DisciplineRequest,
  DisciplineUpdate,
  EnqueueRequest,
  Invite,
  OneTimeLink,
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

/** Disables a verified or retired bot, or enables a disabled one (E93, E96). */
export function setBotStatus(id: string, status: BotUpdate["status"]): Promise<BotDetail> {
  return sendJson("PATCH", `/admin/bots/${encodeURIComponent(id)}`, { status });
}

/** Deletes this version for good with its files and matches (E105). */
export function deleteBot(id: string): Promise<undefined> {
  return sendJson("DELETE", `/admin/bots/${encodeURIComponent(id)}`);
}

export function createDiscipline(request: DisciplineRequest): Promise<StoredDiscipline> {
  return sendJson("POST", "/admin/disciplines", request);
}

/** Changes settings or archives a discipline; disciplines are never deleted (E100). */
export function updateDiscipline(id: string, change: DisciplineUpdate): Promise<StoredDiscipline> {
  return sendJson("PATCH", `/admin/disciplines/${encodeURIComponent(id)}`, change);
}
