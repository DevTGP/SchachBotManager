import { useTranslation } from "react-i18next";

import type { League } from "../../api/types";
import { formatDateTime } from "../../format/dateTime";
import { useLocale } from "../../hooks/useLocale";

/**
 * When the next season starts: an admin releases the first one, every later one starts by
 * itself after the pause once enough bots are registered (E132).
 */
export function NextSeason({ league }: { league: League }) {
  const { t } = useTranslation();
  const locale = useLocale();
  const season = league.season;
  if (league.archived) return <p className="hint">{t("leagues.archivedHint")}</p>;
  if (season === null || season.status !== "planned") return null;
  const text =
    season.starts_after === null
      ? t("leagues.awaitingRelease")
      : t("leagues.startsAfter", {
          at: formatDateTime(season.starts_after, locale),
          count: league.min_participants,
        });
  return <p className="hint">{text}</p>;
}
