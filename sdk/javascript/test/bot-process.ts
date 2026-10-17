// A bot in its own Node process, written for one test: source, start and answers.
import { spawn } from "node:child_process";
import { writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import type { Message } from "../src/channel.ts";
import { example } from "./spec.ts";

const SDK = pathToFileURL(
  path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "src", "index.ts"),
).href;

export const MESSAGES = [
  example("init.standard"),
  example("turn.first_move"),
  example("game_over.checkmate"),
];
export const REFEREE_INPUT = MESSAGES.map((message) => `${JSON.stringify(message)}\n`).join("");

export interface BotCode {
  /** Body of onGameStart(info). */
  readonly start?: string;
  /** Body of chooseMove(board, clock) before it returns the first legal move. */
  readonly turn?: string;
  /** The call that starts the bot. */
  readonly run?: string;
}

/** Writes my_bot.mjs into the directory and returns its path. */
export function writeBot(directory: string, code: BotCode = {}): string {
  const file = path.join(directory, "my_bot.mjs");
  const source = `import * as sbm from ${JSON.stringify(SDK)};

class TestBot extends sbm.Bot {
  onGameStart(info) {
    ${code.start ?? ""}
  }

  chooseMove(board, clock) {
    ${code.turn ?? ""}
    return board.legalMoves()[0];
  }
}

${code.run ?? "await sbm.run(TestBot);"}
`;
  writeFileSync(file, source, "utf-8");
  return file;
}

export interface Finished {
  readonly code: number | null;
  readonly stdout: string;
  readonly stderr: string;
}

/** The environment without SBM_ variables, plus the given ones. */
function environment(variables: Record<string, string>): NodeJS.ProcessEnv {
  const clean = Object.fromEntries(
    Object.entries(process.env).filter(([key]) => !key.startsWith("SBM_")),
  );
  return { ...clean, ...variables };
}

/** Runs the bot with arguments, input on stdin and extra environment variables. */
export function runBot(
  file: string,
  argv: readonly string[] = [],
  input: string = REFEREE_INPUT,
  variables: Record<string, string> = {},
): Promise<Finished> {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, ["--no-warnings", file, ...argv], {
      cwd: path.dirname(path.dirname(file)),
      env: environment(variables),
      timeout: 60_000,
    });
    const stdout: Buffer[] = [];
    const stderr: Buffer[] = [];
    child.stdout.on("data", (chunk: Buffer) => stdout.push(chunk));
    child.stderr.on("data", (chunk: Buffer) => stderr.push(chunk));
    child.on("error", reject);
    child.on("close", (code) =>
      resolve({
        code,
        stdout: Buffer.concat(stdout).toString("utf-8"),
        stderr: Buffer.concat(stderr).toString("utf-8"),
      }),
    );
    child.stdin.on("error", () => undefined);
    child.stdin.end(input);
  });
}

/** The bot's messages on stdout. */
export function answers(stdout: string): Message[] {
  return stdout
    .split("\n")
    .filter((line) => line !== "")
    .map((line) => JSON.parse(line) as Message);
}
