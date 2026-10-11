import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { fetchCompetitionGames } from "../../api/competitionGames";
import type { CompetitionGame } from "../../api/types";
import { TableShell } from "../../components/TableShell";
import { competitionName } from "../../format/competition";
import { formatDateTime } from "../../format/dateTime";
import { useApi } from "../../hooks/useApi";
import { useSession } from "../../session/sessionContext";

// A game is released while the page may be open.
const POLL_MS = 60_000;

/** The open league and tournament games of the own account, each played on /play/:id (E183). */
export function OwnCompetitionGames() {
  const { user } = useSession();
  if (!user) return null;
  return <GameList />;
}

function GameList() {
  const { t } = useTranslation();
  const games = useApi(
    (signal) => fetchCompetitionGames(signal),
    "account/competition-games",
    POLL_MS,
  );
  const items = games.data ?? [];
  if (items.length === 0) return null;
  return (
    <section>
      <h2>{t("competitionGame.title")}</h2>
      <p className="hint">{t("competitionGame.listHint")}</p>
      <TableShell rows={items.length} empty={null}>
        <thead>
          <tr>
            <th>{t("competitionGame.competition")}</th>
            <th>{t("competitionGame.opponent")}</th>
            <th>{t("play.color")}</th>
            <th>{t("competitionGame.state")}</th>
            <th>{t("matchTable.open")}</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.match.id}>
              <td>{competitionName(t, item)}</td>
              <td>{item.match[item.color === "white" ? "black" : "white"].name}</td>
              <td>{t(`viewer.${item.color}`)}</td>
              <td>
                <GameState item={item} />
              </td>
              <td>
                <Link to={`/play/${item.match.id}`}>{t("matchTable.open")}</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </TableShell>
    </section>
  );
}

function GameState({ item }: { item: CompetitionGame }) {
  const { t, i18n } = useTranslation();
  const readiness = item.match.readiness;
  if (item.match.status === "running" || readiness?.started_at) {
    return <>{t("competitionGame.running")}</>;
  }
  if (!readiness) return <>{t("competitionGame.waiting")}</>;
  const deadline = formatDateTime(readiness.deadline, i18n.language);
  return <>{t("competitionGame.until", { at: deadline })}</>;
}
