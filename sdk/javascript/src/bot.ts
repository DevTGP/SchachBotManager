// Bot (spec/api/bot.json): the base class the bot author extends.
import type { Board } from "./board.ts";
import type { Clock } from "./clock.ts";
import type { Move } from "./move.ts";
import type { GameInfo, GameResult, Info } from "./records.ts";

// The info reported during the current turn, per bot.
const reports = new WeakMap<Bot, Info>();

/**
 * Override chooseMove, optionally onGameStart and onGameEnd; start with run(MyBot). Fields of
 * the object keep their values from turn to turn.
 */
export abstract class Bot {
  /** Called once before the first turn, within the start-up budget. */
  onGameStart(info: GameInfo): void | Promise<void> {
    void info;
  }

  /**
   * The move to play in the position on board, or RESIGN; a Promise of it works as well. The
   * bot may make and undo moves on board freely; the SDK keeps its own game position.
   */
  abstract chooseMove(board: Board, clock: Clock): Move | Promise<Move>;

  /** Called after game_over for cleanup and last log lines. */
  onGameEnd(result: GameResult): void | Promise<void> {
    void result;
  }

  /** Sets the search information sent with the move of the current turn. */
  report(info: Info): void {
    if (typeof info !== "object" || info === null || Array.isArray(info)) {
      throw new TypeError("Bot.report: info must be an object");
    }
    reports.set(this, { ...info });
  }
}

/** The info reported during the turn; nothing carries over to the next one. */
export function takeReport(bot: Bot): Info | undefined {
  const info = reports.get(bot);
  reports.delete(bot);
  return info;
}
