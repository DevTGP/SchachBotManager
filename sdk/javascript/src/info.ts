// Info as the info object of a move message, within the limits of the protocol (E43, E63).
//
// A field outside its limits would make the referee score a protocol violation, although info
// is display only. The SDK therefore truncates pv and text and leaves out other invalid fields
// with a warning.
import { ChessError } from "./errors.ts";
import { Log } from "./log.ts";
import { Move } from "./move.ts";
import type { Info } from "./records.ts";

export const MAX_PV_MOVES = 32;
export const MAX_TEXT_LENGTH = 256;

// Field of Info, field of the protocol, inclusive range from move.schema.json
const INTEGER_LIMITS = [
  ["depth", "depth", 0, 1024],
  ["seldepth", "seldepth", 0, 1024],
  ["scoreCp", "score_cp", -100_000, 100_000],
  ["scoreMate", "score_mate", -1024, 1024],
  ["nodes", "nodes", 0, Number.MAX_SAFE_INTEGER],
] as const;

type IntegerField = (typeof INTEGER_LIMITS)[number][0];

function show(value: unknown): string {
  return typeof value === "string" ? JSON.stringify(value) : String(value);
}

function integer(name: IntegerField, value: unknown, low: number, high: number): number | null {
  let number: number | null = null;
  if (typeof value === "number" && Number.isInteger(value)) {
    number = value;
  } else if (typeof value === "bigint" && value >= low && value <= high) {
    number = Number(value);
  }
  if (number === null || number < low || number > high || (name === "scoreMate" && number === 0)) {
    Log.warn(`report: ${name}=${show(value)} is outside the protocol limits and is not sent`);
    return null;
  }
  return number;
}

function isIterable(value: unknown): value is Iterable<unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as Iterable<unknown>)[Symbol.iterator] === "function"
  );
}

function principalVariation(moves: unknown): string[] {
  if (!isIterable(moves)) {
    Log.warn(`report: pv=${show(moves)} is not a list of moves and is not sent`);
    return [];
  }
  const all = [...moves];
  if (all.length > MAX_PV_MOVES) {
    Log.debug(`report: pv truncated to ${MAX_PV_MOVES} moves`);
  }
  const pv: string[] = [];
  for (const move of all.slice(0, MAX_PV_MOVES)) {
    if (!(move instanceof Move)) {
      Log.warn(`report: pv ends before ${show(move)}, which is not a Move`);
      break;
    }
    try {
      pv.push(move.uci());
    } catch (error) {
      if (!(error instanceof ChessError)) {
        throw error;
      }
      Log.warn(`report: pv ends before ${String(move)}, which has no UCI form`);
      break;
    }
  }
  return pv;
}

function text(value: unknown): string | null {
  if (typeof value !== "string") {
    Log.warn(`report: text=${show(value)} is not a string and is not sent`);
    return null;
  }
  // Counted in code points like the schema; lone surrogates have no UTF-8 form.
  return [...value.toWellFormed()].slice(0, MAX_TEXT_LENGTH).join("");
}

function isSet(value: unknown): boolean {
  return value !== undefined && value !== null;
}

/** The info object for the move message; empty if no field is set. */
export function infoFields(info: Info): Record<string, unknown> {
  const fields: Record<string, unknown> = {};
  for (const [name, protocolName, low, high] of INTEGER_LIMITS) {
    const value: unknown = info[name];
    if (isSet(value)) {
      const number = integer(name, value, low, high);
      if (number !== null) {
        fields[protocolName] = number;
      }
    }
  }
  if ("score_cp" in fields && "score_mate" in fields) {
    Log.warn("report: scoreCp and scoreMate are both set; only scoreMate is sent");
    delete fields.score_cp;
  }
  if (isSet(info.pv)) {
    fields.pv = principalVariation(info.pv);
  }
  if (isSet(info.text)) {
    const checked = text(info.text);
    if (checked !== null) {
      fields.text = checked;
    }
  }
  return fields;
}
