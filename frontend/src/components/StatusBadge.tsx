import { useTranslation } from "react-i18next";

import type { MatchStatus } from "../api/types";

/** The state of a game as a badge, e.g. in place of a result that is not there yet. */
export function StatusBadge({ status }: { status: MatchStatus }) {
  const { t } = useTranslation();
  return <span className={`badge status-${status}`}>{t(`status.${status}`)}</span>;
}
