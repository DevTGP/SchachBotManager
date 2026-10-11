import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { fetchSeasonSchedule } from "../../api/leagues";
import type { ScheduleGame, ScheduleRound } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { sideLabel } from "../../format/botLabel";
import { formatResult } from "../../format/result";
import { POLL_LIST_MS } from "../../hooks/polling";
import { useApi } from "../../hooks/useApi";

const OVER = new Set(["finished", "aborted"]);

/**
 * The rounds of one tier, each a collapsible table of its boards with the result or the state
 * of the game; the first round still being played starts open (E138).
 */
export function TierSchedule({
  seasonId,
  tier,
  running,
}: {
  seasonId: string;
  tier: number;
  running: boolean;
}) {
  const { t } = useTranslation();
  const schedule = useApi(
    (signal) => fetchSeasonSchedule(seasonId, tier, signal),
    `schedule:${seasonId}:${tier}`,
    running ? POLL_LIST_MS : undefined,
  );
  return (
    <>
      <h3>{t("seasons.schedule")}</h3>
      <ApiContent state={schedule}>
        {(data) => {
          if (data.rounds.length === 0) return <p className="muted">{t("seasons.noSchedule")}</p>;
          const current = data.rounds.find((round) => !isOver(round))?.round;
          return data.rounds.map((round) => (
            <RoundGames key={round.round} round={round} open={round.round === current} />
          ));
        }}
      </ApiContent>
    </>
  );
}

function isOver(round: ScheduleRound): boolean {
  return round.games.every((game) => OVER.has(game.status));
}

function RoundGames({ round, open }: { round: ScheduleRound; open: boolean }) {
  const { t } = useTranslation();
  const finished = round.games.filter((game) => game.status === "finished").length;
  return (
    <details className="schedule-round" open={open}>
      <summary>
        {t("seasons.round", { round: round.round })}
        <span className="muted">
          {" · "}
          {t("seasons.roundProgress", { finished, games: round.games.length })}
        </span>
      </summary>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th className="number">{t("seasons.board")}</th>
              <th>{t("viewer.white")}</th>
              <th>{t("viewer.black")}</th>
              <th>{t("bot.result")}</th>
            </tr>
          </thead>
          <tbody>
            {round.games.map((game) => (
              <tr key={game.match_id}>
                <td className="number">{game.board}</td>
                <td>
                  <Link to={`/bots/${game.white.bot_id}`}>{sideLabel(game.white)}</Link>
                </td>
                <td>
                  <Link to={`/bots/${game.black.bot_id}`}>{sideLabel(game.black)}</Link>
                </td>
                <td>
                  <Link to={`/matches/${game.match_id}`}>
                    <GameState game={game} />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {round.bye && <p className="muted">{t("seasons.bye", { bot: sideLabel(round.bye) })}</p>}
    </details>
  );
}

function GameState({ game }: { game: ScheduleGame }) {
  const { t } = useTranslation();
  if (game.status !== "finished" || game.result === null) return <>{t(`status.${game.status}`)}</>;
  const result = formatResult(game.result);
  if (game.termination === "forfeit_withdrawn") {
    return <>{t("seasons.forfeitResult", { result })}</>;
  }
  return <>{result}</>;
}
