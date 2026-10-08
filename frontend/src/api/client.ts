import type { ErrorCode } from "./types";

export const API_BASE = "/api/v1";

/** network: the API did not answer or did not answer with JSON. */
export type FailureCode = ErrorCode | "network";

export class ApiError extends Error {
  readonly code: FailureCode;
  readonly status: number;
  /** The invalid parameter, for invalid_parameter. */
  readonly field: string | undefined;
  /** The file to blame, for invalid_upload. */
  readonly path: string | undefined;

  constructor(code: FailureCode, status: number, message: string, field?: string, path?: string) {
    super(message);
    this.code = code;
    this.status = status;
    this.field = field;
    this.path = path;
  }
}

/** Every request other than GET carries it; a cross-site form cannot set it (E84). */
export const CSRF_HEADER = { "X-SBM-CSRF": "1" };

type Query = Record<string, string | number | undefined>;

export function apiUrl(path: string, query: Query = {}): string {
  const params = new URLSearchParams();
  for (const [name, value] of Object.entries(query)) {
    if (value !== undefined) params.set(name, String(value));
  }
  const search = params.toString();
  return `${API_BASE}${path}${search ? `?${search}` : ""}`;
}

export async function getJson<T>(path: string, query?: Query, signal?: AbortSignal): Promise<T> {
  const response = await request(apiUrl(path, query), { signal }, signal);
  return (await readBody(response)) as T;
}

/** The raw bytes of a download; a failure still answers with a JSON error. */
export async function getBytes(
  path: string,
  query?: Query,
  signal?: AbortSignal,
): Promise<ArrayBuffer> {
  const response = await request(
    apiUrl(path, query),
    { signal, headers: { Accept: "*/*" } },
    signal,
  );
  if (!response.ok) await readBody(response);
  return response.arrayBuffer();
}

/** A change; answers without content (204) give undefined. */
export async function sendJson<T = undefined>(
  method: "POST" | "PUT" | "PATCH" | "DELETE",
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = { ...CSRF_HEADER };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const response = await request(apiUrl(path), {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (response.status === 204) return undefined as T;
  return (await readBody(response)) as T;
}

/** A multipart body; the browser sets its Content-Type with the boundary. */
export async function sendForm<T>(method: "POST", path: string, form: FormData): Promise<T> {
  const response = await request(apiUrl(path), { method, headers: CSRF_HEADER, body: form });
  return (await readBody(response)) as T;
}

async function request(url: string, init: RequestInit, signal?: AbortSignal): Promise<Response> {
  try {
    return await fetch(url, {
      ...init,
      headers: { Accept: "application/json", ...init.headers },
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ApiError("network", 0, String(error));
  }
}

async function readBody(response: Response): Promise<unknown> {
  const body: unknown = await response.json().catch(() => undefined);
  if (response.ok && body !== undefined) return body;
  const failure = body as
    { code?: ErrorCode; message?: string; field?: string; path?: string } | undefined;
  throw new ApiError(
    failure?.code ?? "network",
    response.status,
    failure?.message ?? response.statusText,
    failure?.field,
    failure?.path,
  );
}
