import { getJson, sendJson } from "./client";
import type { ApiToken, CreatedApiToken, CurrentUser, Rating, SessionState } from "./types";

export async function fetchSession(signal?: AbortSignal): Promise<CurrentUser | null> {
  const state = await getJson<SessionState>("/session", undefined, signal);
  return state.user;
}

export async function login(username: string, password: string): Promise<CurrentUser | null> {
  const state = await sendJson<SessionState>("POST", "/session", { username, password });
  return state.user;
}

export function logout(): Promise<undefined> {
  return sendJson("DELETE", "/session");
}

export async function redeemInvite(
  token: string,
  username: string,
  password: string,
): Promise<CurrentUser | null> {
  const body = { token, username, password };
  const state = await sendJson<SessionState>("POST", "/invites/redeem", body);
  return state.user;
}

export async function redeemPasswordReset(
  token: string,
  password: string,
): Promise<CurrentUser | null> {
  const state = await sendJson<SessionState>("POST", "/password-resets/redeem", {
    token,
    password,
  });
  return state.user;
}

export function changePassword(currentPassword: string, newPassword: string): Promise<undefined> {
  return sendJson("PUT", "/account/password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
}

/** The own rating from rated games against bots (E117); also in the public ranking (E118). */
export function fetchOwnRating(signal?: AbortSignal): Promise<Rating> {
  return getJson<Rating>("/account/rating", undefined, signal);
}

export async function fetchTokens(signal?: AbortSignal): Promise<ApiToken[]> {
  const list = await getJson<{ items: ApiToken[] }>("/account/tokens", undefined, signal);
  return list.items;
}

/** A token for remote bots; the answer is the only place the token appears (E116). */
export function createToken(name: string): Promise<CreatedApiToken> {
  return sendJson("POST", "/account/tokens", { name });
}

export function revokeToken(id: string): Promise<undefined> {
  return sendJson("DELETE", `/account/tokens/${encodeURIComponent(id)}`);
}
