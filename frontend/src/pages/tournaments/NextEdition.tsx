import { useTranslation } from "react-i18next";

import type { Tournament } from "../../api/types";
import { formatDateTime } from "../../format/dateTime";
import { useLocale } from "../../hooks/useLocale";

/**
 * When the next edition starts: by the calendar once enough bots are registered, or without one
 * when an admin starts it (E171).
 */
export function NextEdition({ tournament }: { tournament: Tournament }) {
  const { t } = useTranslation();
  const locale = useLocale();
  const edition = tournament.edition;
  if (tournament.archived) return <p className="hint">{t("tournaments.archivedHint")}</p>;
  if (edition === null || edition.status !== "planned") return null;
  const text =
    edition.starts_after === null
      ? t("tournaments.awaitingStart")
      : t("tournaments.startsAfter", {
          at: formatDateTime(edition.starts_after, locale),
          count: tournament.min_participants,
        });
  return <p className="hint">{text}</p>;
}
