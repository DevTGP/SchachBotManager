// loadData: plain names in the data directory only (E62).
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { after, before, test } from "node:test";

import { DataNotFoundError, InvalidArgumentError, loadData } from "../src/index.ts";
import { DATA_DIR_VARIABLE, dataDirectory } from "../src/data.ts";

let directory = "";
let saved: string | undefined;

before(() => {
  directory = mkdtempSync(path.join(tmpdir(), "sbm-data-"));
  writeFileSync(path.join(directory, "book.bin"), Buffer.from([0, 1, 2, 255]));
  writeFileSync(path.join(directory, "empty"), "");
  mkdirSync(path.join(directory, "folder"));
  saved = process.env[DATA_DIR_VARIABLE];
  process.env[DATA_DIR_VARIABLE] = directory;
});

after(() => {
  if (saved === undefined) {
    delete process.env[DATA_DIR_VARIABLE];
  } else {
    process.env[DATA_DIR_VARIABLE] = saved;
  }
  rmSync(directory, { recursive: true, force: true });
});

test("reads the file as bytes", () => {
  const data = loadData("book.bin");
  assert.ok(data instanceof Uint8Array);
  assert.deepEqual([...data], [0, 1, 2, 255]);
  assert.equal(loadData("empty").length, 0);
});

test("a missing file or a folder is not found", () => {
  assert.throws(() => loadData("missing.bin"), DataNotFoundError);
  assert.throws(() => loadData("folder"), DataNotFoundError);
});

for (const name of [
  "",
  ".",
  "..",
  "../book.bin",
  "a/b",
  "a\\b",
  "/etc/passwd",
  "C:book.bin",
  "a\0b",
]) {
  test(`${JSON.stringify(name)} is not a plain name`, () => {
    assert.throws(() => loadData(name), InvalidArgumentError);
  });
}

test("the name must be a string", () => {
  assert.throws(() => loadData(1 as unknown as string), TypeError);
});

test("without the variable the folder data next to the main module", () => {
  delete process.env[DATA_DIR_VARIABLE];
  try {
    assert.equal(dataDirectory(), path.join(path.dirname(path.resolve(process.argv[1])), "data"));
  } finally {
    process.env[DATA_DIR_VARIABLE] = directory;
  }
});
