import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { SeasonTier } from "../../api/types";
import { sideLabel } from "../../format/botLabel";
import { formatPoints } from "../../format/points";

/** The table of one tier; withdrawn bots stand at the end without a rank (E135). */
export function TierTable({ tier, seasonId }: { tier: SeasonTier; seasonId: string }) {
  const { t } = useTranslation();
  return (
    <section>
      <h2>{t("seasons.tier", { tier: tier.tier })}</h2>
      <p className="muted">
        {t("seasons.progress", { finished: tier.finished, games: tier.games })}{" "}
        <Link to={`/matches?season=${seasonId}&tier=${tier.tier}`}>{t("seasons.games")}</Link>
      </p>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>{t("ratings.rank")}</th>
              <th>{t("bots.name")}</th>
              <th className="number">{t("bot.games")}</th>
              <th className="number">{t("bot.wins")}</th>
              <th className="number">{t("bot.draws")}</th>
              <th className="number">{t("bot.losses")}</th>
              <th className="number">{t("leagues.points")}</th>
              <th>{t("seasons.outcome")}</th>
            </tr>
          </thead>
          <tbody>
            {tier.table.map((row) => (
              <tr key={row.bot.bot_id}>
                <td>{row.rank ?? "–"}</td>
                <td>
                  <Link to={`/bots/${row.bot.bot_id}`}>{sideLabel(row.bot)}</Link>
                </td>
                <td className="number">{row.games}</td>
                <td className="number">
                  {row.forfeit_wins > 0
                    ? t("seasons.wins", { wins: row.wins, forfeits: row.forfeit_wins })
                    : row.wins}
                </td>
                <td className="number">{row.draws}</td>
                <td className="number">{row.losses}</td>
                <td className="number">{formatPoints(row.points)}</td>
                <td>
                  {row.outcome
                    ? t(`outcome.${row.outcome}`)
                    : row.withdrawn
                      ? t("outcome.withdrawn")
                      : ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
