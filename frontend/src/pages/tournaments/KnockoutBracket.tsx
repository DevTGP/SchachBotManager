import type { TFunction } from "i18next";
import { useTranslation } from "react-i18next";

import type { Duel, DuelSide } from "../../api/types";
import { ActionsHeader, OpenCell } from "../../components/OpenCell";
import { PairingCells, PairingHeader } from "../../components/Pairing";
import { GameState } from "../../components/ScheduleRounds";
import { SideName } from "../../components/SideName";
import { formatPoints } from "../../format/points";

/**
 * The bracket of a knockout edition round by round: the duels with their score and how each was
 * decided, then their games; the first round with an open duel starts open, the last one once all are decided (E176,
 * E180).
 */
export function KnockoutBracket({ duels }: { duels: Duel[] }) {
  const { t } = useTranslation();
  const rounds = [...new Set(duels.map((duel) => duel.round))].sort((a, b) => a - b);
  const current =
    rounds.find((round) => duels.some((duel) => duel.round === round && !duel.decided)) ??
    rounds.at(-1);
  return (
    <section>
      <h2>{t("editions.bracket")}</h2>
      {rounds.map((round) => (
        <BracketRound
          key={round}
          round={round}
          duels={duels.filter((duel) => duel.round === round)}
          open={round === current}
        />
      ))}
    </section>
  );
}

function BracketRound({ round, duels, open }: { round: number; duels: Duel[]; open: boolean }) {
  const { t } = useTranslation();
  const decided = duels.filter((duel) => duel.decided).length;
  const games = duels.flatMap((duel) => duel.games.map((game) => ({ ...game, slot: duel.slot })));
  return (
    <details className="schedule-round" open={open}>
      <summary>
        {roundName(round, duels.length, t)}
        <span className="muted">
          {" · "}
          {t("editions.duelProgress", { decided, duels: duels.length })}
        </span>
      </summary>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th className="number">{t("editions.duel")}</th>
              <th>{t("editions.sideA")}</th>
              <th className="number">{t("editions.score")}</th>
              <th>{t("editions.sideB")}</th>
              <th>{t("editions.decision")}</th>
            </tr>
          </thead>
          <tbody>
            {duels.map((duel) => (
              <tr key={duel.slot}>
                <td className="number">{duel.slot}</td>
                <td>
                  <DuelSideName side={duel.a} winner={duel.winner} />
                </td>
                <td className="number">{score(duel)}</td>
                <td>
                  <DuelSideName side={duel.b} winner={duel.winner} />
                </td>
                <td>{duel.decided_by ? t(`decidedBy.${duel.decided_by}`) : t("editions.open")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {games.length > 0 && (
        <div className="table-scroll">
          <table className="match-table">
            <thead>
              <tr>
                <th className="number">{t("editions.duel")}</th>
                <th>{t("editions.phase")}</th>
                <PairingHeader />
                <th>{t("bot.result")}</th>
                <ActionsHeader />
              </tr>
            </thead>
            <tbody>
              {games.map((game) => (
                <tr key={game.match_id}>
                  <td className="number">{game.slot}</td>
                  <td>{t(`duelPhase.${game.phase}`, { game: game.game })}</td>
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
      )}
    </details>
  );
}

/** Final, semi-final and quarter-final by name, earlier rounds by number. */
function roundName(round: number, duels: number, t: TFunction): string {
  if (duels === 1) return t("editions.final");
  if (duels === 2) return t("editions.semiFinal");
  if (duels === 4) return t("editions.quarterFinal");
  return t("seasons.round", { round });
}

function score(duel: Duel): string {
  if (!duel.a || !duel.b || duel.games.length === 0) return "–";
  const regular = `${formatPoints(duel.a.points)}–${formatPoints(duel.b.points)}`;
  const tiebreak = duel.a.tiebreak_points + duel.b.tiebreak_points > 0;
  return tiebreak
    ? `${regular} (${formatPoints(duel.a.tiebreak_points)}–${formatPoints(duel.b.tiebreak_points)})`
    : regular;
}

function DuelSideName({ side, winner }: { side: DuelSide | null; winner: string | null }) {
  const { t } = useTranslation();
  if (!side) return <span className="muted">–</span>;
  const name = (
    <>
      <SideName side={side.bot} /> <span className="muted">({side.seed})</span>
    </>
  );
  return side.bot.bot_id === winner ? (
    <strong title={t("editions.winnerMark")}>{name}</strong>
  ) : (
    name
  );
}
