import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router";

import { fetchBots, fetchMatches } from "../api/endpoints";
import type { MatchStatus } from "../api/types";
import { ApiContent } from "../components/ApiContent";
import { MatchTable } from "../components/MatchTable";
import { Pager } from "../components/Pager";
import { botLabel } from "../format/botLabel";
import { useApi } from "../hooks/useApi";
import { POLL_LIST_MS } from "../hooks/polling";

const PAGE_SIZE = 25;
const STATUSES: MatchStatus[] = ["queued", "running", "finished", "aborted"];

/** Filters and page live in the URL (status, bot, offset), so every view can be linked. */
export function MatchesPage() {
  const { t } = useTranslation();
  const [params, setParams] = useSearchParams();
  const status = STATUSES.find((value) => value === params.get("status"));
  const botId = params.get("bot") ?? undefined;
  const offset = Math.max(0, Number.parseInt(params.get("offset") ?? "0", 10) || 0);

  const matches = useApi(
    (signal) => fetchMatches({ status, botId, limit: PAGE_SIZE, offset }, signal),
    `${status}/${botId}/${offset}`,
    POLL_LIST_MS,
  );
  const bots = useApi(fetchBots, "bots");

  function update(name: string, value: string | undefined) {
    const next = new URLSearchParams(params);
    if (value) next.set(name, value);
    else next.delete(name);
    if (name !== "offset") next.delete("offset");
    setParams(next);
  }

  return (
    <>
      <h1>{t("matches.title")}</h1>
      <div className="filters">
        <label>
          {t("matches.status")}
          <select
            value={status ?? ""}
            onChange={(event) => update("status", event.target.value || undefined)}
          >
            <option value="">{t("matches.allStatuses")}</option>
            {STATUSES.map((value) => (
              <option key={value} value={value}>
                {t(`status.${value}`)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("matches.bot")}
          <select
            value={botId ?? ""}
            onChange={(event) => update("bot", event.target.value || undefined)}
          >
            <option value="">{t("matches.allBots")}</option>
            {bots.data?.map((bot) => (
              <option key={bot.id} value={bot.id}>
                {botLabel(bot)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <ApiContent state={matches}>
        {(page) => (
          <>
            <MatchTable matches={page.items} empty={t("matches.empty")} />
            <Pager
              offset={offset}
              limit={PAGE_SIZE}
              total={page.total}
              onChange={(value) => update("offset", value > 0 ? String(value) : undefined)}
            />
          </>
        )}
      </ApiContent>
    </>
  );
}
