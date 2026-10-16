// What an upload of a JavaScript bot may contain (verifikation.md, E207).
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  DATA,
  MAX_DATA_BYTES,
  MAX_SOURCE_FILES,
  SOURCE,
  UploadError,
  checkUpload,
  fileKind,
} from "../src/analysis/upload.ts";

function rejects(action: () => unknown, path?: string): void {
  assert.throws(action, (error) => error instanceof UploadError && error.path === path);
}

test("source files are .js and .mjs files, data files lie directly in data/", () => {
  assert.equal(fileKind("bot.js"), SOURCE);
  assert.equal(fileKind("lib/search.mjs"), SOURCE);
  assert.equal(fileKind("data/book.bin"), DATA);
  assert.equal(fileKind("data/notes.js"), DATA);
  for (const path of ["bot.py", "bot.ts", "bot.cjs", "package.json", "data/sub/x.bin"]) {
    rejects(() => fileKind(path), path);
  }
});

test("paths are plain, short and outside node_modules", () => {
  for (const path of [
    ".hidden.js",
    "a//b.js",
    "../bot.js",
    "a b.js",
    "node_modules/x.js",
    "lib/Node_Modules/x.js",
    `${"a/".repeat(8)}b.js`,
    `${"a".repeat(200)}.js`,
  ]) {
    rejects(() => fileKind(path), path);
  }
});

test("the entry file is a top-level source file of the upload", () => {
  const files = [
    ["bot.js", 10],
    ["lib/a.js", 5],
    ["data/book.bin", 3],
  ] as const;
  assert.deepEqual(
    checkUpload(files, "bot.js").map((file) => [file.path, file.kind, file.size]),
    [
      ["bot.js", SOURCE, 10],
      ["lib/a.js", SOURCE, 5],
      ["data/book.bin", DATA, 3],
    ],
  );
  rejects(() => checkUpload(files, "main.js"), "main.js");
  rejects(() => checkUpload(files, "lib/a.js"), "lib/a.js");
  rejects(() => checkUpload(files, "bot.py"), "bot.py");
});

test("counts and sizes are limited per kind", () => {
  const many = Array.from({ length: MAX_SOURCE_FILES + 1 }, (_, i) => [`m${i}.js`, 1] as const);
  rejects(() => checkUpload([["bot.js", 1], ...many], "bot.js"));
  rejects(() =>
    checkUpload(
      [
        ["bot.js", 1],
        ["data/big", MAX_DATA_BYTES + 1],
      ],
      "bot.js",
    ),
  );
  assert.equal(
    checkUpload(
      [
        ["bot.js", 1],
        ["data/big", MAX_DATA_BYTES],
      ],
      "bot.js",
    ).length,
    2,
  );
});

test("paths are unique also across case, and no file is named like a folder", () => {
  const twice = [
    ["bot.js", 1],
    ["Bot.js", 1],
  ] as const;
  rejects(() => checkUpload(twice, "bot.js"), "Bot.js");
  const clash = [
    ["bot.js", 1],
    ["lib.js", 1],
    ["lib.js/a.js", 1],
  ] as const;
  rejects(() => checkUpload(clash, "bot.js"), "lib.js");
});
