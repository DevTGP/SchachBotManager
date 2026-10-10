import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { EnqueuedMatches } from "../api/types";

/** The confirmation after queueing, with the series of two or more games (E155). */
export function QueuedNotice({ queued }: { queued: EnqueuedMatches }) {
  const { t } = useTranslation();
  return (
    <p role="status">
      <span>{t("admin.queued", { count: queued.match_ids.length })}</span>{" "}
      <Link to="/queue">{t("nav.queue")}</Link>
      {queued.series_id && (
        <>
          {" · "}
          <Link to={`/series/${queued.series_id}`}>{t("series.view")}</Link>
        </>
      )}
    </p>
  );
}
