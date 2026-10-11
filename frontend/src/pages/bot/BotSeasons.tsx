import type { TFunction } from "i18next";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { fetchBotSeasons } from "../../api/leagues";
import type { BotSeason } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { formatPoints } from "../../format/points";
import { useApi } from "../../hooks/useApi";

/** The league seasons of exactly this version with its place, current while one runs (E139). */
export function BotSeasons({ botId }: { botId: string }) {
  const { t } = useTranslation();
  const seasons = useApi((signal) => fetchBotSeasons(botId, signal), `bot-seasons:${botId}`);
  return (
    <section>
      <h2>{t("bot.seasons")}</h2>
      <ApiContent state={seasons}>
        {(items) =>
          items.length === 0 ? (
            <p className="muted">{t("bot.noSeasons")}</p>
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>{t("leagues.league")}</th>
                    <th>{t("bot.season")}</th>
                    <th className="number">{t("bot.tier")}</th>
                    <th className="number">{t("ratings.rank")}</th>
                    <th className="number">{t("bot.games")}</th>
                    <th className="number">{t("leagues.points")}</th>
                    <th>{t("seasons.outcome")}</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((entry) => (
                    <tr key={entry.season_id}>
                      <td>
                        <Link to={`/leagues/${entry.league_id}`}>{entry.league_name}</Link>
                      </td>
                      <td>
                        <Link to={`/seasons/${entry.season_id}`}>
                          {t("bot.seasonNumber", { number: entry.number })}
                        </Link>
                      </td>
                      <td className="number">{entry.tier}</td>
                      <td className="number">
                        {entry.rank === null
                          ? "–"
                          : t("bot.rankOf", { rank: entry.rank, size: entry.tier_size })}
                      </td>
                      <td className="number">{entry.games}</td>
                      <td className="number">{formatPoints(entry.points)}</td>
                      <td>{outcome(entry, t)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        }
      </ApiContent>
    </section>
  );
}

function outcome(entry: BotSeason, t: TFunction): string {
  if (entry.outcome) return t(`outcome.${entry.outcome}`);
  if (entry.withdrawn) return t("outcome.withdrawn");
  return entry.status === "running" ? t("seasonStatus.running") : "";
}
