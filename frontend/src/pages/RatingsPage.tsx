import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router";

import { ApiContent } from "../components/ApiContent";
import { botLabel } from "../format/botLabel";
import { useApi } from "../hooks/useApi";
import { RANKING_FILTERS, loadRanking, type RankingRow } from "./ranking";

/**
 * Bots and players with at least one counted game, highest rating first (E103, E118). The
 * filter lives in the URL (show), so every view can be linked. Players have no link: their
 * games are not public (E115).
 */
export function RatingsPage() {
  const { t } = useTranslation();
  const [params, setParams] = useSearchParams();
  const filter = RANKING_FILTERS.find((value) => value === params.get("show"));
  const ranking = useApi((signal) => loadRanking(filter, signal), `ratings/${filter}`);

  function choose(value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set("show", value);
    else next.delete("show");
    setParams(next);
  }

  return (
    <>
      <h1>{t("ratings.title")}</h1>
      <p className="muted">{t("ratings.hint")}</p>
      <div className="filters">
        <label>
          {t("ratings.show")}
          <select value={filter ?? ""} onChange={(event) => choose(event.target.value)}>
            <option value="">{t("ratings.all")}</option>
            {RANKING_FILTERS.map((value) => (
              <option key={value} value={value}>
                {t(`ratings.${value}`)}
              </option>
            ))}
          </select>
        </label>
      </div>
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
                    <th>{t("ratings.type")}</th>
                    <th>{t("bots.rating")}</th>
                    <th>{t("bots.ratedGames")}</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, index) => (
                    <tr key={rowKey(row)}>
                      <td>{index + 1}</td>
                      <td>
                        {row.kind === "bot" ? (
                          <Link to={`/bots/${row.bot.id}`}>{botLabel(row.bot)}</Link>
                        ) : (
                          row.username
                        )}
                      </td>
                      <td>
                        {row.kind === "bot"
                          ? t(`language.${row.bot.language}`)
                          : t("ratings.player")}
                      </td>
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
