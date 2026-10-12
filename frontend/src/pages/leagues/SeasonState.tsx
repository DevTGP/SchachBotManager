import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { SeasonSummary } from "../../api/types";

/** "Season 3: running" for the latest season of a league, linked to it (E188); nothing without one. */
export function SeasonState({ season }: { season: SeasonSummary | null }) {
  const { t } = useTranslation();
  if (season === null) return null;
  return (
    <Link to={`/seasons/${season.id}`}>
      {t("leagues.seasonState", {
        number: season.number,
        status: t(`seasonStatus.${season.status}`),
      })}
    </Link>
  );
}
