import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";

import { fetchSeason } from "../../api/leagues";
import type { Season } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { formatDateTime } from "../../format/dateTime";
import { disciplineLabel } from "../../format/timeControl";
import { useApi } from "../../hooks/useApi";
import { POLL_LIST_MS } from "../../hooks/polling";
import { useLocale } from "../../hooks/useLocale";
import { LeagueFacts } from "./LeagueFacts";
import { TierTable } from "./TierTable";

/** A season with the settings of its start and the table of every tier (E135, E137). */
export function SeasonPage() {
  const { t } = useTranslation();
  const locale = useLocale();
  const { id = "" } = useParams();
  const season = useApi(
    (signal) => fetchSeason(id, signal),
    `season:${id}`,
    (data: Season | undefined) => (data?.status === "running" ? POLL_LIST_MS : undefined),
  );
  return (
    <ApiContent state={season}>
      {(data) => (
        <>
          <h1>{t("seasons.title", { league: data.league_name, number: data.number })}</h1>
          <p>
            <Link to={`/leagues/${data.league_id}`}>{t("seasons.toLeague")}</Link>
          </p>
          <p className="muted">
            {t(`seasonStatus.${data.status}`)}
            {data.started_at &&
              ` · ${t("seasons.started", { at: formatDateTime(data.started_at, locale) })}`}
            {data.finished_at &&
              ` · ${t("seasons.finished", { at: formatDateTime(data.finished_at, locale) })}`}
          </p>
          {data.settings && data.discipline ? (
            <LeagueFacts
              settings={data.settings}
              discipline={disciplineLabel(data.discipline, locale)}
            />
          ) : (
            <p className="muted">{t("seasons.notStarted")}</p>
          )}
          {data.tiers.map((tier) => (
            <TierTable
              key={tier.tier}
              tier={tier}
              seasonId={data.id}
              running={data.status === "running"}
            />
          ))}
        </>
      )}
    </ApiContent>
  );
}
