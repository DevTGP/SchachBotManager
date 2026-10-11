import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

/** The header of a column of row actions, named for screen readers only. */
export function ActionsHeader() {
  const { t } = useTranslation();
  return (
    <th>
      <span className="sr-only">{t("common.actions")}</span>
    </th>
  );
}

/**
 * Opens a game; names in the row stay plain text instead of one long link (E165). Further
 * actions of the row follow the button.
 */
export function OpenCell({ matchId, children }: { matchId: string; children?: ReactNode }) {
  const { t } = useTranslation();
  return (
    <td className="row-actions">
      <Link className="button small" to={`/matches/${matchId}`}>
        {t("matchTable.open")}
      </Link>
      {children}
    </td>
  );
}
