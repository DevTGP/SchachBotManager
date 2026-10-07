import { describe, expect, it } from "vitest";

import { match, OPENING, START_FEN } from "../test/fixtures";
import { clocksAt, moveRows, moverOf, positionAt } from "./game";

const BLACK_TO_MOVE = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1";

describe("game", () => {
  it("returns the stored position after each move", () => {
    const game = match();
    expect(positionAt(game, 0)).toBe(START_FEN);
    expect(positionAt(game, 2)).toBe(OPENING[1]?.fen);
  });

  it("gives each side its clock after its last move", () => {
    const game = match();
    expect(clocksAt(game, 0)).toEqual({ w: 180_000, b: 180_000 });
    expect(clocksAt(game, 1)).toEqual({ w: 179_000, b: 180_000 });
    expect(clocksAt(game, 3)).toEqual({ w: 176_500, b: 178_000 });
  });

  it("puts White and Black of one move number in one row", () => {
    const rows = moveRows(match());
    expect(rows.map((row) => [row.number, row.white?.move.san, row.black?.move.san])).toEqual([
      [1, "e4", "e5"],
      [2, "Nf3", undefined],
    ]);
  });

  it("leaves White's cell empty when the game starts with Black", () => {
    const game = match({ start_fen: BLACK_TO_MOVE, moves: OPENING.slice(1) });
    expect(moverOf(game, 0)).toBe("b");
    const rows = moveRows(game);
    expect(rows.map((row) => [row.number, row.white?.ply, row.black?.ply])).toEqual([
      [1, undefined, 1],
      [2, 2, undefined],
    ]);
    expect(clocksAt(game, 1)).toEqual({ w: 180_000, b: 178_000 });
  });
});
