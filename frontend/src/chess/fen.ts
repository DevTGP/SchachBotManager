export type Color = "w" | "b";

const PIECE_VALUES: Record<string, number> = { p: 1, n: 3, b: 3, r: 5, q: 9 };

/** The side to move, the second FEN field. */
export function sideToMove(fen: string): Color {
  return fen.split(" ")[1] === "b" ? "b" : "w";
}

/** The number of the full move, the sixth FEN field; 1 if missing. */
export function fullmoveNumber(fen: string): number {
  const number = Number(fen.split(" ")[5]);
  return Number.isInteger(number) && number > 0 ? number : 1;
}

/** White's material minus Black's, in pawns (P 1, N 3, B 3, R 5, Q 9). */
export function materialBalance(fen: string): number {
  let balance = 0;
  for (const symbol of fen.split(" ")[0] ?? "") {
    const value = PIECE_VALUES[symbol.toLowerCase()];
    if (value === undefined) continue;
    balance += symbol === symbol.toUpperCase() ? value : -value;
  }
  return balance;
}

/** Origin and target square of a UCI move such as e7e8q. */
export function moveSquares(uci: string): [string, string] {
  return [uci.slice(0, 2), uci.slice(2, 4)];
}
