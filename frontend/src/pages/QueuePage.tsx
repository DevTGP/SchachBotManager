import { useTranslation } from "react-i18next";

import { fetchQueue } from "../api/endpoints";
import { ApiContent } from "../components/ApiContent";
import { useApi } from "../hooks/useApi";
import { POLL_LIST_MS } from "../hooks/polling";
import { QueueTable } from "./QueueTable";

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
              {data.running.length === 0 ? (
                <p className="muted">{t("queue.noRunning")}</p>
              ) : (
                <QueueTable entries={data.running} running />
              )}
            </section>
            <section>
              <h2>{t("queue.waiting")}</h2>
              {data.waiting.length === 0 ? (
                <p className="muted">{t("queue.noWaiting")}</p>
              ) : (
                <QueueTable entries={data.waiting} running={false} />
              )}
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
