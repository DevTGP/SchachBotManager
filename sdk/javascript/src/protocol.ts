// Messages of protocol version 1 (spec/protocol/v1/); unknown referee fields are ignored (E36).
import type { Message } from "./channel.ts";
import { ProtocolError } from "./channel.ts";
import { BLACK, WHITE } from "./constants.ts";
import { infoFields } from "./info.ts";
import type { GameInfo, GameResult, Info } from "./records.ts";

export const PROTOCOL_VERSION = 1;
export const LANGUAGE = "javascript";
const COLORS = new Map([
  ["white", WHITE],
  ["black", BLACK],
]);

type Kind = "string" | "integer" | "array";

const CHECKS: Record<Kind, (value: unknown) => boolean> = {
  string: (value) => typeof value === "string",
  integer: (value) => Number.isInteger(value),
  array: (value) => Array.isArray(value),
};

/** A required field of a referee message with its JSON type. */
export function field(message: Message, name: string, kind: "string"): string;
export function field(message: Message, name: string, kind: "integer"): number;
export function field(message: Message, name: string, kind: "array"): unknown[];
export function field(message: Message, name: string, kind: Kind): unknown {
  const value = message[name];
  if (!CHECKS[kind](value)) {
    throw new ProtocolError(`${String(message.type)}: field "${name}" missing or not ${kind}`);
  }
  return value;
}

export function gameInfo(init: Message): GameInfo {
  const color = COLORS.get(field(init, "color", "string"));
  if (color === undefined) {
    throw new ProtocolError(`init: unknown color ${JSON.stringify(init.color)}`);
  }
  return Object.freeze({
    gameId: field(init, "game_id", "string"),
    color,
    opponentName: field(init, "opponent_name", "string"),
    startFen: field(init, "start_fen", "string"),
    initialTimeMs: field(init, "initial_time_ms", "integer"),
    incrementMs: field(init, "increment_ms", "integer"),
    startupMs: field(init, "startup_ms", "integer"),
    memoryLimitMib: field(init, "memory_limit_mib", "integer"),
    discipline: field(init, "discipline", "string"),
  });
}

export function supportedVersions(init: Message): unknown[] {
  return field(init, "supported", "array");
}

export function gameResult(gameOver: Message): GameResult {
  return Object.freeze({
    result: field(gameOver, "result", "string"),
    termination: field(gameOver, "termination", "string"),
  });
}

export function ready(sdkVersion: string): Message {
  return { type: "ready", v: PROTOCOL_VERSION, sdk: sdkVersion, lang: LANGUAGE };
}

export function resign(): Message {
  return { type: "resign", v: PROTOCOL_VERSION };
}

export function move(uci: string, info: Info | undefined): Message {
  const message: Message = { type: "move", v: PROTOCOL_VERSION, move: uci };
  if (info !== undefined) {
    message.info = infoFields(info);
  }
  return message;
}
