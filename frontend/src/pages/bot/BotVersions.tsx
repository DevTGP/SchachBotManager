import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { Bot } from "../../api/types";
import { formatDateTime } from "../../format/dateTime";
import { useLocale } from "../../hooks/useLocale";

/** The versions of the name the viewer may see, newest first; the shown one is marked (E95). */
export function BotVersions({ versions, current }: { versions: Bot[]; current: string }) {
  const { t } = useTranslation();
  const locale = useLocale();
  if (versions.length < 2) return null;
  return (
    <>
      <h2>{t("bot.versions")}</h2>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>{t("bots.version")}</th>
              <th>{t("bots.status")}</th>
              <th>{t("bots.created")}</th>
            </tr>
          </thead>
          <tbody>
            {versions.map((bot) => (
              <tr key={bot.id}>
                <td>
                  {bot.id === current ? (
                    <strong aria-current="page">{bot.version}</strong>
                  ) : (
                    <Link to={`/bots/${bot.id}`}>{bot.version}</Link>
                  )}
                </td>
                <td>{t(`botStatus.${bot.status}`)}</td>
                <td>{formatDateTime(bot.created_at, locale)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
