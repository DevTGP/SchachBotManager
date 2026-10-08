import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { Bot } from "../../api/types";
import { formatDateTime } from "../../format/dateTime";
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

/** The own bots in every status: one row group per name, each version linked to its page. */
export function OwnBotGroups({ bots }: { bots: Bot[] }) {
  const { t } = useTranslation();
  const locale = useLocale();
  if (bots.length === 0) return <p className="muted">{t("ownBots.empty")}</p>;
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>{t("bots.name")}</th>
            <th>{t("bots.version")}</th>
            <th>{t("bots.status")}</th>
            <th>{t("bots.created")}</th>
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
                <td>{t(`botStatus.${bot.status}`)}</td>
                <td>{formatDateTime(bot.created_at, locale)}</td>
              </tr>
            ))}
          </tbody>
        ))}
      </table>
    </div>
  );
}
