import { useTranslation } from "react-i18next";

import { MAX_PRIORITY } from "../../api/admin";
import type { QueueEntry } from "../../api/types";
import { QueueTable } from "../../components/QueueTable";
import { QueueEntryActions } from "./QueueEntryActions";

/**
 * The queue in the admin view (E152, E167): single games can be cancelled, waiting ones get a
 * new priority in their own field. Games of people only show; they have their own runner.
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
  const byId = new Map([...running, ...waiting].map((entry) => [entry.match.id, entry]));
  return (
    <QueueTable
      rows={[...running, ...waiting]}
      view="admin"
      empty={t("admin.queueEmpty")}
      actions={(row) => {
        const entry = byId.get(row.match.id);
        if (!entry || entry.match.type !== "single") return null;
        return (
          <QueueEntryActions
            entry={entry}
            front={entry.position === 1 ? undefined : front}
            onChange={onChange}
          />
        );
      }}
    />
  );
}
