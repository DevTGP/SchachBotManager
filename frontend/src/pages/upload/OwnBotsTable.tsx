import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { Bot } from "../../api/types";
import { formatDateTime } from "../../format/dateTime";
import { useLocale } from "../../hooks/useLocale";

/** The own bots in every status, newest first, each linked to its report. */
export function OwnBotsTable({ bots }: { bots: Bot[] }) {
  const { t } = useTranslation();
  const locale = useLocale();
  if (bots.length === 0) return <p className="muted">{t("upload.ownEmpty")}</p>;
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
        <tbody>
          {bots.map((bot) => (
            <tr key={bot.id}>
              <td>
                <Link to={`/bots/${bot.id}`}>{bot.name}</Link>
              </td>
              <td>{bot.version}</td>
              <td>{t(`botStatus.${bot.status}`)}</td>
              <td>{formatDateTime(bot.created_at, locale)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
