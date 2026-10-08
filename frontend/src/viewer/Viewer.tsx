import { useState } from "react";
import { useTranslation } from "react-i18next";

import type { Match } from "../api/types";
import { materialBalance, sideToMove, type Color } from "../chess/fen";
import { playersLabel } from "../format/botLabel";
import { Board } from "./Board";
import { Controls } from "./Controls";
import { ExportPanel } from "./ExportPanel";
import { clocksAt, moverOf, positionAt } from "./game";
import { MatchDetails } from "./MatchDetails";
import { MoveInfoPanel } from "./MoveInfoPanel";
import { MoveList } from "./MoveList";
import { PlayerBar } from "./PlayerBar";
import { usePlayback } from "./usePlayback";
import { useViewerKeys } from "./useViewerKeys";
import { useViewerPly } from "./useViewerPly";

export function Viewer({ match, live }: { match: Match; live: boolean }) {
  const { t } = useTranslation();
  const total = match.moves.length;
  const position = useViewerPly(total, live);
  const { ply, goTo } = position;
  const playback = usePlayback(match.moves, ply, goTo);
  useViewerKeys(ply, total, goTo, playback.toggle);
  const [flipped, setFlipped] = useState(false);

  const fen = positionAt(match, ply);
  const lastMove = ply > 0 ? match.moves[ply - 1] : undefined;
  const clocks = clocksAt(match, ply);
  const balance = materialBalance(fen);
  // A finished match has nobody to move.
  const toMove: Color | undefined = live ? sideToMove(fen) : undefined;
  const bottom: Color = flipped ? "b" : "w";
  const top: Color = flipped ? "w" : "b";

  function bar(color: Color) {
    return (
      <PlayerBar
        side={color === "w" ? match.white : match.black}
        color={color}
        clockMs={clocks[color]}
        lead={color === "w" ? balance : -balance}
        toMove={toMove === color}
      />
    );
  }

  return (
    <div className="viewer">
      <div className="viewer-board">
        {bar(top)}
        <Board fen={fen} lastMove={lastMove?.uci} orientation={flipped ? "black" : "white"} />
        {bar(bottom)}
        <Controls
          position={position}
          total={total}
          live={live}
          playback={playback}
          onFlip={() => setFlipped((value) => !value)}
        />
        <p className="muted small">{t("viewer.keyboard")}</p>
      </div>
      <div className="viewer-side">
        <h1>{playersLabel(match)}</h1>
        <MatchDetails match={match} />
        <h2>{t("viewer.moves")}</h2>
        <MoveList match={match} ply={ply} goTo={goTo} />
        {lastMove && (
          <>
            <h2>{t("viewer.info")}</h2>
            <MoveInfoPanel info={lastMove.info} mover={moverOf(match, ply - 1)} />
          </>
        )}
        <h2>{t("viewer.export")}</h2>
        <ExportPanel matchId={match.id} fen={fen} ply={ply} />
      </div>
    </div>
  );
}
