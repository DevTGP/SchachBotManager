// The JavaScript template project under templates/javascript.
//
// bot.js imports the published package "schachbotmanager"; the tests use a copy that imports
// this SDK from src/ instead, so they run without npm install.
import assert from "node:assert/strict";
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { after, before, test } from "node:test";
import { pathToFileURL } from "node:url";

import { Board, Bot, Clock, WHITE } from "../src/index.ts";
import type { Board as BoardType, GameInfo, Move } from "../src/index.ts";
import { takeReport } from "../src/bot.ts";
import { DATA_DIR_VARIABLE } from "../src/data.ts";
import { arenaMissing, playInArena, REGULAR } from "./arena-command.ts";
import { answers, runBot } from "./bot-process.ts";
import { load, ROOT } from "./spec.ts";

const TEMPLATE = path.join(ROOT, "templates", "javascript");
const SDK = pathToFileURL(path.join(ROOT, "sdk", "javascript", "src", "index.ts")).href;
const CLOCK = new Clock(60_000, 60_000, 0);
// Values for the ${input:…} prompts of tasks.json.
const INPUTS: Record<string, string> = { "${input:replayGame}": "1", "${input:replayPly}": "10" };

interface TemplateModule {
  TemplateBot: new () => Bot & { onGameStart(info: GameInfo): void };
  loadBook(): Map<string, string[]>;
  positionKey(board: BoardType): string;
}

interface Task {
  label: string;
  command: string;
  args: string[];
  isBackground?: boolean;
  problemMatcher: { background?: { endsPattern: string } } | [];
}

interface Configuration {
  type: string;
  program: string;
  args?: string[];
  preLaunchTask?: string;
}

let directory = "";
let copy = "";
let template: TemplateModule;
let saved: string | undefined;

before(async () => {
  directory = mkdtempSync(path.join(tmpdir(), "sbm-template-"));
  copy = path.join(directory, "bot", "bot.js");
  mkdirSync(path.join(directory, "bot", "data"), { recursive: true });
  const source = readFileSync(path.join(TEMPLATE, "bot.js"), "utf-8");
  assert.ok(source.includes('from "schachbotmanager";'));
  writeFileSync(copy, source.replace('from "schachbotmanager";', `from ${JSON.stringify(SDK)};`));
  copyFileSync(
    path.join(TEMPLATE, "data", "book.txt"),
    path.join(directory, "bot", "data", "book.txt"),
  );
  saved = process.env[DATA_DIR_VARIABLE];
  process.env[DATA_DIR_VARIABLE] = path.join(TEMPLATE, "data");
  template = (await import(pathToFileURL(copy).href)) as TemplateModule;
});

after(() => {
  if (saved === undefined) {
    delete process.env[DATA_DIR_VARIABLE];
  } else {
    process.env[DATA_DIR_VARIABLE] = saved;
  }
  rmSync(directory, { recursive: true, force: true });
});

function startedBot(): Bot {
  const bot = new template.TemplateBot();
  bot.onGameStart({
    gameId: "g",
    color: WHITE,
    opponentName: "opp",
    startFen: new Board().fen(),
    initialTimeMs: 60_000,
    incrementMs: 0,
    startupMs: 10_000,
    memoryLimitMib: 256,
    discipline: "test",
  });
  return bot;
}

function uci(move: Move | Promise<Move>): string {
  assert.ok(!(move instanceof Promise));
  return move.uci();
}

function vscode<T>(name: string): T {
  return load<T>(path.join(TEMPLATE, ".vscode", name));
}

test("the book holds legal moves", () => {
  const book = template.loadBook();
  assert.ok(book.size >= 8);
  for (const [position, moves] of book) {
    const board = Board.fromFen(`${position} 0 1`);
    assert.equal(template.positionKey(board), position);
    assert.ok(moves.length > 0);
    for (const move of moves) {
      assert.ok(board.isLegal(board.parseMove(move)), `${move} in ${position}`);
    }
  }
});

test("plays from the book", () => {
  const bot = startedBot();
  assert.ok(["e2e4", "d2d4", "g1f3", "c2c4"].includes(uci(bot.chooseMove(new Board(), CLOCK))));
  assert.equal(takeReport(bot)?.text, "book");
});

