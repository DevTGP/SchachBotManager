import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { EditionSummary } from "../../api/types";
import { SideName } from "../../components/SideName";
import { formatDateTime } from "../../format/dateTime";
import { useLocale } from "../../hooks/useLocale";

/** The editions of a tournament, newest first, with the winner of each finished one (E173). */
export function TournamentEditions({ editions }: { editions: EditionSummary[] }) {
  const { t } = useTranslation();
  const locale = useLocale();
  return (
    <section>
      <h2>{t("tournaments.editions")}</h2>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>{t("tournaments.edition")}</th>
              <th>{t("bots.status")}</th>
              <th className="number">{t("tournaments.participants")}</th>
              <th>{t("editions.winner")}</th>
              <th>{t("seasons.startedAt")}</th>
              <th>{t("seasons.finishedAt")}</th>
            </tr>
          </thead>
          <tbody>
            {editions.map((edition) => (
              <tr key={edition.id}>
                <td>
                  <Link to={`/editions/${edition.id}`}>
                    {t("tournaments.editionNumber", { number: edition.number })}
                  </Link>
                </td>
                <td>{t(`editionStatus.${edition.status}`)}</td>
                <td className="number">{edition.participants}</td>
                <td>{edition.winner ? <SideName side={edition.winner} /> : "–"}</td>
                <td>{edition.started_at ? formatDateTime(edition.started_at, locale) : "–"}</td>
                <td>{edition.finished_at ? formatDateTime(edition.finished_at, locale) : "–"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
