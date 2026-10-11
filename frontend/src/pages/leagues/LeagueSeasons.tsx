import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { SeasonSummary } from "../../api/types";
import { formatDateTime } from "../../format/dateTime";
import { useLocale } from "../../hooks/useLocale";

/** The seasons of a league, newest first (E132). */
export function LeagueSeasons({ seasons }: { seasons: SeasonSummary[] }) {
  const { t } = useTranslation();
  const locale = useLocale();
  return (
    <section>
      <h2>{t("leagues.seasons")}</h2>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>{t("leagues.season")}</th>
              <th>{t("bots.status")}</th>
              <th className="number">{t("leagues.participants")}</th>
              <th>{t("seasons.startedAt")}</th>
              <th>{t("seasons.finishedAt")}</th>
            </tr>
          </thead>
          <tbody>
            {seasons.map((season) => (
              <tr key={season.id}>
                <td>
                  <Link to={`/seasons/${season.id}`}>
                    {t("leagues.seasonNumber", { number: season.number })}
                  </Link>
                </td>
                <td>{t(`seasonStatus.${season.status}`)}</td>
                <td className="number">{season.participants}</td>
                <td>{season.started_at ? formatDateTime(season.started_at, locale) : "–"}</td>
                <td>{season.finished_at ? formatDateTime(season.finished_at, locale) : "–"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
