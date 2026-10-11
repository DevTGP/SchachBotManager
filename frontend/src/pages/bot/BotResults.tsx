import { useTranslation } from "react-i18next";

import { fetchBotRecord } from "../../api/botHistory";
import type { RecordCounts } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { useApi } from "../../hooks/useApi";

/**
 * Wins, draws and losses in all finished games except those against itself, in total and per
 * discipline; forfeits and games against people count too (E141).
 */
export function BotResults({ botId }: { botId: string }) {
  const { t } = useTranslation();
  const record = useApi((signal) => fetchBotRecord(botId, signal), `bot-record:${botId}`);
  return (
    <section>
      <h2>{t("bot.results")}</h2>
      <ApiContent state={record}>
        {(data) =>
          data.total.games === 0 ? (
            <p className="muted">{t("bot.noResults")}</p>
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>{t("matches.discipline")}</th>
                    <th className="number">{t("bot.games")}</th>
                    <th className="number">{t("bot.wins")}</th>
                    <th className="number">{t("bot.draws")}</th>
                    <th className="number">{t("bot.losses")}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.disciplines.map((entry) => (
                    <CountsRow
                      key={entry.discipline_id ?? "free"}
                      label={entry.name ?? t("bot.freeTimes")}
                      counts={entry}
                    />
                  ))}
                </tbody>
                <tfoot>
                  <CountsRow label={t("bot.total")} counts={data.total} />
                </tfoot>
              </table>
            </div>
          )
        }
      </ApiContent>
    </section>
  );
}

function CountsRow({ label, counts }: { label: string; counts: RecordCounts }) {
  return (
    <tr>
      <th scope="row">{label}</th>
      <td className="number">{counts.games}</td>
      <td className="number">{counts.wins}</td>
      <td className="number">{counts.draws}</td>
      <td className="number">{counts.losses}</td>
    </tr>
  );
}
