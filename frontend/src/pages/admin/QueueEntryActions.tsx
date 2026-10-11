import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { cancelMatch, MAX_PRIORITY, setMatchPriority } from "../../api/admin";
import type { QueueEntry } from "../../api/types";
import { FormError } from "../../components/FormError";
import { useSubmit } from "../../hooks/useSubmit";

/**
 * A waiting game gets a new priority or moves to the front; any single game can be cancelled
 * after a second click (E152). front is the priority that puts it first, if it is not first.
 */
export function QueueEntryActions({
  entry,
  front,
  onChange,
}: {
  entry: QueueEntry;
  front: number | undefined;
  onChange: () => void;
}) {
  const { t } = useTranslation();
  const [priority, setPriority] = useState(String(entry.priority));
  const [asking, setAsking] = useState(false);
  const { pending, error, submit } = useSubmit();
  const waiting = entry.match.status === "queued";

  function run(action: () => Promise<unknown>) {
    void submit(async () => {
      await action();
      setAsking(false);
      onChange();
    });
  }

  function applyPriority(event: FormEvent) {
    event.preventDefault();
    run(() => setMatchPriority(entry.match.id, Number(priority)));
  }

  return (
    <>
      <span className="inline-actions">
        {waiting && (
          <form className="inline-actions priority-form" onSubmit={applyPriority}>
            <input
              type="number"
              className="priority-input"
              required
              min={0}
              max={MAX_PRIORITY}
              step={1}
              aria-label={t("admin.priority")}
              value={priority}
              onChange={(event) => setPriority(event.target.value)}
            />
            <button type="submit" className="small" disabled={pending}>
              {t("admin.setPriority")}
            </button>
          </form>
        )}
        {waiting && front !== undefined && (
          <button
            type="button"
            className="small"
            disabled={pending}
            onClick={() => run(() => setMatchPriority(entry.match.id, front))}
          >
            {t("admin.toFront")}
          </button>
        )}
        {asking ? (
          <>
            <button
              type="button"
              className="small danger confirm"
              disabled={pending}
              onClick={() => run(() => cancelMatch(entry.match.id))}
            >
              {t("admin.cancelConfirm")}
            </button>
            <button
              type="button"
              className="small"
              disabled={pending}
              onClick={() => setAsking(false)}
            >
              {t("admin.cancelKeep")}
            </button>
          </>
        ) : (
          <button
            type="button"
            className="small danger"
            disabled={pending}
            onClick={() => setAsking(true)}
          >
            {t("admin.cancelMatch")}
          </button>
        )}
      </span>
      <FormError error={error} />
    </>
  );
}
