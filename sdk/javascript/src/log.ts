// Log (spec/api/log.json): the debug log of the bot, written to stderr. Each line carries time,
// ply and level: "14:03:27.512 [ply 12] INFO  message". The SDK sets the start level and an
// optional file from the command line or environment (E61) and the ply from each turn.
import { writeSync } from "node:fs";

import type { LogLevel } from "./constants.ts";
import { DEBUG, ERROR, INFO, OFF, TRACE, WARN } from "./constants.ts";
import { InvalidArgumentError } from "./errors.ts";

export const LEVEL_NAMES = ["TRACE", "DEBUG", "INFO", "WARN", "ERROR", "OFF"] as const;

const STDERR = 2;

const toStderr = (line: string): void => {
  // Synchronous, so lines keep their order and none is lost when the process ends.
  writeSync(STDERR, line);
};

const state: {
  level: LogLevel;
  ply: number | undefined;
  file: number | undefined;
  output: (line: string) => void;
} = { level: INFO, ply: undefined, file: undefined, output: toStderr };

function checkLevel(function_: string, level: unknown): LogLevel {
  if (typeof level !== "number") {
    throw new TypeError(`Log.${function_}: level must be a number, not ${typeof level}`);
  }
  if (!Number.isInteger(level) || level < TRACE || level > OFF) {
    throw new InvalidArgumentError(`Log.${function_}: unknown level ${level}`);
  }
  return level;
}

function pad(value: number, width: number): string {
  return String(value).padStart(width, "0");
}

function timeOfDay(now: Date): string {
  return (
    `${pad(now.getHours(), 2)}:${pad(now.getMinutes(), 2)}:${pad(now.getSeconds(), 2)}.` +
    pad(now.getMilliseconds(), 3)
  );
}

function write(level: LogLevel, message: unknown): void {
  if (level < state.level) {
    return;
  }
  const ply = state.ply === undefined ? "-" : String(state.ply);
  const line = `${timeOfDay(new Date())} [ply ${ply}] ${LEVEL_NAMES[level].padEnd(5)} ${String(message)}\n`;
  state.output(line);
  if (state.file !== undefined) {
    writeSync(state.file, line);
  }
}

/** Debug log with the levels TRACE < DEBUG < INFO < WARN < ERROR < OFF; static only. */
export class Log {
  private constructor() {
    throw new TypeError("Log has only static functions");
  }

  /** Writes at level TRACE. */
  static trace(message: string): void {
    write(TRACE, message);
  }

  /** Writes at level DEBUG. */
  static debug(message: string): void {
    write(DEBUG, message);
  }

  /** Writes at level INFO. */
  static info(message: string): void {
    write(INFO, message);
  }

  /** Writes at level WARN. */
  static warn(message: string): void {
    write(WARN, message);
  }

  /** Writes at level ERROR. */
  static error(message: string): void {
    write(ERROR, message);
  }

  /** Sets the minimum level written; OFF writes nothing. */
  static setLevel(level: LogLevel): void {
    state.level = checkLevel("setLevel", level);
  }

  /** Current minimum level; INFO unless the command line or environment says otherwise. */
  static level(): LogLevel {
    return state.level;
  }

  /** Whether a message at that level would be written. */
  static isEnabled(level: LogLevel): boolean {
    const checked = checkLevel("isEnabled", level);
    return state.level <= checked && checked < OFF;
  }
}

/** Start level and optional log file (a file descriptor), set by run before the game. */
export function configure(level: LogLevel, file: number | undefined): void {
  state.level = level;
  state.file = file;
}

/** Ply shown in each line from the current turn on. */
export function setPly(ply: number | undefined): void {
  state.ply = ply;
}

/** Where lines go instead of stderr, for tests; undefined restores stderr. */
export function setOutput(output: ((line: string) => void) | undefined): void {
  state.output = output ?? toStderr;
}
