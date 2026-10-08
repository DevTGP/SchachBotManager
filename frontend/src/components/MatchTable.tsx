import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { MatchSummary } from "../api/types";
import { playersLabel } from "../format/botLabel";
import { formatDateTime } from "../format/dateTime";
import { formatResult } from "../format/result";
import { formatTimeControl } from "../format/timeControl";
import { useLocale } from "../hooks/useLocale";

export function MatchTable({ matches, empty }: { matches: MatchSummary[]; empty: string }) {
  const { t } = useTranslation();
  const locale = useLocale();
  if (matches.length === 0) return <p className="muted">{empty}</p>;
  return (
    <div className="table-scroll">
      <table className="match-table">
        <thead>
          <tr>
            <th>{t("matchTable.players")}</th>
            <th>{t("matchTable.result")}</th>
            <th className="optional">{t("matchTable.termination")}</th>
            <th>{t("matchTable.timeControl")}</th>
            <th className="number optional">{t("matchTable.moves")}</th>
            <th>{t("matchTable.date")}</th>
          </tr>
        </thead>
        <tbody>
          {matches.map((match) => (
            <tr key={match.id}>
              <td>
                <Link to={`/matches/${match.id}`}>{playersLabel(match)}</Link>
              </td>
              <td>{match.result ? formatResult(match.result) : t(`status.${match.status}`)}</td>
              <td className="optional">
                {match.termination ? t(`termination.${match.termination}`) : ""}
              </td>
              <td>{formatTimeControl(match.discipline)}</td>
              <td className="number optional">{Math.ceil(match.ply_count / 2)}</td>
              <td>{formatDateTime(match.started_at ?? match.created_at, locale)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
