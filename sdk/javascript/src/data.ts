// loadData (spec/api/runtime.json, E30, E62, E225): the data files uploaded with the bot.
import { readFileSync, statSync } from "node:fs";
import path from "node:path";

import { DataNotFoundError, InvalidArgumentError } from "./errors.ts";

export const DATA_DIR_VARIABLE = "SBM_DATA_DIR";

/** SBM_DATA_DIR if set (server), otherwise the directory data next to the main module. */
export function dataDirectory(): string {
  const configured = process.env[DATA_DIR_VARIABLE];
  if (configured) {
    return configured;
  }
  const main = process.argv[1];
  const base = main ? path.dirname(path.resolve(main)) : process.cwd();
  return path.join(base, "data");
}

function isPlainName(name: string): boolean {
  if (name === "" || name === "." || name === ".." || /[/\\\0]/.test(name)) {
    return false;
  }
  // Catches what the platform reads as a path anyway, e.g. the drive in C:book.bin on Windows.
  return path.basename(name) === name && path.parse(name).root === "" && !/^[A-Za-z]:/.test(name);
}

/** Contents of the data file with this name; the only way for a bot to read files. */
export function loadData(name: string): Uint8Array {
  if (typeof name !== "string") {
    throw new TypeError(`loadData: name must be a string, not ${typeof name}`);
  }
  if (!isPlainName(name)) {
    throw new InvalidArgumentError(`loadData: ${JSON.stringify(name)} is not a plain file name`);
  }
  const directory = dataDirectory();
  const file = path.join(directory, name);
  if (!statSync(file, { throwIfNoEntry: false })?.isFile()) {
    throw new DataNotFoundError(`loadData: no data file ${JSON.stringify(name)} in ${directory}`);
  }
  const content = readFileSync(file);
  return new Uint8Array(content.buffer, content.byteOffset, content.byteLength);
}
