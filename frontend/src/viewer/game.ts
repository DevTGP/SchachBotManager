import type { Match, Move } from "../api/types";
import { fullmoveNumber, sideToMove, type Color } from "../chess/fen";

/** The position after `ply` moves; ply 0 is the start position. */
export function positionAt(match: Match, ply: number): string {
  return ply === 0 ? match.start_fen : (match.moves[ply - 1]?.fen ?? match.start_fen);
}

/** The side that played the move with this index (0 for the first move). */
export function moverOf(match: Match, index: number): Color {
  return sideToMove(positionAt(match, index));
}

export interface Clocks {
  w: number;
  b: number;
}

/** Remaining time of both sides after `ply` moves, as the referee recorded it. */
export function clocksAt(match: Match, ply: number): Clocks {
  const initial = match.discipline.initial_time_ms;
  const clocks: Clocks = { w: initial, b: initial };
  match.moves.slice(0, ply).forEach((move, index) => {
    clocks[moverOf(match, index)] = move.clock_ms;
  });
  return clocks;
}

export interface MoveCell {
  ply: number;
  move: Move;
}

export interface MoveRow {
  number: number;
  white?: MoveCell;
  black?: MoveCell;
}

/** The moves in rows of one full move; a game starting with Black leaves the first white cell empty. */
export function moveRows(match: Match): MoveRow[] {
  const rows: MoveRow[] = [];
  match.moves.forEach((move, index) => {
    const before = positionAt(match, index);
    const number = fullmoveNumber(before);
    const cell = { ply: index + 1, move };
    let row = rows[rows.length - 1];
    if (row === undefined || row.number !== number || sideToMove(before) === "w") {
      row = { number };
      rows.push(row);
    }
    if (sideToMove(before) === "w") row.white = cell;
    else row.black = cell;
  });
  return rows;
}
