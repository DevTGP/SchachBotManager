import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router";

import { fetchDisciplines } from "../api/endpoints";
import { ApiContent } from "../components/ApiContent";
import { useApi } from "../hooks/useApi";
import { RANKING_FILTERS, loadRanking, type RankingRow } from "./ranking";

/**
 * Bots and players with at least one counted game, highest rating first (E103, E118), in one
 * discipline or overall (E163). Filter and discipline live in the URL (show, discipline), so
 * every view can be linked. Players have no link: there is no page of a player. Version and
 * creator have columns of their own (E164).
 */
export function RatingsPage() {
  const { t } = useTranslation();
  const [params, setParams] = useSearchParams();
  const filter = RANKING_FILTERS.find((value) => value === params.get("show"));
  const discipline = params.get("discipline") ?? undefined;
  const disciplines = useApi(fetchDisciplines, "disciplines");
  const ranking = useApi(
    (signal) => loadRanking(filter, discipline, signal),
    `ratings/${filter}/${discipline}`,
  );

  function choose(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next);
  }

  return (
    <>
      <h1>{t("ratings.title")}</h1>
      <p className="muted">{t("ratings.hint")}</p>
      <div className="filters">
        <label>
          {t("disciplines.choose")}
          <select
            value={discipline ?? ""}
            onChange={(event) => choose("discipline", event.target.value)}
          >
            <option value="">{t("ratings.overall")}</option>
            {(disciplines.data ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("ratings.show")}
          <select value={filter ?? ""} onChange={(event) => choose("show", event.target.value)}>
            <option value="">{t("ratings.all")}</option>
            {RANKING_FILTERS.map((value) => (
              <option key={value} value={value}>
                {t(`ratings.${value}`)}
              </option>
            ))}
          </select>
        </label>
      </div>
      {!discipline && <p className="hint">{t("ratings.overallHint")}</p>}
      <ApiContent state={ranking}>
        {(rows) =>
          rows.length === 0 ? (
            <p className="muted">{t("ratings.empty")}</p>
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>{t("ratings.rank")}</th>
                    <th>{t("ratings.name")}</th>
                    <th>{t("bots.version")}</th>
                    <th>{t("bots.owner")}</th>
                    <th>{t("ratings.type")}</th>
                    <th>{t("bots.rating")}</th>
                    <th>{t("bots.ratedGames")}</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, index) => (
                    <tr key={rowKey(row)}>
                      <td>{index + 1}</td>
                      {row.kind === "bot" ? (
                        <>
                          <td>
                            <Link to={`/bots/${row.bot.id}`}>{row.bot.name}</Link>
                          </td>
                          <td>{row.bot.version}</td>
                          <td>{row.bot.owner ?? t("bots.builtin")}</td>
                          <td>{t(`language.${row.bot.language}`)}</td>
                        </>
                      ) : (
                        <>
                          <td>{row.username}</td>
                          <td>{t("common.none")}</td>
                          <td>{t("common.none")}</td>
                          <td>{t("ratings.player")}</td>
                        </>
                      )}
                      <td>{row.rating.value}</td>
                      <td>{row.rating.games}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        }
      </ApiContent>
    </>
  );
}

function rowKey(row: RankingRow): string {
  return row.kind === "bot" ? `bot/${row.bot.id}` : `player/${row.username}`;
}
