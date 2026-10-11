import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { fetchOpponents } from "../../api/endpoints";
import { ApiContent } from "../../components/ApiContent";
import { SideName } from "../../components/SideName";
import { TableShell } from "../../components/TableShell";
import { useApi } from "../../hooks/useApi";

/** The record against every other bot from finished single games, most games first (E161). */
export function BotOpponents({ botId }: { botId: string }) {
  const { t } = useTranslation();
  const opponents = useApi((signal) => fetchOpponents(botId, signal), `opponents:${botId}`);
  return (
    <section>
      <h2>{t("bot.record")}</h2>
      <ApiContent state={opponents}>
        {(items) => (
          <TableShell rows={items.length} empty={t("bot.noRecord")}>
            <thead>
              <tr>
                <th>{t("bot.opponent")}</th>
                <th>{t("bots.version")}</th>
                <th className="number">{t("bot.games")}</th>
                <th className="number">{t("bot.wins")}</th>
                <th className="number">{t("bot.draws")}</th>
                <th className="number">{t("bot.losses")}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((opponent) => (
                <tr key={opponent.bot_id}>
                  <td>
                    <SideName side={opponent} />
                  </td>
                  <td>{opponent.version ?? "–"}</td>
                  <td className="number">
                    <Link to={`/matches?bot=${botId}&opponent=${opponent.bot_id}`}>
                      {opponent.games}
                    </Link>
                  </td>
                  <td className="number">{opponent.wins}</td>
                  <td className="number">{opponent.draws}</td>
                  <td className="number">{opponent.losses}</td>
                </tr>
              ))}
            </tbody>
          </TableShell>
        )}
      </ApiContent>
    </section>
  );
}
