import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { fetchBots } from "../api/endpoints";
import type { Bot } from "../api/types";
import { ApiContent } from "../components/ApiContent";
import { SideName } from "../components/SideName";
import { TableShell } from "../components/TableShell";
import { formatDateTime } from "../format/dateTime";
import { ratingText } from "../format/rating";
import { useApi } from "../hooks/useApi";
import { useLocale } from "../hooks/useLocale";

export function BotsPage() {
  const { t } = useTranslation();
  const bots = useApi(fetchBots, "bots");
  return (
    <>
      <h1>{t("bots.title")}</h1>
      <ApiContent state={bots}>{(items) => <BotTable bots={items} />}</ApiContent>
    </>
  );
}

/**
 * Every bot version with the version in its own column; the language only when bots of several
 * languages exist, and the number of games leads to them (G12, E165).
 */
function BotTable({ bots }: { bots: Bot[] }) {
  const { t } = useTranslation();
  const locale = useLocale();
  const languages = new Set(bots.map((bot) => bot.language)).size > 1;
  return (
    <TableShell rows={bots.length} empty={t("bots.empty")}>
      <thead>
        <tr>
          <th>{t("bots.name")}</th>
          <th>{t("bots.version")}</th>
          <th>{t("bots.owner")}</th>
          {languages && <th className="optional">{t("bots.language")}</th>}
          <th className="number">{t("bots.rating")}</th>
          <th className="number">{t("bots.ratedGames")}</th>
          <th className="optional">{t("bots.created")}</th>
        </tr>
      </thead>
      <tbody>
        {bots.map((bot) => (
          <tr key={bot.id}>
            <td>
              <SideName side={{ bot_id: bot.id, name: bot.name, version: null }} />
            </td>
            <td>{bot.version}</td>
            <td>{bot.builtin ? t("bots.builtin") : (bot.owner ?? t("common.none"))}</td>
            {languages && <td className="optional">{t(`language.${bot.language}`)}</td>}
            <td className="number">{ratingText(bot.rating)}</td>
            <td className="number">
              <Link to={`/matches?bot=${bot.id}`}>{bot.rating.games}</Link>
            </td>
            <td className="optional">{formatDateTime(bot.created_at, locale)}</td>
          </tr>
        ))}
      </tbody>
    </TableShell>
  );
}