test("takes a hanging queen but not a defended pawn", () => {
  const bot = startedBot();
  const hanging = Board.fromFen("4k3/8/8/3q4/8/8/8/3RK3 w - - 0 1");
  assert.equal(uci(bot.chooseMove(hanging, CLOCK)), "d1d5");
  assert.equal(takeReport(bot)?.scoreCp, 900);
  const defended = Board.fromFen("4k3/8/2p5/3p4/8/8/8/3QK3 w - - 0 1");
  for (let i = 0; i < 10; i += 1) {
    assert.notEqual(uci(bot.chooseMove(defended, CLOCK)), "d1d5");
  }
});

test("runs as a script and finds data/ next to bot.js", async () => {
  // runBot starts the bot outside its folder and without SBM_DATA_DIR.
  const finished = await runBot(copy);
  assert.equal(finished.code, 0, finished.stderr);
  assert.deepEqual(
    answers(finished.stdout).map((message) => message.type),
    ["ready", "move"],
  );
  assert.match(finished.stderr, /INFO {2}playing White against /);
});

test("does not start a game when imported", async () => {
  const importer = path.join(directory, "bot", "import.mjs");
  writeFileSync(
    importer,
    'import { TemplateBot } from "./bot.js";\nconsole.error(TemplateBot.name);\n',
  );
  const finished = await runBot(importer, [], "");
  assert.equal(finished.code, 0, finished.stderr);
  assert.equal(finished.stdout, "");
  assert.equal(finished.stderr.trim(), "TemplateBot");
});

test("package.json takes the SDK from npm", () => {
  const manifest = load<{ type: string; dependencies: Record<string, string> }>(
    path.join(TEMPLATE, "package.json"),
  );
  assert.equal(manifest.type, "module");
  assert.ok(manifest.dependencies.schachbotmanager);
  assert.deepEqual(Object.keys(manifest.dependencies), ["schachbotmanager"]);
});

test("the tasks start the arena", () => {
  const tasks = vscode<{ tasks: Task[] }>("tasks.json").tasks;
  assert.ok(tasks.length >= 5);
  for (const task of tasks) {
    assert.equal(task.command, "sbm-arena");
    const args = task.args.map((arg) => INPUTS[arg] ?? arg);
    assert.ok(!args.some((arg) => arg.includes("${")), task.label);
    const bots = args.filter((arg) => ["tcp", "bot.js", "material"].includes(arg));
    assert.equal(bots.length, 2, task.label);
    if (task.isBackground) {
      assert.ok(args.includes("tcp") && args.includes("--no-clock"), task.label);
      assert.ok(!Array.isArray(task.problemMatcher));
      assert.equal(task.problemMatcher.background?.endsPattern, "waiting for .* to connect");
    } else {
      assert.ok(args.includes("bot.js"), task.label);
    }
  }
});

test("launch starts the bot after its task", () => {
  const labels = new Set(vscode<{ tasks: Task[] }>("tasks.json").tasks.map((task) => task.label));
  const configurations = vscode<{ configurations: Configuration[] }>("launch.json").configurations;
  assert.equal(configurations.length, 5);
  for (const configuration of configurations) {
    assert.equal(configuration.type, "node");
    assert.equal(configuration.program, "${workspaceFolder}/bot.js");
    assert.deepEqual(configuration.args, ["--tcp"]);
    if (configuration.preLaunchTask !== undefined) {
      assert.ok(labels.has(configuration.preLaunchTask), configuration.preLaunchTask);
    }
  }
  assert.equal(configurations.filter((entry) => entry.preLaunchTask === undefined).length, 1);
});

test("plays a game against material in the arena", { skip: arenaMissing }, () => {
  const args = ["bot.js", "material", "--games", "2", "--time", "10+0", "--max-moves", "40"];
  const terminations = playInArena(args, path.dirname(copy));
  assert.equal(terminations.length, 2);
  for (const termination of terminations) {
    assert.ok(REGULAR.includes(termination), termination);
  }
});
