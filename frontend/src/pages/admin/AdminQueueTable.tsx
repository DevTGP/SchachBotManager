import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { MAX_PRIORITY } from "../../api/admin";
import type { QueueEntry } from "../../api/types";
import { playersLabel } from "../../format/botLabel";
import { QueueEntryActions } from "./QueueEntryActions";

/**
 * The queue with the admin's interventions (E152): single games can be cancelled, waiting ones
 * get a new priority. Games of people only show; they have their own runner.
 */
export function AdminQueueTable({
  running,
  waiting,
  onChange,
}: {
  running: QueueEntry[];
  waiting: QueueEntry[];
  onChange: () => void;
}) {
  const { t } = useTranslation();
  // "To the front" outranks the first waiting game; equal priorities keep the order of arrival.
  const front = Math.min(MAX_PRIORITY, (waiting[0]?.priority ?? 0) + 1);
  const entries = [...running, ...waiting];
  if (entries.length === 0) return <p className="muted">{t("admin.queueEmpty")}</p>;
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th className="number">{t("queue.position")}</th>
            <th>{t("matchTable.players")}</th>
            <th className="number">{t("admin.priority")}</th>
            <th>{t("admin.actions")}</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.match.id}>
              <td className="number">{entry.position || t("admin.queueRunningShort")}</td>
              <td>
                <Link to={`/matches/${entry.match.id}`}>{playersLabel(entry.match)}</Link>
              </td>
              <td className="number">{entry.match.type === "single" ? entry.priority : ""}</td>
              <td>
                {entry.match.type === "single" && (
                  <QueueEntryActions
                    entry={entry}
                    front={entry.position === 1 ? undefined : front}
                    onChange={onChange}
                  />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
