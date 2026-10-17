// Bot SDK of SchachBotManager (spec/api/): board and moves, the bot base class and run.
import { native } from "./native.ts";

export { Board } from "./board.ts";
export { Bot } from "./bot.ts";
export { Clock } from "./clock.ts";
export * from "./constants.ts";
export { loadData } from "./data.ts";
export {
  ChessError,
  DataNotFoundError,
  IllegalMoveError,
  InvalidArgumentError,
  InvalidFenError,
  InvalidStateError,
  InvalidUciError,
} from "./errors.ts";
export { Log } from "./log.ts";
export { Move, NULL_MOVE, RESIGN } from "./move.ts";
export type { GameInfo, GameResult, Info, PlacedPiece } from "./records.ts";
export type { BotClass, RunOptions } from "./runtime.ts";
export { run } from "./runtime.ts";

/** Version of the SDK, equal to the version of the core. */
export const version: string = native.version;
