import { useTranslation } from "react-i18next";
import { useParams } from "react-router";

import { fetchSeries } from "../../api/endpoints";
import type { Series } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { MatchTable } from "../../components/MatchTable";
import { SideName } from "../../components/SideName";
import { compareSides } from "../../format/pairing";
import { formatPoints } from "../../format/points";
import { useApi } from "../../hooks/useApi";
import { POLL_LIST_MS } from "../../hooks/polling";

/** Games can still come while one waits or runs. */
function isOpen(series: Series | undefined): boolean {
  return (
    series?.matches.some((match) => match.status === "queued" || match.status === "running") ??
    false
  );
}

/** The score and the games of one request with two or more games (E155). */
export function SeriesPage() {
  const { t } = useTranslation();
  const { id = "" } = useParams();
  const series = useApi(
    (signal) => fetchSeries(id, signal),
    id,
    (data) => (isOpen(data) ? POLL_LIST_MS : undefined),
  );
  return (
    <ApiContent state={series}>
      {(data) => {
        const [first, second] =
          compareSides(data.b, data.a) < 0 ? [data.b, data.a] : [data.a, data.b];
        return (
          <>
            <h1>{t("series.title")}</h1>
            <p className="series-score">
              <SideName side={first} />{" "}
              <strong>
                {formatPoints(first.points)} – {formatPoints(second.points)}
              </strong>{" "}
              <SideName side={second} />
            </p>
            <p className="muted">
              {t("series.counted", { counted: data.counted, games: data.games })}
            </p>
            <MatchTable matches={data.matches} empty={t("matches.empty")} />
          </>
        );
      }}
    </ApiContent>
  );
}
