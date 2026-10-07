import type { ErrorCode } from "./types";

export const API_BASE = "/api/v1";

/** network: the API did not answer or did not answer with JSON. */
export type FailureCode = ErrorCode | "network";

export class ApiError extends Error {
  readonly code: FailureCode;
  readonly status: number;

  constructor(code: FailureCode, status: number, message: string) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

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
  let response: Response;
  try {
    response = await fetch(apiUrl(path, query), {
      signal,
      headers: { Accept: "application/json" },
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ApiError("network", 0, String(error));
  }
  const body: unknown = await response.json().catch(() => undefined);
  if (response.ok && body !== undefined) return body as T;
  const failure = body as { code?: ErrorCode; message?: string } | undefined;
  throw new ApiError(
    failure?.code ?? "network",
    response.status,
    failure?.message ?? response.statusText,
  );
}
