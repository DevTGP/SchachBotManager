import { apiUrl, getBytes, getJson, sendForm, sendJson } from "./client";
import type { Bot, BotDetail, OwnBotUpdate, OwnMatchRequest } from "./types";

/** A bot as the upload page collects it; paths are relative with /. */
export interface BotUpload {
  name: string;
  version: string;
  entry: string;
  description: string;
  files: { path: string; content: Blob }[];
}

function botPath(id: string): string {
  return `/bots/${encodeURIComponent(id)}`;
}

export function fetchBot(id: string, signal?: AbortSignal): Promise<BotDetail> {
  return getJson(botPath(id), undefined, signal);
}

/** Every bot of the logged-in account, newest first, in any status. */
export async function fetchOwnBots(signal?: AbortSignal): Promise<Bot[]> {
  const list = await getJson<{ items: Bot[] }>("/account/bots", undefined, signal);
  return list.items;
}

/** Stores the bot and queues its verification (E91, E92). */
export function uploadBot(upload: BotUpload): Promise<BotDetail> {
  const form = new FormData();
  form.append("name", upload.name);
  form.append("version", upload.version);
  form.append("language", "python");
  form.append("entry", upload.entry);
  if (upload.description) form.append("description", upload.description);
  for (const file of upload.files) {
    form.append("paths", file.path);
    // The part's file name does not count; the path does.
    form.append("files", file.content, "file");
  }
  return sendForm("POST", "/bots", form);
}

/** The owner changes the description or retires the bot and brings it back (E95, E96). */
export function updateOwnBot(id: string, change: OwnBotUpdate): Promise<BotDetail> {
  return sendJson("PATCH", botPath(id), change);
}

/** One file of the bot as a download, for owner and admins (E97). */
export function botFileUrl(id: string, path: string): string {
  return apiUrl(`${botPath(id)}/file`, { path });
}

export function fetchBotFile(id: string, path: string, signal?: AbortSignal): Promise<ArrayBuffer> {
  return getBytes(`${botPath(id)}/file`, { path }, signal);
}

/** All files of the bot as a ZIP file (E97). */
export function botSourceUrl(id: string): string {
  return apiUrl(`${botPath(id)}/source`);
}

/** Games of an own bot, with the tighter limits for coders (E98). */
export async function enqueueOwnMatches(order: OwnMatchRequest): Promise<string[]> {
  const result = await sendJson<{ match_ids: string[] }>("POST", "/matches", order);
  return result.match_ids;
}
