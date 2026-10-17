// One game from the bot's side: init, turns and game_over (state machine of bot-protokoll.md).
import { Board } from "./board.ts";
import type { Bot } from "./bot.ts";
import { takeReport } from "./bot.ts";
import type { Channel, Message } from "./channel.ts";
import { ProtocolError } from "./channel.ts";
import { Clock } from "./clock.ts";
import { ChessError } from "./errors.ts";
import { Log, setPly } from "./log.ts";
import { Move } from "./move.ts";
import { native } from "./native.ts";
import * as protocol from "./protocol.ts";
import type { GameInfo, GameResult } from "./records.ts";

/** A callback threw or returned something unusable; the process ends (E49). */
export class BotError extends Error {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "BotError";
  }
}

function describeValue(value: unknown): string {
  if (value === null || value === undefined) {
    return String(value);
  }
  if (typeof value === "object") {
    return value.constructor?.name ?? "object";
  }
  return typeof value;
}

/** Calls bot code and turns anything it throws into a BotError that keeps it as the cause. */
export async function guarded<T>(name: string, callback: () => T | Promise<T>): Promise<T> {
  try {
    return await callback();
  } catch (error) {
    const what =
      error instanceof Error ? `${error.name}: ${error.message}` : `${describeValue(error)}`;
    throw new BotError(`${name} threw ${what}`, { cause: error });
  }
}

/** The message of a BotError with the stack of the bot's exception, for the log. */
export function describe(error: BotError): string {
  const cause = error.cause;
  if (cause instanceof Error && cause.stack) {
    return `${error.message}\n${cause.stack}`;
  }
  return error.message;
}

/** info and result are set once init and game_over arrive. */
export class Game {
  readonly #bot: Bot;
  readonly #channel: Channel;
  #board: Board | undefined;
  #incrementMs = 0;
  info: GameInfo | undefined;
  result: GameResult | undefined;

  constructor(bot: Bot, channel: Channel) {
    this.#bot = bot;
    this.#channel = channel;
  }

  /** Answers referee messages until game_over or the end of the input. */
  async play(): Promise<void> {
    for (let message = await this.#channel.receive(); message !== null;) {
      const kind = message.type;
      if (kind === "init") {
        await this.#start(message);
      } else if (kind === "turn") {
        await this.#turn(message);
      } else if (kind === "error") {
        Log.error(`referee reports ${String(message.code)}: ${String(message.message)}`);
      } else if (kind === "game_over") {
        await this.#end(message);
        return;
      } else {
        Log.warn(`ignoring a message of unknown type ${JSON.stringify(kind)}`);
      }
      message = await this.#channel.receive();
    }
    Log.warn("input ended before game_over");
  }

  async #start(init: Message): Promise<void> {
    if (this.#board !== undefined) {
      throw new ProtocolError("init: second init in one game");
    }
    const info = protocol.gameInfo(init);
    this.info = info;
    this.#board = readFen("init", info.startFen);
    this.#incrementMs = info.incrementMs;
    const supported = protocol.supportedVersions(init);
    if (!supported.includes(protocol.PROTOCOL_VERSION)) {
      // The referee diagnoses the mismatch after ready; this line tells the author why.
      Log.error(
        `the referee supports protocol versions ${JSON.stringify(supported)}, ` +
          `this SDK speaks version ${protocol.PROTOCOL_VERSION}; update the SDK`,
      );
    }
    await guarded("onGameStart", () => this.#bot.onGameStart(info));
    await this.#channel.send(protocol.ready(native.version));
  }

  async #turn(turn: Message): Promise<void> {
    // First, so that elapsedMs covers everything the SDK does in this turn.
    const clock = new Clock(
      protocol.field(turn, "remaining_ms", "integer"),
      protocol.field(turn, "opponent_remaining_ms", "integer"),
      this.#incrementMs,
    );
    if (this.#board === undefined) {
      throw new ProtocolError("turn before init");
    }
    setPly(protocol.field(turn, "ply", "integer"));
    const board = this.#synchronize(this.#board, turn);
    takeReport(this.#bot);
    const copy = board.copy();
    const choice = await guarded("chooseMove", () => this.#bot.chooseMove(copy, clock));
    await this.#channel.send(this.#answer(choice));
    if (choice !== Move.RESIGN) {
      this.#playOwn(board, choice as Move);
    }
  }

  /** Applies the opponent's move and adopts the referee's position on a mismatch (E42). */
  #synchronize(board: Board, turn: Message): Board {
    const fen = protocol.field(turn, "fen", "string");
    // Read and written again, so an en passant square without a legal capture still compares
    // equal (E48).
    const reference = readFen("turn", fen);
    const lastMove = turn.last_move;
    if (lastMove !== undefined && lastMove !== null) {
      // A move that does not fit is repaired by the comparison below.
      try {
        board.makeMove(board.parseMove(lastMove as string));
      } catch (error) {
        if (!(error instanceof ChessError || error instanceof TypeError)) {
          throw error;
        }
      }
    }
    if (board.fen() === reference.fen()) {
      return board;
    }
    Log.warn(`own position differs from the referee's; continuing from ${fen}`);
    this.#board = reference;
    return reference;
  }

  #answer(choice: unknown): Message {
    if (!(choice instanceof Move)) {
      throw new BotError(`chooseMove returned ${describeValue(choice)}, not a Move`);
    }
    const info = takeReport(this.#bot);
    if (choice === Move.RESIGN) {
      return protocol.resign();
    }
    let uci: string;
    try {
      uci = choice.uci();
    } catch (error) {
      if (!(error instanceof ChessError)) {
        throw error;
      }
      throw new BotError(`chooseMove returned ${String(choice)}, which has no UCI form`);
    }
    return protocol.move(uci, info);
  }

  #playOwn(board: Board, choice: Move): void {
    try {
      board.makeMove(choice);
    } catch (error) {
      if (!(error instanceof ChessError)) {
        throw error;
      }
      Log.warn(`own move ${choice.uci()} is not legal in this position; the referee decides`);
    }
  }

  async #end(gameOver: Message): Promise<void> {
    const result = protocol.gameResult(gameOver);
    this.result = result;
    await guarded("onGameEnd", () => this.#bot.onGameEnd(result));
  }
}

function readFen(message: string, fen: string): Board {
  try {
    return Board.fromFen(fen);
  } catch (error) {
    if (error instanceof ChessError) {
      throw new ProtocolError(`${message}: ${error.message}`);
    }
    throw error;
  }
}
