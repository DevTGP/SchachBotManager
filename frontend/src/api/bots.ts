import { getJson, sendForm } from "./client";
import type { Bot, BotDetail } from "./types";

/** A bot as the upload page collects it; paths are relative with /. */
export interface BotUpload {
  name: string;
  version: string;
  entry: string;
  files: { path: string; content: Blob }[];
}

export function fetchBot(id: string, signal?: AbortSignal): Promise<BotDetail> {
  return getJson(`/bots/${encodeURIComponent(id)}`, undefined, signal);
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
  for (const file of upload.files) {
    form.append("paths", file.path);
    // The part's file name does not count; the path does.
    form.append("files", file.content, "file");
  }
  return sendForm("POST", "/bots", form);
}
