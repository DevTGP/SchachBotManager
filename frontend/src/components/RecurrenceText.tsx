import { useTranslation } from "react-i18next";

import type { Recurrence } from "../api/types";
import { formatDateTime } from "../format/dateTime";
import { splitInterval } from "../format/recurrence";
import { useLocale } from "../hooks/useLocale";

/** The calendar of a league or tournament in words, in local time (E171). */
export function RecurrenceText({ recurrence }: { recurrence: Recurrence | null }) {
  const { t } = useTranslation();
  const locale = useLocale();
  if (recurrence === null) return t("recurrence.manual");
  const { amount, unit } = splitInterval(recurrence.interval_hours);
  return t(`recurrence.interval.${unit}`, {
    count: amount,
    at: formatDateTime(recurrence.first_start, locale),
  });
}
