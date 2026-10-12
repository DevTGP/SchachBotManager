import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router";

import { fetchBots, fetchDisciplines, fetchMatches } from "../api/endpoints";
import type { MatchKind, MatchStatus } from "../api/types";
import { ApiContent } from "../components/ApiContent";
import { BotPicker } from "../components/BotPicker";
import { MatchTable } from "../components/MatchTable";
import { Pager } from "../components/Pager";
import { type Pill, PillSelect } from "../components/PillSelect";
import { tierAnchor } from "../format/anchors";
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
 * may list the games they set (E156). A season page links here with season and tier (E137),
 * an edition page with the edition (E180); both filters link back to their page (E188).
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
  const seasonId = params.get("season") ?? undefined;
  const tierText = seasonId ? params.get("tier") : null;
  const tier = tierText ? Number.parseInt(tierText, 10) || undefined : undefined;
  const editionId = params.get("edition") ?? undefined;
  const offset = Math.max(0, Number.parseInt(params.get("offset") ?? "0", 10) || 0);

  const query = { status, kind, botId, opponentId, disciplineId, mine, seasonId, tier, editionId };
  const matches = useApi(
    (signal) => fetchMatches({ ...query, limit: PAGE_SIZE, offset }, signal),
    `${JSON.stringify(query)}/${offset}`,
    POLL_LIST_MS,
  );
  const bots = useApi(fetchBots, "bots");
  const disciplines = useApi(fetchDisciplines, "disciplines");

  const chosen = bots.data?.find((bot) => bot.id === botId);
  const opponents = bots.data?.filter((bot) => bot.name !== chosen?.name) ?? [];
  const statusPills: Pill<MatchStatus | "">[] = [
    { value: "", label: t("matches.allStatuses") },
    ...STATUSES.map((value) => ({ value, label: t(`status.${value}`) })),
  ];
  const kindPills: Pill<MatchKind | "">[] = [
    { value: "", label: t("matches.allKinds") },
    ...KINDS.map((entry) => ({ value: entry.value, label: t(entry.label) })),
  ];

  function update(name: string, value: string | undefined) {
    const next = new URLSearchParams(params);
    if (value) next.set(name, value);
    else next.delete(name);
    if (name !== "offset") next.delete("offset");
    if (name === "bot") next.delete("opponent");
    if (name === "season") next.delete("tier");
    setParams(next);
  }

  return (
    <>
      <h1>{t("matches.title")}</h1>
      <div className="filters">
        <PillSelect
          label={t("matches.status")}
          options={statusPills}
          value={status ?? ""}
          onChange={(value) => update("status", value || undefined)}
        />
        <PillSelect
          label={t("matches.kind")}
          options={kindPills}
          value={kind ?? ""}
          onChange={(value) => update("kind", value || undefined)}
        />
        <BotPicker
          label={t("matches.bot")}
          bots={bots.data ?? []}
          value={botId ?? ""}
          empty={t("matches.allBots")}
          onChange={(value) => update("bot", value || undefined)}
        />
        {botId && (
          <BotPicker
            label={t("matches.opponent")}
            bots={opponents}
            value={opponentId ?? ""}
            empty={t("matches.allOpponents")}
            onChange={(value) => update("opponent", value || undefined)}
          />
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
          <label className="checkbox">
            <input
              type="checkbox"
              checked={mine}
              onChange={(event) => update("mine", event.target.checked ? "true" : undefined)}
            />
            {t("matches.mine")}
          </label>
        )}
      </div>
      {seasonId && (
        <p className="hint">
          {tier ? t("matches.seasonTierFilter", { tier }) : t("matches.seasonFilter")}{" "}
          <Link to={`/seasons/${seasonId}${tier ? `#${tierAnchor(tier)}` : ""}`}>
            {t("matches.toSeason")}
          </Link>{" "}
          <button type="button" onClick={() => update("season", undefined)}>
            {t("matches.clearSeason")}
          </button>
        </p>
      )}
      {editionId && (
        <p className="hint">
          {t("matches.editionFilter")}{" "}
          <Link to={`/editions/${editionId}`}>{t("matches.toEdition")}</Link>{" "}
          <button type="button" onClick={() => update("edition", undefined)}>
            {t("matches.clearEdition")}
          </button>
        </p>
      )}
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
