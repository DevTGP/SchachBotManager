import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router";

import { fetchDisciplines } from "../api/endpoints";
import { ApiContent } from "../components/ApiContent";
import { type Pill, PillSelect } from "../components/PillSelect";
import { SideName } from "../components/SideName";
import { TableShell } from "../components/TableShell";
import { useApi } from "../hooks/useApi";
import { RANKING_FILTERS, loadRanking, type RankingFilter, type RankingRow } from "./ranking";

/**
 * Bots and players with at least one counted game, highest rating first (E103, E118), in one
 * discipline or overall (E163). Filter and discipline live in the URL (show, discipline), so
 * every view can be linked; both are pills (E168). Players have no link: there is no page of a
 * player. Version and creator have columns of their own (E164, E165).
 */
export function RatingsPage() {
  const { t } = useTranslation();
  const [params, setParams] = useSearchParams();
  const filter = RANKING_FILTERS.find((value) => value === params.get("show"));
  const discipline = params.get("discipline") ?? "";
  const disciplines = useApi(fetchDisciplines, "disciplines");
  const ranking = useApi(
    (signal) => loadRanking(filter, discipline || undefined, signal),
    `ratings/${filter}/${discipline}`,
  );

  function choose(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next);
  }

  const disciplinePills: Pill<string>[] = [
    { value: "", label: t("ratings.overall") },
    ...(disciplines.data ?? []).map((item) => ({ value: item.id, label: item.name })),
  ];
  const filterPills: Pill<NonNullable<RankingFilter> | "">[] = [
    { value: "", label: t("ratings.all") },
    ...RANKING_FILTERS.map((value) => ({ value, label: t(`ratings.${value}`) })),
  ];

  return (
    <>
      <h1>{t("ratings.title")}</h1>
      <p className="muted">{t("ratings.hint")}</p>
      <div className="filters">
        <PillSelect
          label={t("disciplines.choose")}
          options={disciplinePills}
          value={discipline}
          onChange={(value) => choose("discipline", value)}
        />
        <PillSelect
          label={t("ratings.show")}
          options={filterPills}
          value={filter ?? ""}
          onChange={(value) => choose("show", value)}
        />
      </div>
      {!discipline && <p className="hint">{t("ratings.overallHint")}</p>}
      <ApiContent state={ranking}>
        {(rows) => (
          <TableShell rows={rows.length} empty={<EmptyRanking />}>
            <thead>
              <tr>
                <th className="number">{t("ratings.rank")}</th>
                <th>{t("ratings.name")}</th>
                <th className="optional">{t("bots.version")}</th>
                <th className="optional">{t("bots.owner")}</th>
                <th className="optional">{t("ratings.type")}</th>
                <th className="number">{t("bots.rating")}</th>
                <th className="number">{t("bots.ratedGames")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={rowKey(row)}>
                  <td className="number">{index + 1}</td>
                  {row.kind === "bot" ? (
                    <>
                      <td>
                        <SideName
                          side={{ bot_id: row.bot.id, name: row.bot.name, version: null }}
                        />
                      </td>
                      <td className="optional">{row.bot.version}</td>
                      <td className="optional">{row.bot.owner ?? t("bots.builtin")}</td>
                      <td className="optional">{t(`language.${row.bot.language}`)}</td>
                    </>
                  ) : (
                    <>
                      <td>{row.username}</td>
                      <td className="optional">{t("common.none")}</td>
                      <td className="optional">{t("common.none")}</td>
                      <td className="optional">{t("ratings.player")}</td>
                    </>
                  )}
                  <td className="number">{row.rating.value}</td>
                  <td className="number">{row.rating.games}</td>
                </tr>
              ))}
            </tbody>
          </TableShell>
        )}
      </ApiContent>
    </>
  );
}

/** Before the first counted game: what fills the ranking and where to start one (G11). */
function EmptyRanking() {
  const { t } = useTranslation();
  return (
    <>
      {t("ratings.empty")} <Link to="/matches">{t("nav.matches")}</Link> ·{" "}
      <Link to="/play">{t("nav.play")}</Link>
    </>
  );
}

function rowKey(row: RankingRow): string {
  return row.kind === "bot" ? `bot/${row.bot.id}` : `player/${row.username}`;
}
