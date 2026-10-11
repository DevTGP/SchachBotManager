import { useTranslation } from "react-i18next";

import { fetchQueue } from "../api/endpoints";
import { ApiContent } from "../components/ApiContent";
import { QueueTable } from "../components/QueueTable";
import { useApi } from "../hooks/useApi";
import { POLL_LIST_MS } from "../hooks/polling";

export function QueuePage() {
  const { t } = useTranslation();
  const queue = useApi(fetchQueue, "queue", POLL_LIST_MS);
  return (
    <>
      <h1>{t("queue.title")}</h1>
      <ApiContent state={queue}>
        {(data) => (
          <>
            {data.paused && (
              <p className="notice" role="status">
                {t("queue.paused")}
              </p>
            )}
            <section>
              <h2>{t("queue.running")}</h2>
              <QueueTable rows={data.running} view="public" empty={t("queue.noRunning")} />
            </section>
            <section>
              <h2>{t("queue.waiting")}</h2>
              <QueueTable rows={data.waiting} view="public" empty={t("queue.noWaiting")} />
              {data.waiting_total > data.waiting.length && (
                <p>{t("queue.more", { count: data.waiting_total - data.waiting.length })}</p>
              )}
              {data.running.length + data.waiting.length > 0 && (
                <p className="muted">{t("queue.estimateNote")}</p>
              )}
            </section>
          </>
        )}
      </ApiContent>
    </>
  );
}
