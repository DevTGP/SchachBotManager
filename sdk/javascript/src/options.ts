// Start options of run from the command line and the environment (E61); arguments win.
import type { LogLevel } from "./constants.ts";
import { INFO } from "./constants.ts";
import { LEVEL_NAMES } from "./log.ts";

export const DEFAULT_PORT = 7470;
const TRANSPORTS = ["stdio", "tcp", "remote"] as const;
// The SDK reads these and their values; every other argument belongs to the bot.
const VALUE_OPTIONS = [
  "--log-level",
  "--log-file",
  "--remote",
  "--token",
  "--opponent",
  "--color",
  "--discipline",
  "--time",
];

export type Transport = (typeof TRANSPORTS)[number];

/** An argument or environment variable has an invalid value. */
export class OptionsError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "OptionsError";
  }
}

export interface Options {
  readonly transport: Transport;
  readonly port: number;
  readonly logLevel: LogLevel;
  readonly logFile: string | undefined;
}

function port(text: string): number {
  if (!/^\d+$/.test(text) || Number(text) < 1 || Number(text) > 65535) {
    throw new OptionsError(`invalid port ${JSON.stringify(text)}, expected 1 to 65535`);
  }
  return Number(text);
}

function level(text: string): LogLevel {
  const index = (LEVEL_NAMES as readonly string[]).indexOf(text.toUpperCase());
  if (index < 0) {
    throw new OptionsError(
      `invalid log level ${JSON.stringify(text)}, expected one of ${LEVEL_NAMES.join(", ")}`,
    );
  }
  return index as LogLevel;
}

// An argument the way argparse reads it: options start with -, negative numbers do not.
function isOption(argument: string): boolean {
  return argument.startsWith("-") && !/^-(\d+|\d*\.\d+)$/.test(argument);
}

/** The SDK's arguments with their values; --tcp without a value gives "". */
function readArguments(argv: readonly string[]): Map<string, string> {
  const found = new Map<string, string>();
  for (let i = 0; i < argv.length; i += 1) {
    const argument = argv[i];
    if (argument === "--") {
      break;
    }
    const equals = argument.indexOf("=");
    const name = argument.startsWith("--") && equals > 0 ? argument.slice(0, equals) : argument;
    const inline = name === argument ? undefined : argument.slice(equals + 1);
    if (name === "--tcp") {
      const next = argv[i + 1];
      if (inline !== undefined) {
        found.set(name, inline);
      } else if (next !== undefined && !isOption(next)) {
        found.set(name, next);
        i += 1;
      } else {
        found.set(name, "");
      }
    } else if (VALUE_OPTIONS.includes(name)) {
      const next = argv[i + 1];
      if (inline !== undefined) {
        found.set(name, inline);
      } else if (next !== undefined && !isOption(next)) {
        found.set(name, next);
        i += 1;
      } else {
        throw new OptionsError(`argument ${name}: expected one argument`);
      }
    }
  }
  return found;
}

function fromEnvironment(environment: NodeJS.ProcessEnv): Options {
  const transport = (environment.SBM_TRANSPORT ?? "stdio").toLowerCase();
  if (!(TRANSPORTS as readonly string[]).includes(transport)) {
    throw new OptionsError(
      `invalid SBM_TRANSPORT ${JSON.stringify(transport)}, expected stdio or tcp`,
    );
  }
  const portText = environment.SBM_PORT;
  const levelText = environment.SBM_LOG_LEVEL;
  return {
    transport: transport as Transport,
    port: portText === undefined ? DEFAULT_PORT : port(portText),
    logLevel: levelText === undefined ? INFO : level(levelText),
    logFile: environment.SBM_LOG_FILE || undefined,
  };
}

/** Options for run from the arguments after the program name and the environment. */
export function parseOptions(argv: readonly string[], environment: NodeJS.ProcessEnv): Options {
  let options = fromEnvironment(environment);
  const found = readArguments(argv);
  const tcp = found.get("--tcp");
  if (tcp !== undefined) {
    options = { ...options, transport: "tcp", port: tcp ? port(tcp) : options.port };
  }
  const levelText = found.get("--log-level");
  if (levelText !== undefined) {
    options = { ...options, logLevel: level(levelText) };
  }
  const logFile = found.get("--log-file");
  if (logFile !== undefined) {
    options = { ...options, logFile: logFile || undefined };
  }
  if (found.has("--remote")) {
    options = { ...options, transport: "remote" };
  }
  return options;
}
