import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { fetchBots } from "../api/endpoints";
import { ApiContent } from "../components/ApiContent";
import { formatDateTime } from "../format/dateTime";
import { useApi } from "../hooks/useApi";
import { useLocale } from "../hooks/useLocale";

export function BotsPage() {
  const { t } = useTranslation();
  const locale = useLocale();
  const bots = useApi(fetchBots, "bots");
  return (
    <>
      <h1>{t("bots.title")}</h1>
      <ApiContent state={bots}>
        {(items) =>
          items.length === 0 ? (
            <p className="muted">{t("bots.empty")}</p>
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>{t("bots.name")}</th>
                    <th>{t("bots.version")}</th>
                    <th>{t("bots.language")}</th>
                    <th>{t("bots.kind")}</th>
                    <th>{t("bots.rating")}</th>
                    <th>{t("bots.created")}</th>
                    <th>{t("bots.matches")}</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((bot) => (
                    <tr key={bot.id}>
                      <td>
                        <Link to={`/bots/${bot.id}`}>{bot.name}</Link>
                      </td>
                      <td>{bot.version}</td>
                      <td>{t(`language.${bot.language}`)}</td>
                      <td>{bot.builtin ? t("bots.builtin") : t("bots.uploaded")}</td>
                      <td>{bot.rating.value}</td>
                      <td>{formatDateTime(bot.created_at, locale)}</td>
                      <td>
                        <Link to={`/matches?bot=${bot.id}`}>{t("bots.matches")}</Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        }
      </ApiContent>
    </>
  );
}
