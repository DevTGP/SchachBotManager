import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { fetchRatings } from "../api/endpoints";
import { ApiContent } from "../components/ApiContent";
import { botLabel } from "../format/botLabel";
import { useApi } from "../hooks/useApi";

/** Public bots with at least one counted match, highest rating first (E103). */
export function RatingsPage() {
  const { t } = useTranslation();
  const ratings = useApi(fetchRatings, "ratings");
  return (
    <>
      <h1>{t("ratings.title")}</h1>
      <p className="muted">{t("ratings.hint")}</p>
      <ApiContent state={ratings}>
        {(items) =>
          items.length === 0 ? (
            <p className="muted">{t("ratings.empty")}</p>
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>{t("ratings.rank")}</th>
                    <th>{t("ratings.bot")}</th>
                    <th>{t("bots.language")}</th>
                    <th>{t("bots.rating")}</th>
                    <th>{t("bots.ratedGames")}</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((bot, index) => (
                    <tr key={bot.id}>
                      <td>{index + 1}</td>
                      <td>
                        <Link to={`/bots/${bot.id}`}>{botLabel(bot)}</Link>
                      </td>
                      <td>{t(`language.${bot.language}`)}</td>
                      <td>{bot.rating.value}</td>
                      <td>{bot.rating.games}</td>
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
