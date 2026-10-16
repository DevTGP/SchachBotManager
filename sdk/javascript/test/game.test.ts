// One game against a scripted referee: init, turns, game_over and the bot's answers.
import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";

import { ProtocolError } from "../src/channel.ts";
import { BotError } from "../src/game.ts";
import { Board, Bot, Clock, Log, Move, NULL_MOVE, RESIGN, version, WHITE } from "../src/index.ts";
import type { GameInfo, GameResult } from "../src/index.ts";
import { gameInfo, gameResult, PROTOCOL_VERSION, supportedVersions } from "../src/protocol.ts";
import { captureLog } from "./capture.ts";
import { play, turn } from "./referee.ts";
import { example, load, SPEC } from "./spec.ts";

const lines = captureLog();
const START = example("turn.first_move").fen as string;
const INIT = example("init.standard");
const GAME_OVER = example("game_over.checkmate");
const BLACK_INIT = { ...INIT, color: "black" };

type Call = ["start", GameInfo] | ["turn", string, Clock] | ["end", GameResult];

/** Plays the first legal move and records what the SDK passes in. */
class FirstMove extends Bot {
  calls: Call[] = [];

  override onGameStart(info: GameInfo): void | Promise<void> {
    this.calls.push(["start", info]);
  }

  chooseMove(board: Board, clock: Clock): Move | Promise<Move> {
    this.calls.push(["turn", board.fen(), clock]);
    return board.legalMoves()[0];
  }

  override onGameEnd(result: GameResult): void | Promise<void> {
    this.calls.push(["end", result]);
  }
}

function log(): string {
  return lines.join("");
}

test("white game", async () => {
  const bot = new FirstMove();
  const answers = await play(bot, INIT, example("turn.first_move"), GAME_OVER);
  assert.deepEqual(answers, [
    { type: "ready", v: 1, sdk: version, lang: "javascript" },
    { type: "move", v: 1, move: new Board().legalMoves()[0].uci() },
  ]);
  const [start, move, end] = bot.calls;
  assert.deepEqual(start, [
    "start",
    {
      gameId: "66f1c2a9e4b0a1b2c3d4e5f6",
      color: WHITE,
      opponentName: "Stockfisch Junior",
      startFen: START,
      initialTimeMs: 300000,
      incrementMs: 2000,
      startupMs: 10000,
      memoryLimitMib: 1024,
      discipline: "Blitz 5+2",
    },
  ]);
  assert.ok(Object.isFrozen(start[1]));
  assert.equal(move[0], "turn");
  assert.equal(move[1], START);
  const clock = move[2] as Clock;
  assert.equal(clock.remainingMs(), 300000);
  assert.equal(clock.opponentRemainingMs(), 300000);
  assert.equal(clock.incrementMs(), 2000);
  assert.deepEqual(end, ["end", { result: "0-1", termination: "checkmate" }]);
  assert.equal(log(), "");
});

test("black follows the opponent's moves", async () => {
  const bot = new FirstMove();
  const promotion = example("turn.after_promotion");
  const king = Board.fromFen(promotion.fen as string);
  king.makeMove(king.legalMoves()[0]);
  const after = king.copy();
  const reply = after.legalMoves().at(-1) as Move;
  after.makeMove(reply);
  const later = turn(after.fen(), 121, reply.uci());
  const black = example("init.black_custom_position");
  const answers = await play(bot, black, promotion, later, GAME_OVER);
  assert.deepEqual(
    answers.map((answer) => answer.type),
    ["ready", "move", "move"],
  );
  assert.equal(bot.calls[1][1], promotion.fen);
  assert.equal(bot.calls[2][1], after.fen());
  assert.equal(log(), "");
});

test("an en passant square without capture is no mismatch", async () => {
  await play(new FirstMove(), BLACK_INIT, example("turn.after_opponent_move"), GAME_OVER);
  assert.equal(log(), "");
});

test("a mismatch adopts the referee's position", async () => {
  const bot = new FirstMove();
  const other = "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1";
  await play(bot, BLACK_INIT, turn(other, 1, "e2e4"), GAME_OVER);
  assert.equal(bot.calls[1][1], other);
  assert.match(log(), /WARN {2}own position differs/);
});

test("an unusable last move is repaired by the FEN", async () => {
  const fen = example("turn.after_opponent_move").fen as string;
  for (const lastMove of ["e2e5", 7 as unknown as string]) {
    lines.length = 0;
    await play(new FirstMove(), BLACK_INIT, turn(fen, 1, lastMove), GAME_OVER);
    assert.match(log(), /WARN {2}own position differs/);
  }
});

