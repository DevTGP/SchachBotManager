import type { SettingsGroups } from "../../api/admin";
import { secondsToMs } from "./matchOrder";

/** One number of a group; times in milliseconds are typed in seconds. */
export interface SettingsField<G extends keyof SettingsGroups> {
  name: keyof SettingsGroups[G] & string;
  min: number;
  max: number;
  seconds?: boolean;
}

type Fields = { [G in keyof SettingsGroups]: readonly SettingsField<G>[] };

/** The fields of /admin/settings with the ranges the API accepts (E154). */
export const SETTINGS_FIELDS: Fields = {
  coders: [
    { name: "games_per_day", min: 1, max: 1000 },
    { name: "uploads_per_day", min: 1, max: 1000 },
    { name: "games_per_request", min: 1, max: 100 },
    { name: "max_initial_ms", min: 1, max: 3600, seconds: true },
    { name: "max_increment_ms", min: 0, max: 60, seconds: true },
    { name: "priority", min: 0, max: 99 },
  ],
  accounts: [
    { name: "invite_days", min: 1, max: 365 },
    { name: "invite_max_days", min: 1, max: 365 },
    { name: "login_failures", min: 1, max: 100 },
  ],
  rating: [
    { name: "start", min: 0, max: 10_000 },
    { name: "base", min: 1, max: 1000 },
    { name: "step", min: 1, max: 1000 },
    { name: "max_win", min: 1, max: 1000 },
    { name: "min_win", min: 0, max: 1000 },
    { name: "max_draw", min: 0, max: 1000 },
  ],
  estimate: [
    { name: "recent_games", min: 1, max: 200 },
    { name: "moves_per_game", min: 1, max: 1000 },
  ],
};

export const SETTINGS_GROUPS = ["coders", "accounts", "rating", "estimate"] as const;

/** The values of a group as typed in the form. */
export function toForm<G extends keyof SettingsGroups>(
  group: G,
  values: SettingsGroups[G],
): Record<string, string> {
  const fields: readonly SettingsField<G>[] = SETTINGS_FIELDS[group];
  return Object.fromEntries(
    fields.map(({ name, seconds }) => {
      const value = Number(values[name]);
      return [name, String(seconds ? value / 1000 : value)];
    }),
  );
}

/** The request body of a group from the form. */
export function fromForm<G extends keyof SettingsGroups>(
  group: G,
  form: Record<string, string>,
): SettingsGroups[G] {
  const fields: readonly SettingsField<G>[] = SETTINGS_FIELDS[group];
  return Object.fromEntries(
    fields.map(({ name, seconds }) => {
      const typed = form[name] ?? "";
      return [name, seconds ? secondsToMs(typed) : Number(typed)];
    }),
  ) as SettingsGroups[G];
}
