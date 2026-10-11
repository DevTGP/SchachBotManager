import { useTranslation } from "react-i18next";

import type { EditionTableRow } from "../../api/types";
import { SideName } from "../../components/SideName";
import { formatPoints } from "../../format/points";

/**
 * The table of a round robin or Swiss edition, withdrawn bots at the end without a rank (E177).
 * Byes only exist in the Swiss system; Buchholz shows where it counts.
 */
export function EditionTable({
  rows,
  swiss,
  buchholz,
}: {
  rows: EditionTableRow[];
  swiss: boolean;
  buchholz: boolean;
}) {
  const { t } = useTranslation();
  const showBuchholz = swiss || buchholz;
  return (
    <section>
      <h2>{t("editions.table")}</h2>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>{t("ratings.rank")}</th>
              <th>{t("bots.name")}</th>
              <th>{t("bots.version")}</th>
              <th className="number">{t("bot.games")}</th>
              <th className="number">{t("bot.wins")}</th>
              <th className="number">{t("bot.draws")}</th>
              <th className="number">{t("bot.losses")}</th>
              {swiss && <th className="number">{t("editions.byes")}</th>}
              <th className="number">{t("leagues.points")}</th>
              {showBuchholz && <th className="number">{t("tiebreak.buchholz")}</th>}
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.bot.bot_id}>
                <td>{row.rank ?? "–"}</td>
                <td>
                  <SideName side={row.bot} />
                </td>
                <td>{row.bot.version ?? "–"}</td>
                <td className="number">{row.games}</td>
                <td className="number">
                  {row.forfeit_wins > 0
                    ? t("seasons.wins", { wins: row.wins, forfeits: row.forfeit_wins })
                    : row.wins}
                </td>
                <td className="number">{row.draws}</td>
                <td className="number">{row.losses}</td>
                {swiss && <td className="number">{row.byes}</td>}
                <td className="number">{formatPoints(row.points)}</td>
                {showBuchholz && <td className="number">{formatPoints(row.buchholz)}</td>}
                <td>{row.withdrawn ? t("outcome.withdrawn") : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