test("changes of the bot to its board stay local", async () => {
  class Mutating extends FirstMove {
    override chooseMove(board: Board, clock: Clock): Move {
      const move = super.chooseMove(board, clock) as Move;
      board.makeMove(board.legalMoves()[0]);
      board.makeMove(board.legalMoves()[0]);
      return move;
    }
  }
  const bot = new Mutating();
  const first = new Board();
  first.makeMove(first.legalMoves()[0]);
  const reply = first.legalMoves()[0];
  first.makeMove(reply);
  await play(bot, INIT, turn(START, 0), turn(first.fen(), 2, reply.uci()), GAME_OVER);
  assert.equal(bot.calls[2][1], first.fen());
  assert.equal(log(), "");
});

test("asynchronous callbacks are awaited", async () => {
  const pause = (): Promise<void> => new Promise((resolve) => setTimeout(resolve, 5));
  class Slow extends FirstMove {
    override async onGameStart(info: GameInfo): Promise<void> {
      await pause();
      await super.onGameStart(info);
    }

    override async chooseMove(board: Board, clock: Clock): Promise<Move> {
      await pause();
      return super.chooseMove(board, clock);
    }

    override async onGameEnd(result: GameResult): Promise<void> {
      await pause();
      await super.onGameEnd(result);
    }
  }
  const bot = new Slow();
  const answers = await play(bot, INIT, turn(START, 0), GAME_OVER);
  assert.equal(answers[1].type, "move");
  assert.deepEqual(
    bot.calls.map((call) => call[0]),
    ["start", "turn", "end"],
  );
});

test("resign", async () => {
  class Resigning extends FirstMove {
    override chooseMove(): Move {
      return RESIGN;
    }
  }
  const answers = await play(new Resigning(), INIT, turn(START, 0), GAME_OVER);
  assert.deepEqual(answers[1], { type: "resign", v: 1 });
});

test("a report belongs to one turn", async () => {
  class Reporting extends FirstMove {
    override chooseMove(board: Board, clock: Clock): Move | Promise<Move> {
      if (board.fullmoveNumber() === 1) {
        this.report({ depth: 3, text: "first" });
      }
      return super.chooseMove(board, clock);
    }
  }
  const second = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 2";
  const answers = await play(new Reporting(), INIT, turn(START, 0), turn(second, 2), GAME_OVER);
  assert.deepEqual(answers[1].info, { depth: 3, text: "first" });
  assert.ok(!("info" in answers[2]));
});

test("a report keeps its values when the object changes later", async () => {
  class Reusing extends FirstMove {
    override chooseMove(board: Board, clock: Clock): Move | Promise<Move> {
      const info = { depth: 3 };
      this.report(info);
      info.depth = 99;
      return super.chooseMove(board, clock);
    }
  }
  const answers = await play(new Reusing(), INIT, turn(START, 0), GAME_OVER);
  assert.deepEqual(answers[1].info, { depth: 3 });
});

test("a report before the turn is dropped", async () => {
  class Early extends FirstMove {
    override onGameStart(): void {
      this.report({ depth: 1 });
    }
  }
  const answers = await play(new Early(), INIT, turn(START, 0), GAME_OVER);
  assert.ok(!("info" in answers[1]));
});

test("report needs an object", () => {
  for (const value of [undefined, null, 3, "depth", []]) {
    assert.throws(() => new FirstMove().report(value as never), TypeError);
  }
});

const UNUSABLE: [string, unknown, RegExp][] = [
  ["undefined", undefined, /returned undefined, not a Move/],
  ["null", null, /returned null, not a Move/],
  ["a string", "e2e4", /returned string, not a Move/],
  ["a lookalike", { uci: () => "e2e4" }, /returned Object, not a Move/],
  ["NULL_MOVE", NULL_MOVE, /no UCI form/],
];

for (const [name, answer, message] of UNUSABLE) {
  test(`an unusable answer: ${name}`, async () => {
    class Wrong extends FirstMove {
      override chooseMove(): Move {
        return answer as Move;
      }
    }
    await assert.rejects(play(new Wrong(), INIT, turn(START, 0), GAME_OVER), (error) => {
      assert.ok(error instanceof BotError);
      assert.match(error.message, message);
      return true;
    });
  });
}

