import { useTranslation } from "react-i18next";

import type { Match } from "../api/types";
import { formatDateTime } from "../format/dateTime";
import { formatRatingChange } from "../format/rating";
import { formatResult } from "../format/result";
import { formatTimeControl } from "../format/timeControl";
import { useLocale } from "../hooks/useLocale";

export function MatchDetails({ match }: { match: Match }) {
  const { t } = useTranslation();
  const locale = useLocale();
  const rows: [string, string][] = [
    [t("viewer.status"), t(`status.${match.status}`)],
    [t("viewer.result"), formatResult(match.result) || t("common.none")],
    [
      t("viewer.termination"),
      match.termination ? t(`termination.${match.termination}`) : t("common.none"),
    ],
    [t("viewer.discipline"), `${match.discipline.name} (${formatTimeControl(match.discipline)})`],
    [t("viewer.rated"), match.rated ? t("viewer.ratedYes") : t("viewer.ratedNo")],
  ];
  // Present once the runner has counted the match (E103).
  if (match.white.rating) {
    rows.push([t("viewer.ratingWhite"), formatRatingChange(match.white.rating)]);
  }
  if (match.black.rating) {
    rows.push([t("viewer.ratingBlack"), formatRatingChange(match.black.rating)]);
  }
  if (match.started_at) rows.push([t("viewer.started"), formatDateTime(match.started_at, locale)]);
  if (match.finished_at) {
    rows.push([t("viewer.finished"), formatDateTime(match.finished_at, locale)]);
  }
  return (
    <dl className="details">
      {rows.map(([term, value]) => (
        <div key={term}>
          <dt>{term}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
