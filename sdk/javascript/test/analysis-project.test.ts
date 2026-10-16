// sbm-check: the files of a bot folder, the report and the command line (E208).
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";

import { EXIT_FINDINGS, EXIT_USAGE, main } from "../src/analysis/cli.ts";
import { checkProject, selectFiles } from "../src/analysis/project.ts";

const BIN = fileURLToPath(new URL("../src/analysis/bin.ts", import.meta.url));
// The flags of a bot on the server (E207); the analysis runs with them too. Without
// --no-expose-wasm here, since Node strips the types of bin.ts with WebAssembly.
const SANDBOX_FLAGS = [
  "--permission",
  "--allow-fs-read=*",
  "--disable-warning=SecurityWarning",
  "--disallow-code-generation-from-strings",
];

let root = "";

function write(relative: string, text: string): void {
  const file = path.join(root, relative);
  mkdirSync(path.dirname(file), { recursive: true });
  writeFileSync(file, text);
}

function run(args: string[]): { code: number; out: string[]; err: string[] } {
  const out: string[] = [];
  const err: string[] = [];
  const code = main(args, { out: (line) => out.push(line), err: (line) => err.push(line) });
  return { code, out, err };
}

before(() => {
  root = mkdtempSync(path.join(tmpdir(), "sbm-check-"));
  write("bot.js", 'import { helper } from "./lib/helper.js";\nhelper();\n');
  write("lib/helper.js", "export function helper() {}\n");
  write("lib/tables.mjs", "export const TABLE = [];\n");
  write("data/book.txt", "e2e4\n");
  write("data/deep/x.txt", "");
  write("README.md", "");
  write(".hidden/x.js", "");
  write(".eslintrc.js", "");
  write("node_modules/schachbotmanager/index.js", "");
  write("tests/bot.test.js", "process;\n");
});

after(() => rmSync(root, { recursive: true, force: true }));

test("selects the sources and the data files an upload takes", () => {
  const selection = selectFiles(root);
  assert.deepEqual(
    [...selection.files.keys()],
    ["bot.js", "lib/helper.js", "lib/tables.mjs", "tests/bot.test.js", "data/book.txt"].sort(
      (a, b) => a.split("/").length - b.split("/").length || (a < b ? -1 : 1),
    ),
  );
  assert.deepEqual(selection.ignored, ["README.md", "data/deep/x.txt"]);
  const excluded = selectFiles(root, ["tests/*", "lib/t?bles.mjs"]);
  assert.deepEqual([...excluded.files.keys()].sort(), ["bot.js", "data/book.txt", "lib/helper.js"]);
});

test("a symbolic link stays out", (context) => {
  try {
    symlinkSync(path.join(root, "bot.js"), path.join(root, "link.js"));
  } catch {
    context.skip("no symbolic links here");
    return;
  }
  try {
    assert.ok(!selectFiles(root).files.has("link.js"));
  } finally {
    rmSync(path.join(root, "link.js"));
  }
});

test("reports upload errors and still analyzes the sources", () => {
  const report = checkProject(selectFiles(root), "main.js");
  assert.deepEqual(
    report.findings.map((f) => [f.file, f.rule]),
    [
      ["main.js", "upload"],
      ["tests/bot.test.js", "forbidden_name"],
      ["tests/bot.test.js", "not_module"],
    ],
  );
});

test("the command line prints the report and sets the exit code", () => {
  const ok = run([root, "--exclude", "tests/*"]);
  assert.equal(ok.code, 0);
  assert.match(ok.out.at(-1) ?? "", /^sbm-check: OK, 4 files checked \(javascript-1\)$/);
  assert.deepEqual(ok.err, ["ignored: README.md, data/deep/x.txt"]);

  const failed = run([root, "--json"]);
  assert.equal(failed.code, EXIT_FINDINGS);
  const json = JSON.parse(failed.out.join("\n"));
  assert.equal(json.ok, false);
  assert.equal(json.ruleset, "javascript-1");
  assert.deepEqual(Object.keys(json.findings[0]), ["rule", "file", "line", "message"]);

  assert.equal(run([path.join(root, "missing")]).code, EXIT_USAGE);
  assert.equal(run(["--unknown"]).code, EXIT_USAGE);
  assert.equal(run([root, root]).code, EXIT_USAGE);
  assert.equal(run(["--help"]).code, 0);
});

test("the command runs with the flags of the sandbox", () => {
  const result = spawnSync(
    process.execPath,
    [...SANDBOX_FLAGS, BIN, "--json", "--exclude", "tests/*", root],
    { encoding: "utf-8" },
  );
  assert.equal(result.status, 0, result.stderr);
  assert.equal(JSON.parse(result.stdout).ok, true);
});
