import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router";

import { fetchBots, fetchDisciplines, fetchMatches } from "../api/endpoints";
import type { MatchKind, MatchStatus } from "../api/types";
import { ApiContent } from "../components/ApiContent";
import { MatchTable } from "../components/MatchTable";
import { Pager } from "../components/Pager";
import { botLabel } from "../format/botLabel";
import { useApi } from "../hooks/useApi";
import { POLL_LIST_MS } from "../hooks/polling";
import { useSession } from "../session/sessionContext";

const PAGE_SIZE = 25;
const STATUSES: MatchStatus[] = ["queued", "running", "finished", "aborted"];
const KINDS: { value: MatchKind; label: string }[] = [
  { value: "bots", label: "matches.kindBots" },
  { value: "players", label: "matches.kindPlayers" },
];

/**
 * Filters and page live in the URL (status, kind, bot, opponent, discipline, mine, offset), so
 * every view can be linked. Games with people and remote bots are listed like those of bots and
 * can be filtered (E119). The opponent narrows the games of the chosen bot; coders and admins
 * may list the games they set (E156).
 */
export function MatchesPage() {
  const { t } = useTranslation();
  const [params, setParams] = useSearchParams();
  const status = STATUSES.find((value) => value === params.get("status"));
  const kind = KINDS.find((entry) => entry.value === params.get("kind"))?.value;
  const botId = params.get("bot") ?? undefined;
  const opponentId = botId ? (params.get("opponent") ?? undefined) : undefined;
  const disciplineId = params.get("discipline") ?? undefined;
  const { user } = useSession();
  const maySetGames = user?.role === "coder" || user?.role === "admin";
  const mine = maySetGames && params.get("mine") === "true";
  const offset = Math.max(0, Number.parseInt(params.get("offset") ?? "0", 10) || 0);

  const query = { status, kind, botId, opponentId, disciplineId, mine };
  const matches = useApi(
    (signal) => fetchMatches({ ...query, limit: PAGE_SIZE, offset }, signal),
    `${JSON.stringify(query)}/${offset}`,
    POLL_LIST_MS,
  );
  const bots = useApi(fetchBots, "bots");
  const disciplines = useApi(fetchDisciplines, "disciplines");

  function update(name: string, value: string | undefined) {
    const next = new URLSearchParams(params);
    if (value) next.set(name, value);
    else next.delete(name);
    if (name !== "offset") next.delete("offset");
    if (name === "bot") next.delete("opponent");
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
          {t("matches.kind")}
          <select
            value={kind ?? ""}
            onChange={(event) => update("kind", event.target.value || undefined)}
          >
            <option value="">{t("matches.allKinds")}</option>
            {KINDS.map((entry) => (
              <option key={entry.value} value={entry.value}>
                {t(entry.label)}
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
        {botId && (
          <label>
            {t("matches.opponent")}
            <select
              value={opponentId ?? ""}
              onChange={(event) => update("opponent", event.target.value || undefined)}
            >
              <option value="">{t("matches.allOpponents")}</option>
              {bots.data
                ?.filter((bot) => bot.id !== botId)
                .map((bot) => (
                  <option key={bot.id} value={bot.id}>
                    {botLabel(bot)}
                  </option>
                ))}
            </select>
          </label>
        )}
        <label>
          {t("matches.discipline")}
          <select
            value={disciplineId ?? ""}
            onChange={(event) => update("discipline", event.target.value || undefined)}
          >
            <option value="">{t("matches.allDisciplines")}</option>
            {disciplines.data?.map((discipline) => (
              <option key={discipline.id} value={discipline.id}>
                {discipline.name}
              </option>
            ))}
          </select>
        </label>
        {maySetGames && (
          <label>
            <input
              type="checkbox"
              checked={mine}
              onChange={(event) => update("mine", event.target.checked ? "true" : undefined)}
            />
            {t("matches.mine")}
          </label>
        )}
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
