import { describe, expect, it } from "vitest";

import { START_FEN } from "../test/fixtures";
import { fullmoveNumber, materialBalance, moveSquares, sideToMove } from "./fen";

describe("fen", () => {
  it("reads side to move and move number", () => {
    expect(sideToMove(START_FEN)).toBe("w");
    expect(sideToMove("8/8/8/8/8/8/8/k6K b - - 0 37")).toBe("b");
    expect(fullmoveNumber("8/8/8/8/8/8/8/k6K b - - 0 37")).toBe(37);
    expect(fullmoveNumber("8/8/8/8/8/8/8/k6K b - -")).toBe(1);
  });

  it("counts material from White's side", () => {
    expect(materialBalance(START_FEN)).toBe(0);
    // White is a queen and a pawn up; kings do not count.
    expect(materialBalance("4k3/8/8/8/8/8/P7/3QK3 w - - 0 1")).toBe(10);
    expect(materialBalance("4k3/8/8/8/8/8/8/4K2r w - - 0 1")).toBe(-5);
  });

  it("splits a UCI move into its squares", () => {
    expect(moveSquares("e7e8q")).toEqual(["e7", "e8"]);
  });
});
