import { useTranslation } from "react-i18next";

import type { Bot } from "../api/types";
import { botLabel } from "../format/botLabel";

/** Instead of a bot id: the server draws a verified bot for every game (E162). */
export const RANDOM_BOT = "random";

/** The options of a bot select, led by "Random" if a drawn bot is allowed. */
export function BotOptions({ bots, random = false }: { bots: Bot[]; random?: boolean }) {
  const { t } = useTranslation();
  return (
    <>
      {random && <option value={RANDOM_BOT}>{t("botChoice.random")}</option>}
      {bots.map((bot) => (
        <option key={bot.id} value={bot.id}>
          {botLabel(bot)}
        </option>
      ))}
    </>
  );
}
