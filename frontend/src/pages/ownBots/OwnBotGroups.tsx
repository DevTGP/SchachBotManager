import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { Bot } from "../../api/types";
import { BotStatusBadge } from "../../components/BotStatusBadge";
import { TableShell } from "../../components/TableShell";
import { formatDateTime } from "../../format/dateTime";
import { ratingText } from "../../format/rating";
import { useLocale } from "../../hooks/useLocale";

/** The bots grouped by name, in the order of their newest version (E95). */
function groupByName(bots: Bot[]): [string, Bot[]][] {
  const groups = new Map<string, Bot[]>();
  for (const bot of bots) {
    const group = groups.get(bot.name);
    if (group) group.push(bot);
    else groups.set(bot.name, [bot]);
  }
  return [...groups];
}

/**
 * The own bots in every status: one row group per name, each version linked to its page with its
 * rating and the number of its games (G9).
 */
export function OwnBotGroups({ bots }: { bots: Bot[] }) {
  const { t } = useTranslation();
  const locale = useLocale();
  return (
    <TableShell rows={bots.length} empty={t("ownBots.empty")}>
      <thead>
        <tr>
          <th>{t("bots.name")}</th>
          <th>{t("bots.version")}</th>
          <th>{t("bots.status")}</th>
          <th className="number">{t("bots.rating")}</th>
          <th className="number">{t("bots.ratedGames")}</th>
          <th className="optional">{t("bots.created")}</th>
        </tr>
      </thead>
      {groupByName(bots).map(([name, versions]) => (
        <tbody key={name}>
          {versions.map((bot, index) => (
            <tr key={bot.id}>
              {index === 0 && (
                <th scope="rowgroup" rowSpan={versions.length}>
                  {name}
                </th>
              )}
              <td>
                <Link to={`/bots/${bot.id}`} aria-label={`${name} ${bot.version}`}>
                  {bot.version}
                </Link>
              </td>
              <td>
                <BotStatusBadge status={bot.status} />
              </td>
              <td className="number">{ratingText(bot.rating)}</td>
              <td className="number">
                <Link to={`/matches?bot=${bot.id}`}>{bot.rating.games}</Link>
              </td>
              <td className="optional">{formatDateTime(bot.created_at, locale)}</td>
            </tr>
          ))}
        </tbody>
      ))}
    </TableShell>
  );
}
