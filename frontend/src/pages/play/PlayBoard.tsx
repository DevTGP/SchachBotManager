import { useState } from "react";
import { Chessboard } from "react-chessboard";

import { moveSquares } from "../../chess/fen";
import { movesBetween, type PlayColor } from "../../play/protocol";

const LAST_MOVE_STYLE = { backgroundColor: "rgba(255, 214, 0, 0.45)" };
const SELECTED_STYLE = { backgroundColor: "rgba(20, 120, 220, 0.45)" };
const TARGET_STYLE = { boxShadow: "inset 0 0 0 4px rgba(20, 120, 220, 0.6)" };

/**
 * The board of a running game: the person drags or clicks a piece, then the target. Only moves
 * from the server's list are offered; several moves between the same squares are a promotion,
 * which `onPromotion` asks about.
 */
export function PlayBoard({
  fen,
  orientation,
  lastMove,
  legal,
  onMove,
  onPromotion,
}: {
  fen: string;
  orientation: PlayColor;
  lastMove: string | undefined;
  legal: string[];
  onMove: (uci: string) => void;
  onPromotion: (choices: string[]) => void;
}) {
  const [selected, setSelected] = useState<string | undefined>(undefined);
  const own = orientation === "white" ? "w" : "b";

  function tryMove(from: string, to: string): boolean {
    setSelected(undefined);
    const moves = movesBetween(legal, from, to);
    const [only] = moves;
    if (moves.length === 1 && only) onMove(only);
    else if (moves.length > 1) onPromotion(moves);
    return moves.length === 1;
  }

  function onSquareClick(square: string) {
    if (selected && selected !== square && movesBetween(legal, selected, square).length > 0) {
      tryMove(selected, square);
    } else if (legal.some((move) => move.startsWith(square))) {
      setSelected(square);
    } else {
      setSelected(undefined);
    }
  }

  const squareStyles: Record<string, React.CSSProperties> = {};
  if (lastMove) for (const square of moveSquares(lastMove)) squareStyles[square] = LAST_MOVE_STYLE;
  if (selected) {
    squareStyles[selected] = SELECTED_STYLE;
    for (const move of legal.filter((candidate) => candidate.startsWith(selected))) {
      squareStyles[move.slice(2, 4)] = TARGET_STYLE;
    }
  }

  return (
    <div className="board">
      <Chessboard
        options={{
          id: "play",
          position: fen,
          boardOrientation: orientation,
          squareStyles,
          allowDragging: legal.length > 0,
          canDragPiece: ({ piece }) => legal.length > 0 && piece.pieceType.startsWith(own),
          onPieceDrop: ({ sourceSquare, targetSquare }) =>
            targetSquare !== null && tryMove(sourceSquare, targetSquare),
          onSquareClick: ({ square }) => onSquareClick(square),
        }}
      />
    </div>
  );
}
