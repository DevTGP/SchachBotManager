import { getJson, sendJson } from "./client";
import type { CurrentUser, SessionState } from "./types";

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