for (const callback of ["onGameStart", "chooseMove", "onGameEnd"] as const) {
  for (const asynchronous of [false, true]) {
    test(`an exception in ${callback}${asynchronous ? " (async)" : ""}`, async () => {
      const bot = new FirstMove();
      const boom = new RangeError("boom");
      (bot as unknown as Record<string, () => unknown>)[callback] = asynchronous
        ? () => Promise.reject(boom)
        : () => {
            throw boom;
          };
      await assert.rejects(play(bot, INIT, turn(START, 0), GAME_OVER), (error) => {
        assert.ok(error instanceof BotError);
        assert.equal(error.message, `${callback} threw RangeError: boom`);
        assert.equal(error.cause, boom);
        return true;
      });
    });
  }
}

test("a thrown value that is no Error", async () => {
  const bot = new FirstMove();
  bot.chooseMove = () => {
    throw "text";
  };
  await assert.rejects(play(bot, INIT, turn(START, 0), GAME_OVER), /chooseMove threw string/);
});

test("an illegal own move is left to the referee", async () => {
  class Illegal extends FirstMove {
    override chooseMove(): Move {
      return Move.parse("e2e5");
    }
  }
  const answers = await play(new Illegal(), INIT, turn(START, 0), GAME_OVER);
  assert.equal(answers[1].move, "e2e5");
  assert.match(log(), /WARN {2}own move e2e5 is not legal/);
});

test("unknown types and fields are ignored", async () => {
  const init = { ...INIT, future_field: { x: 1 } };
  const answers = await play(
    new FirstMove(),
    init,
    { type: "ping" },
    { ...turn(START, 0), hint: "e2e4" },
    GAME_OVER,
  );
  assert.deepEqual(
    answers.map((answer) => answer.type),
    ["ready", "move"],
  );
  assert.match(log(), /WARN {2}ignoring a message of unknown type "ping"/);
});

test("referee errors are logged", async () => {
  await play(new FirstMove(), INIT, example("error.illegal_move"), GAME_OVER);
  assert.match(log(), /ERROR referee reports illegal_move: e1g1: castling through check/);
});

test("an unsupported version still answers ready", async () => {
  const answers = await play(new FirstMove(), { ...INIT, supported: [2] }, GAME_OVER);
  assert.equal(answers[0].type, "ready");
  assert.match(log(), /ERROR the referee supports protocol versions \[2\]/);
});

test("end of input before game_over", async () => {
  await play(new FirstMove(), INIT, turn(START, 0));
  assert.match(log(), /WARN {2}input ended before game_over/);
});

test("the ply appears in log lines", async () => {
  class Logging extends FirstMove {
    override chooseMove(board: Board, clock: Clock): Move | Promise<Move> {
      Log.info("thinking");
      return super.chooseMove(board, clock);
    }
  }
  await play(new Logging(), INIT, turn(START, 0), GAME_OVER);
  assert.match(log(), /\[ply 0\] INFO {2}thinking/);
});

const PROTOCOL_ERRORS: [string, Record<string, unknown>[]][] = [
  ["turn before init", [turn(START, 0)]],
  ["second init", [INIT, INIT]],
  ["unknown color", [{ ...INIT, color: "red" }]],
  ["invalid FEN", [{ ...INIT, start_fen: "no fen" }]],
  ["increment not an integer", [{ ...INIT, increment_ms: true }]],
  ["supported not a list", [{ ...INIT, supported: 1 }]],
  ["invalid turn FEN", [INIT, { ...turn(START, 0), fen: "8/8/8/8/8/8/8/8 w - - 0 1" }]],
  ["time as text", [INIT, { ...turn(START, 0), remaining_ms: "1000" }]],
  ["time as fraction", [INIT, { ...turn(START, 0), remaining_ms: 1.5 }]],
  ["incomplete game_over", [INIT, { type: "game_over", result: "1-0" }]],
];

for (const [name, messages] of PROTOCOL_ERRORS) {
  test(`protocol error: ${name}`, async () => {
    await assert.rejects(play(new FirstMove(), ...messages), ProtocolError);
  });
}

function examples(prefix: string): Record<string, unknown>[] {
  const directory = path.join(SPEC, "protocol", "v1", "examples", "valid");
  return readdirSync(directory)
    .filter((name) => name.startsWith(`${prefix}.`))
    .map((name) => load<Record<string, unknown>>(path.join(directory, name)));
}

test("all init examples are read", () => {
  const all = examples("init");
  assert.ok(all.length >= 2);
  for (const init of all) {
    assert.equal(gameInfo(init).startFen, init.start_fen);
    assert.ok(supportedVersions(init).includes(PROTOCOL_VERSION));
  }
});

test("all game_over examples are read", () => {
  const all = examples("game_over");
  assert.ok(all.length >= 2);
  for (const gameOver of all) {
    const result = gameResult(gameOver);
    assert.deepEqual([result.result, result.termination], [gameOver.result, gameOver.termination]);
  }
});
