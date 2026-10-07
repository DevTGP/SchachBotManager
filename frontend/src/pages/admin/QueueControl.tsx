import { useTranslation } from "react-i18next";

import { setQueuePaused } from "../../api/admin";
import { fetchQueue } from "../../api/endpoints";
import { ApiContent } from "../../components/ApiContent";
import { FormError } from "../../components/FormError";
import { useApi } from "../../hooks/useApi";
import { useSubmit } from "../../hooks/useSubmit";

/** Pauses or resumes the queue; running games finish either way (E13). */
export function QueueControl() {
  const { t } = useTranslation();
  const queue = useApi(fetchQueue, "admin-queue");
  const { pending, error, submit } = useSubmit();

  function toggle(paused: boolean) {
    void submit(async () => {
      await setQueuePaused(paused);
      queue.reload();
    });
  }

  return (
    <section>
      <h2>{t("admin.queue")}</h2>
      <ApiContent state={queue}>
        {(data) => (
          <p className="inline-actions">
            <span>{data.paused ? t("admin.queuePaused") : t("admin.queueRunning")}</span>
            <button type="button" disabled={pending} onClick={() => toggle(!data.paused)}>
              {data.paused ? t("admin.resume") : t("admin.pause")}
            </button>
          </p>
        )}
      </ApiContent>
      <FormError error={error} />
    </section>
  );
}
