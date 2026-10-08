import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";

import { loadSeat } from "../../play/seats";
import { splitMoves } from "../../play/protocol";
import { type SocketFactory, usePlayGame } from "../../play/usePlayGame";
import { GameClock } from "./GameClock";
import { PlayBoard } from "./PlayBoard";
import { PromotionChoice } from "./PromotionChoice";

/** A running game of the person against a bot, over the gateway's WebSocket (E112, E114). */
export function GamePage({ createSocket }: { createSocket?: SocketFactory }) {
  const { t } = useTranslation();
  const { id = "" } = useParams();
  const seat = loadSeat(id);
  if (!seat) {
    return (
      <>
        <h1>{t("play.title")}</h1>
        <p className="error" role="alert">
          {t("play.noSeat")}
        </p>
        <Link to="/play">{t("play.newGame")}</Link>
      </>
    );
  }
  return <Game matchId={id} seat={seat} createSocket={createSocket} />;
}

function Game({
  matchId,
  seat,
  createSocket,
}: {
  matchId: string;
  seat: string;
  createSocket?: SocketFactory;
}) {
  const { t } = useTranslation();
  const game = usePlayGame(matchId, seat, createSocket);
  const [promotion, setPromotion] = useState<string[] | undefined>(undefined);
  const { state, phase } = game;

  if (!state) {
    return (
      <>
        <h1>{t("play.title")}</h1>
        <p role="status">{t(`play.phase.${phase}`)}</p>
        {phase !== "connecting" && phase !== "waiting" && (
          <Link to="/play">{t("play.newGame")}</Link>
        )}
      </>
    );
  }

  const own = state.color;
  const other = own === "white" ? "black" : "white";
  const legal = splitMoves(state.legal_moves);
  const moves = splitMoves(state.moves);
  const san = splitMoves(state.san);
  const playing = phase === "playing";

  function onMove(uci: string) {
    setPromotion(undefined);
    game.move(uci);
  }

  function onResign() {
    if (window.confirm(t("play.resignConfirm"))) game.resign();
  }

  return (
    <div className="viewer">
      <div className="viewer-board">
        <GameClock state={state} color={other} receivedAt={game.receivedAt} />
        <PlayBoard
          fen={state.fen}
          orientation={own}
          lastMove={moves.at(-1)}
          legal={playing ? legal : []}
          onMove={onMove}
          onPromotion={setPromotion}
        />
        <GameClock state={state} color={own} receivedAt={game.receivedAt} />
        {promotion && (
          <PromotionChoice
            choices={promotion}
            onChoose={onMove}
            onCancel={() => setPromotion(undefined)}
          />
        )}
      </div>
      <div className="viewer-side">
        <h1>
          {state.white} – {state.black}
        </h1>
        <p role="status">{status(t, phase, state.result, state.termination, legal.length > 0)}</p>
        {game.problem && (
          <p className="error" role="alert">
            {t([`play.problem.${game.problem}`, "play.problem.other"])}
          </p>
        )}
        {playing && (
          <button type="button" onClick={onResign}>
            {t("play.resign")}
          </button>
        )}
        {!playing && <Link to="/play">{t("play.newGame")}</Link>}
        <h2>{t("viewer.moves")}</h2>
        {san.length === 0 ? (
          <p className="muted">{t("viewer.noMoves")}</p>
        ) : (
          <ol className="play-moves">
            {pairs(san).map(([white, black], index) => (
              <li key={index}>
                {white} {black}
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}

function status(
  t: (key: string, options?: Record<string, string>) => string,
  phase: string,
  result: string | null,
  termination: string | null,
  myTurn: boolean,
): string {
  if (result !== null) {
    return t("play.over", { result, termination: t(`termination.${termination ?? "aborted"}`) });
  }
  if (phase !== "playing") return t(`play.phase.${phase}`);
  return t(myTurn ? "play.yourTurn" : "play.botThinks");
}

function pairs(san: string[]): [string, string][] {
  const result: [string, string][] = [];
  for (let index = 0; index < san.length; index += 2) {
    result.push([san[index] ?? "", san[index + 1] ?? ""]);
  }
  return result;
}
