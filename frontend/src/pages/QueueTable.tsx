import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { QueueEntry } from "../api/types";
import { formatTime } from "../format/dateTime";
import { formatTimeControl } from "../format/timeControl";
import { useLocale } from "../hooks/useLocale";

/** Running entries show when they started; waiting ones their place and estimated start. */
export function QueueTable({ entries, running }: { entries: QueueEntry[]; running: boolean }) {
  const { t } = useTranslation();
  const locale = useLocale();
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {!running && <th className="number">{t("queue.position")}</th>}
            <th>{t("matchTable.players")}</th>
            <th>{t("matchTable.timeControl")}</th>
            <th>{running ? t("queue.started") : t("queue.estimatedStart")}</th>
            <th>{t("queue.estimatedEnd")}</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(({ match, position, estimated_start, estimated_end }) => (
            <tr key={match.id}>
              {!running && <td className="number">{position}</td>}
              <td>
                <Link to={`/matches/${match.id}`}>
                  {match.white.name} – {match.black.name}
                </Link>
              </td>
              <td>{formatTimeControl(match.discipline)}</td>
              <td>{formatTime(estimated_start, locale)}</td>
              <td>{formatTime(estimated_end, locale)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
