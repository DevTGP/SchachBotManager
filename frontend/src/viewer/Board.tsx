import { Chessboard } from "react-chessboard";

import { moveSquares } from "../chess/fen";

const LAST_MOVE_STYLE = { backgroundColor: "rgba(255, 214, 0, 0.45)" };

/** Shows a stored position; the viewer needs no rules of its own. */
export function Board({
  fen,
  lastMove,
  orientation,
}: {
  fen: string;
  lastMove: string | undefined;
  orientation: "white" | "black";
}) {
  const squareStyles = lastMove
    ? Object.fromEntries(moveSquares(lastMove).map((square) => [square, LAST_MOVE_STYLE]))
    : {};
  return (
    <div className="board">
      <Chessboard
        options={{
          id: "viewer",
          position: fen,
          boardOrientation: orientation,
          squareStyles,
          allowDragging: false,
        }}
      />
    </div>
  );
}
