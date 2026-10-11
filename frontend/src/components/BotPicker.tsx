import { useTranslation } from "react-i18next";

import type { Bot } from "../api/types";
import { botGroups } from "../format/botGroups";

/** Instead of a bot id: the server draws a verified bot for every game (E162). */
export const RANDOM_BOT = "random";

/**
 * A bot chosen by name, then by version if the name has several; a new name takes its newest
 * version. Names carry no versions (E165). The value stays the bot id, "random" or "" for the
 * leading empty choice of a filter.
 */
export function BotPicker({
  label,
  bots,
  value,
  onChange,
  random = false,
  empty,
}: {
  label: string;
  bots: Bot[];
  value: string;
  onChange: (value: string) => void;
  random?: boolean;
  /** The text of an empty choice, e.g. "all bots" in a filter. */
  empty?: string;
}) {
  const { t } = useTranslation();
  const groups = botGroups(bots);
  const group = groups.find((entry) => entry.versions.some((bot) => bot.id === value));
  const nameValue = group?.name ?? (value === RANDOM_BOT ? RANDOM_BOT : "");

  function chooseName(name: string) {
    if (name === RANDOM_BOT || name === "") onChange(name);
    else onChange(groups.find((entry) => entry.name === name)?.versions[0]?.id ?? "");
  }

  return (
    <>
      <label>
        {label}
        <select value={nameValue} onChange={(event) => chooseName(event.target.value)}>
          {empty !== undefined && <option value="">{empty}</option>}
          {random && <option value={RANDOM_BOT}>{t("botChoice.random")}</option>}
          {groups.map((entry) => (
            <option key={entry.name} value={entry.name}>
              {entry.name}
            </option>
          ))}
        </select>
      </label>
      {group && group.versions.length > 1 && (
        <label>
          {t("botChoice.version", { name: group.name })}
          <select value={value} onChange={(event) => onChange(event.target.value)}>
            {group.versions.map((bot) => (
              <option key={bot.id} value={bot.id}>
                {bot.version ?? "–"}
              </option>
            ))}
          </select>
        </label>
      )}
    </>
  );
}
