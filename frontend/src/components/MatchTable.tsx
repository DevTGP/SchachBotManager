import type { TFunction } from "i18next";
import { useTranslation } from "react-i18next";

import type { MatchSummary } from "../api/types";
import { formatDateTime } from "../format/dateTime";
import { pairing, pairingResult } from "../format/pairing";
import { formatTimeControl } from "../format/timeControl";
import { useLocale } from "../hooks/useLocale";
import { CompetitionCell, CompetitionHeader } from "./CompetitionCell";
import { ActionsHeader, OpenCell } from "./OpenCell";
import { PairingCells, PairingHeader } from "./Pairing";
import { StatusBadge } from "./StatusBadge";
import { TableShell } from "./TableShell";

/**
 * Games with the sides in alphabetical order and the result in that order (E165). A game
 * without a result shows its state; the date tells when it started or was set. The competition
 * column leads to the season, edition or series of a game (E188).
 */
export function MatchTable({ matches, empty }: { matches: MatchSummary[]; empty: string }) {
  const { t } = useTranslation();
  const locale = useLocale();
  return (
    <TableShell rows={matches.length} empty={empty} className="match-table">
      <thead>
        <tr>
          <PairingHeader />
          <th>{t("matchTable.result")}</th>
          <th className="optional">{t("matchTable.termination")}</th>
          <th>{t("matchTable.timeControl")}</th>
          <th className="number optional">{t("matchTable.moves")}</th>
          <CompetitionHeader />
          <th className="optional">{t("matchTable.date")}</th>
          <ActionsHeader />
        </tr>
      </thead>
      <tbody>
        {matches.map((match) => (
          <tr key={match.id}>
            <PairingCells match={match} />
            <td>
              {match.result ? (
                pairingResult(match.result, pairing(match).flipped)
              ) : (
                <StatusBadge status={match.status} />
              )}
            </td>
            <td className="optional">
              {match.termination ? t(`termination.${match.termination}`) : ""}
            </td>
            <td>{formatTimeControl(match.discipline, locale)}</td>
            <td className="number optional">
              {match.status === "queued" ? t("common.none") : Math.ceil(match.ply_count / 2)}
            </td>
            <CompetitionCell match={match} />
            <td className="optional" title={dateTitle(match, locale, t)}>
              {formatDateTime(match.started_at ?? match.created_at, locale)}
            </td>
            <OpenCell matchId={match.id} />
          </tr>
        ))}
      </tbody>
    </TableShell>
  );
}

function dateTitle(match: MatchSummary, locale: string, t: TFunction): string {
  const created = t("matchTable.created", { at: formatDateTime(match.created_at, locale) });
  if (!match.started_at) return created;
  return `${t("matchTable.started", { at: formatDateTime(match.started_at, locale) })}\n${created}`;
}
