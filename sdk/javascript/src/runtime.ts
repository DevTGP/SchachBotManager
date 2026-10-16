// run: the entry point of every bot (spec/api/runtime.json).
import { closeSync, openSync } from "node:fs";

import { Bot } from "./bot.ts";
import type { Channel } from "./channel.ts";
import { openStdio, openTcp, ProtocolError } from "./channel.ts";
import { BotError, describe, Game, guarded } from "./game.ts";
import { configure, Log } from "./log.ts";
import type { Options } from "./options.ts";
import { OptionsError, parseOptions } from "./options.ts";

export type BotClass = new () => Bot;

export interface RunOptions {
  /** true shows the game in the viewer window (E106); not part of this SDK yet (E205). */
  readonly viewer?: boolean;
}

function fail(message: string): never {
  process.stderr.write(`sbm: ${message}\n`);
  process.exit(1);
}

async function open(options: Options): Promise<Channel> {
  return options.transport === "tcp" ? openTcp(options.port) : openStdio();
}

async function play(bot: BotClass, options: Options): Promise<void> {
  if (options.transport === "remote") {
    Log.error("this SDK cannot play remote games yet; use the Python SDK for --remote");
    process.exit(1);
  }
  let channel: Channel;
  try {
    channel = await open(options);
  } catch (error) {
    Log.error(
      `cannot connect to the arena on 127.0.0.1:${options.port}: ${(error as Error).message}`,
    );
    process.exit(1);
  }
  try {
    const instance = await guarded(`new ${bot.name}()`, () => new bot());
    await new Game(instance, channel).play();
  } catch (error) {
    if (error instanceof BotError) {
      Log.error(describe(error));
    } else if (error instanceof ProtocolError) {
      Log.error(`protocol error: ${error.message}`);
    } else {
      throw error;
    }
    channel.close();
    process.exit(1);
  }
  channel.close();
}

function showViewer(): void {
  // The sandbox on the server sets SBM_NO_VIEWER; only a local run hears about the window.
  if (!process.env.SBM_NO_VIEWER) {
    Log.warn("this SDK has no viewer program yet; the game runs without a window");
  }
}

/**
 * Creates one instance of the bot class and plays one game with it.
 *
 * Transport and log level come from the command line or environment (E61): --tcp [PORT],
 * --log-level LEVEL, --log-file PATH or SBM_TRANSPORT, SBM_PORT, SBM_LOG_LEVEL, SBM_LOG_FILE.
 * An exception from the bot is logged at ERROR and ends the process with exit code 1 (E49).
 */
export async function run(bot: BotClass, options: RunOptions = {}): Promise<void> {
  if (typeof bot !== "function" || !(bot.prototype instanceof Bot)) {
    throw new TypeError(`run: bot must be a class that extends Bot, not ${String(bot)}`);
  }
  if (typeof bot.prototype.chooseMove !== "function") {
    throw new TypeError(`run: ${bot.name} has no method chooseMove`);
  }
  const viewer = options.viewer ?? false;
  if (typeof viewer !== "boolean") {
    throw new TypeError(`run: viewer must be true or false, not ${String(viewer)}`);
  }
  let parsed: Options;
  try {
    parsed = parseOptions(process.argv.slice(2), process.env);
  } catch (error) {
    if (error instanceof OptionsError) {
      fail(error.message);
    }
    throw error;
  }
  let file: number | undefined;
  if (parsed.logFile !== undefined) {
    try {
      file = openSync(parsed.logFile, "a");
    } catch (error) {
      fail(`cannot open the log file: ${(error as Error).message}`);
    }
  }
  configure(parsed.logLevel, file);
  if (viewer) {
    showViewer();
  }
  try {
    await play(bot, parsed);
  } finally {
    configure(Log.level(), undefined);
    if (file !== undefined) {
      closeSync(file);
    }
  }
}
