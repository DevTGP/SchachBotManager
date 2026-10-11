import { useTranslation } from "react-i18next";

import { fetchOwnRating } from "../../api/account";
import type { AccountRating } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { TableShell } from "../../components/TableShell";
import { useApi } from "../../hooks/useApi";

/**
 * The rating of the logged-in account (E117), overall and per discipline (G8, E169); the public
 * ranking shows it too (E118).
 */
export function OwnRating() {
  const { t } = useTranslation();
  const rating = useApi((signal) => fetchOwnRating(signal), "own-rating");

  return (
    <section>
      <h2>{t("account.rating")}</h2>
      <ApiContent state={rating}>{(data) => <RatingDetails rating={data} />}</ApiContent>
      <p className="hint">{t("account.ratingHint")}</p>
    </section>
  );
}

function RatingDetails({ rating }: { rating: AccountRating }) {
  const { t } = useTranslation();
  return (
    <>
      <p>{t("account.ratingValue", { value: rating.value, count: rating.games })}</p>
      {rating.disciplines.length > 0 && (
        <TableShell rows={rating.disciplines.length} empty={null}>
          <caption className="sr-only">{t("account.ratingByDiscipline")}</caption>
          <thead>
            <tr>
              <th>{t("matches.discipline")}</th>
              <th className="number">{t("bots.rating")}</th>
              <th className="number">{t("bots.ratedGames")}</th>
            </tr>
          </thead>
          <tbody>
            {rating.disciplines.map((entry) => (
              <tr key={entry.discipline_id}>
                <td>{entry.name}</td>
                <td className="number">{entry.value}</td>
                <td className="number">{entry.games}</td>
              </tr>
            ))}
          </tbody>
        </TableShell>
      )}
    </>
  );
}
