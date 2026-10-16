// Reads the specification below spec/ that the tests compare the binding with.
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
export const SPEC = path.join(ROOT, "spec");

export interface Param {
  name: string;
  type: string;
}

export interface ApiFunction {
  name: string;
  owner?: string;
  kind: "constructor" | "static" | "method" | "callback" | "free";
  params: Param[];
  returns?: { type: string };
}

export interface CallVector {
  id: string;
  function: string;
  args: unknown[];
  board?: { fen: string; moves: string[] };
  move?: number;
  result?: unknown;
  result_contains?: unknown;
  unordered?: boolean;
  error?: string;
  board_after?: string;
}

export function load<T = unknown>(file: string): T {
  return JSON.parse(readFileSync(file, "utf-8")) as T;
}

// Modules of spec/api/ whose functions the native addon implements.
export const CORE_MODULES = [
  "board",
  "board_moves",
  "board_query",
  "board_raw",
  "board_state",
  "move",
];

/** The functions of the modules, e.g. bot or runtime. */
export function apiFunctions(modules: readonly string[]): ApiFunction[] {
  return modules.flatMap(
    (module) =>
      load<{ functions: ApiFunction[] }>(path.join(SPEC, "api", `${module}.json`)).functions,
  );
}

/** Board and Move functions by their full name in the spec, e.g. Board.make_move. */
export function coreFunctions(): Map<string, ApiFunction> {
  return new Map(apiFunctions(CORE_MODULES).map((f) => [`${f.owner}.${f.name}`, f]));
}

function jsonFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true })
    .flatMap((entry) => {
      const full = path.join(directory, entry.name);
      return entry.isDirectory() ? jsonFiles(full) : [full];
    })
    .filter((file) => file.endsWith(".json"));
}

/** Call vectors (spec/testvectors/calls.schema.json); perft.json has its own format. */
export function callVectors(): CallVector[] {
  return jsonFiles(path.join(SPEC, "testvectors"))
    .filter((file) => !file.endsWith(".schema.json") && path.basename(file) !== "perft.json")
    .sort()
    .flatMap((file) => load<{ vectors: CallVector[] }>(file).vectors);
}

export function constants(): { name: string; type: string; value: number }[] {
  return load<{ constants: { name: string; type: string; value: number }[] }>(
    path.join(SPEC, "api", "constants.json"),
  ).constants;
}

/** The spelling of a spec name in JavaScript (E224): make_null_move becomes makeNullMove. */
export function camel(name: string): string {
  return name.replace(/_([a-z0-9])/g, (_, letter: string) => letter.toUpperCase());
}

/** A valid example message of the protocol, e.g. "init.standard". */
export function example(name: string): Record<string, unknown> {
  return load(path.join(SPEC, "protocol", "v1", "examples", "valid", `${name}.json`));
}
