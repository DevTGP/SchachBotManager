import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";

import { fetchSeries } from "../../api/endpoints";
import type { Series, SeriesBot } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { MatchTable } from "../../components/MatchTable";
import { sideLabel } from "../../format/botLabel";
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

function BotName({ bot }: { bot: SeriesBot }) {
  return <Link to={`/bots/${bot.bot_id}`}>{sideLabel(bot)}</Link>;
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
      {(data) => (
        <>
          <h1>{t("series.title")}</h1>
          <p className="series-score">
            <BotName bot={data.a} />{" "}
            <strong>
              {formatPoints(data.a.points)} – {formatPoints(data.b.points)}
            </strong>{" "}
            <BotName bot={data.b} />
          </p>
          <p className="muted">
            {t("series.counted", { counted: data.counted, games: data.games })}
          </p>
          <MatchTable matches={data.matches} empty={t("matches.empty")} />
        </>
      )}
    </ApiContent>
  );
}
