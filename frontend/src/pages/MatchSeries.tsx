import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { SeriesPlace } from "../api/types";

/** Where a game stands in its series, with a link to the score (E155). */
export function MatchSeries({ place }: { place: SeriesPlace | null }) {
  const { t } = useTranslation();
  if (place === null) return null;
  return (
    <p>
      {t("series.place", { index: place.index, games: place.games })}{" "}
      <Link to={`/series/${place.id}`}>{t("series.view")}</Link>
    </p>
  );
}
