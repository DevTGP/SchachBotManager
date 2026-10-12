import { useTranslation } from "react-i18next";

import { formatCountdown } from "../../format/countdown";
import { formatDateTime } from "../../format/dateTime";
import { useNow } from "../../hooks/useNow";

/** The deadline of a released game and the time left until it (E187). */
export function DeadlineCountdown({ at }: { at: string }) {
  const { t, i18n } = useTranslation();
  const now = useNow();
  return (
    <p>
      {t("competitionGame.deadlineLeft", {
        at: formatDateTime(at, i18n.language),
        left: formatCountdown(Date.parse(at) - now),
      })}
    </p>
  );
}
