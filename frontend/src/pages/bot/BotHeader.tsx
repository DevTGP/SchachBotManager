import { useTranslation } from "react-i18next";

import type { BotDetail } from "../../api/types";
import { BotStatusBadge } from "../../components/BotStatusBadge";
import { ratingText } from "../../format/rating";

/** Name as heading, then version, owner, language, state and rating at a glance (G6, E165). */
export function BotHeader({ bot }: { bot: BotDetail }) {
  const { t } = useTranslation();
  const owner = bot.builtin ? t("bots.builtin") : (bot.details?.owner ?? bot.owner);
  return (
    <header className="page-header">
      <h1>{bot.name}</h1>
      <ul className="page-facts">
        {bot.version && <li>{t("bot.versionValue", { version: bot.version })}</li>}
        {owner && <li>{owner}</li>}
        <li>{t(`language.${bot.language}`)}</li>
        <li>
          <BotStatusBadge status={bot.status} />
        </li>
        <li>{t("bot.ratingValue", { value: ratingText(bot.rating), count: bot.rating.games })}</li>
      </ul>
    </header>
  );
}
