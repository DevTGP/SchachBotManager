import { useTranslation } from "react-i18next";

import type { ScheduleGame, ScheduleRound } from "../api/types";
import { pairing, pairingResult } from "../format/pairing";
import { useHashTarget } from "../hooks/useHashTarget";
import { ActionsHeader, OpenCell } from "./OpenCell";
import { PairingCells, PairingHeader } from "./Pairing";

const OVER = new Set(["finished", "aborted"]);

/**
 * Rounds of a league tier or a tournament edition, each a collapsible table of its boards with
 * the result or the state of the game; the first round still being played starts open (E138,
 * E180), as does the round a link names by its anchor (E188). Pairings read alphabetically like
 * every game list (E165).
 */
export function ScheduleRounds({
  rounds,
  empty,
  anchor,
}: {
  rounds: ScheduleRound[];
  empty: string;
  anchor: (round: number) => string;
}) {
  if (rounds.length === 0) return <p className="muted">{empty}</p>;
  const current = rounds.find((round) => !isOver(round))?.round;
  return rounds.map((round) => (
    <RoundGames
      key={round.round}
      round={round}
      id={anchor(round.round)}
      open={round.round === current}
    />
  ));
}

function isOver(round: ScheduleRound): boolean {
  return round.games.every((game) => OVER.has(game.status));
}

function RoundGames({ round, id, open }: { round: ScheduleRound; id: string; open: boolean }) {
  const { t } = useTranslation();
  const { ref, targeted } = useHashTarget<HTMLDetailsElement>(id);
  const finished = round.games.filter((game) => game.status === "finished").length;
  return (
    <details ref={ref} id={id} className="schedule-round" open={open || targeted}>
      <summary>
        {t("seasons.round", { round: round.round })}
        <span className="muted">
          {" · "}
          {t("seasons.roundProgress", { finished, games: round.games.length })}
        </span>
      </summary>
      <div className="table-scroll">
        <table className="match-table">
          <thead>
            <tr>
              <th className="number">{t("seasons.board")}</th>
              <PairingHeader />
              <th>{t("bot.result")}</th>
              <ActionsHeader />
            </tr>
          </thead>
          <tbody>
            {round.games.map((game) => (
              <tr key={game.match_id}>
                <td className="number">{game.board}</td>
                <PairingCells match={game} />
                <td>
                  <GameState game={game} />
                </td>
                <OpenCell matchId={game.match_id} />
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {round.bye && <p className="muted">{t("seasons.bye", { bot: round.bye.name })}</p>}
    </details>
  );
}

/** The result of a finished game, a forfeit marked as such, otherwise the state of the game. */
export function GameState({ game }: { game: Omit<ScheduleGame, "board"> }) {
  const { t } = useTranslation();
  if (game.status !== "finished" || game.result === null) return <>{t(`status.${game.status}`)}</>;
  const result = pairingResult(game.result, pairing(game).flipped);
  if (game.termination === "forfeit_withdrawn" || game.termination === "forfeit_absent") {
    return <>{t("seasons.forfeitResult", { result })}</>;
  }
  return <>{result}</>;
}
