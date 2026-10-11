import type { TFunction } from "i18next";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { fetchBotEditions } from "../../api/tournaments";
import type { BotEdition } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { formatPoints } from "../../format/points";
import { useApi } from "../../hooks/useApi";

/** The tournament editions of exactly this version with its place, current while one runs (E180). */
export function BotEditions({ botId }: { botId: string }) {
  const { t } = useTranslation();
  const editions = useApi((signal) => fetchBotEditions(botId, signal), `bot-editions:${botId}`);
  return (
    <section>
      <h2>{t("bot.editions")}</h2>
      <ApiContent state={editions}>
        {(items) =>
          items.length === 0 ? (
            <p className="muted">{t("bot.noEditions")}</p>
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>{t("tournaments.tournament")}</th>
                    <th>{t("bot.edition")}</th>
                    <th>{t("tournaments.format")}</th>
                    <th className="number">{t("editions.seed")}</th>
                    <th className="number">{t("editions.place")}</th>
                    <th className="number">{t("leagues.points")}</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {items.map((entry) => (
                    <tr key={entry.edition_id}>
                      <td>
                        <Link to={`/tournaments/${entry.tournament_id}`}>
                          {entry.tournament_name}
                        </Link>
                      </td>
                      <td>
                        <Link to={`/editions/${entry.edition_id}`}>
                          {t("tournaments.editionNumber", { number: entry.number })}
                        </Link>
                      </td>
                      <td>{t(`tournamentFormat.${entry.format}`)}</td>
                      <td className="number">{entry.seed}</td>
                      <td className="number">
                        {entry.place === null
                          ? "–"
                          : t("bot.rankOf", { rank: entry.place, size: entry.participants })}
                      </td>
                      <td className="number">
                        {entry.points === null ? "–" : formatPoints(entry.points)}
                      </td>
                      <td>{state(entry, t)}</td>
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

function state(entry: BotEdition, t: TFunction): string {
  if (entry.withdrawn) return t("outcome.withdrawn");
  return entry.status === "running" ? t("editionStatus.running") : "";
}
