// Records of the bot API (spec/api/types.json) with fields in camelCase (E204). The SDK hands
// them over as frozen objects; Info is filled in by the bot.
import type { Color, Piece, Square } from "./constants.ts";
import type { Move } from "./move.ts";

/** Game parameters from init, passed to onGameStart. */
export interface GameInfo {
  readonly gameId: string;
  /** Own color. */
  readonly color: Color;
  readonly opponentName: string;
  readonly startFen: string;
  /** Base thinking time per side. */
  readonly initialTimeMs: number;
  /** Time added after each own move. */
  readonly incrementMs: number;
  /** Budget for start-up including onGameStart. */
  readonly startupMs: number;
  /** Fixed memory protection limit of the sandbox. */
  readonly memoryLimitMib: number;
  /** Display name of the discipline. */
  readonly discipline: string;
}

/** End of the game from game_over, passed to onGameEnd. */
export interface GameResult {
  /** 1-0, 0-1, 1/2-1/2 or * (aborted). */
  readonly result: string;
  readonly termination: string;
}

/** Search information sent with the move (E43); every field is optional. */
export interface Info {
  depth?: number;
  seldepth?: number;
  scoreCp?: number;
  scoreMate?: number;
  nodes?: number;
  pv?: readonly Move[];
  text?: string;
}

/** A piece with its square, as listed by Board.pieces (E190). */
export interface PlacedPiece {
  readonly square: Square;
  readonly piece: Piece;
}
