// The static analysis of JavaScript bots (statische-analyse.md, E208).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";

import { analyze } from "../src/analysis/analyzer.ts";
import { makeReport, reportJson, type Report } from "../src/analysis/report.ts";
import { loadRules } from "../src/analysis/rules.ts";
import { ROOT } from "./spec.ts";

const HEADER = 'import * as sbm from "schachbotmanager";\n';

function check(files: Record<string, string>): Report {
  const encoder = new TextEncoder();
  return analyze(
    new Map(Object.entries(files).map(([file, text]) => [file, encoder.encode(text)])),
  );
}

/** [rule, line] of each finding in bot.js, whose first line imports the SDK. */
function findings(body: string, others: Record<string, string> = {}): [string, number | null][] {
  return check({ "bot.js": HEADER + body, ...others }).findings.map((f) => [f.rule, f.line]);
}

test("the template bot passes", () => {
  const source = readFileSync(path.join(ROOT, "templates", "javascript", "bot.js"), "utf-8");
  const report = check({ "bot.js": source });
  assert.deepEqual(report.findings, []);
  assert.equal(report.ruleset, "javascript-1");
});

test("imports name the SDK or a source file of the bot", () => {
  const util = { "lib/util.js": 'export const X = 1;\nimport { Y } from "../bot.js";\n' };
  assert.deepEqual(findings('import { X } from "./lib/util.js";\nexport const Y = 2;\n', util), []);
  assert.deepEqual(findings('import "./lib/missing.js";\n'), [["import_not_allowed", 2]]);
  assert.deepEqual(findings('import fs from "node:fs";\n'), [["import_not_allowed", 2]]);
  assert.deepEqual(findings('import fs from "fs";\n'), [["import_not_allowed", 2]]);
  assert.deepEqual(findings('import "../outside.js";\n'), [["import_not_allowed", 2]]);
  assert.deepEqual(findings('import "/bot/bot.js";\n'), [["import_not_allowed", 2]]);
  assert.deepEqual(findings('import data from "./data/x.json" with { type: "json" };\n'), [
    ["import_not_allowed", 2],
  ]);
  assert.deepEqual(findings('export * from "node:os";\n'), [["import_not_allowed", 2]]);
  assert.deepEqual(findings('export { cpus } from "os";\n'), [["import_not_allowed", 2]]);
});

test("import() is not allowed", () => {
  assert.deepEqual(findings('await import("./bot.js");\n'), [["dynamic_import", 2]]);
});

test("import.meta only as import.meta.main", () => {
  assert.deepEqual(findings("if (import.meta.main) sbm.run(class {});\n"), []);
  assert.deepEqual(findings("const url = import.meta.url;\n"), [["import_meta", 2]]);
  assert.deepEqual(findings("const meta = import.meta;\n"), [["import_meta", 2]]);
  assert.deepEqual(findings('const main = import.meta["main"];\n'), [["import_meta", 2]]);
});

test("forbidden globals may not appear as names", () => {
  for (const name of ["process", "globalThis", "eval", "require", "Function", "fetch", "Reflect"]) {
    assert.deepEqual(findings(`const x = ${name};\n`), [["forbidden_name", 2]], name);
  }
  assert.deepEqual(findings("function f() {\n  return arguments;\n}\n"), [["forbidden_name", 3]]);
  assert.deepEqual(findings("const process = 1;\n"), [["forbidden_name", 2]]);
  assert.deepEqual(findings("const { a: require } = {};\n"), [["forbidden_name", 2]]);
});

test("the same words as property names, labels and module names pass", () => {
  const body = [
    "const o = { process: 1, eval() {}, global: 2 };",
    "const v = o.process + o.global;",
    "class C {",
    "  process = 1;",
    "  fetch() {}",
    "}",
    "process: for (;;) break process;",
    'export { v as process, C as "eval" };',
    "",
  ].join("\n");
  assert.deepEqual(findings(body), []);
});

test("forbidden properties may appear neither as names nor as strings", () => {
  const cases = [
    "const f = [].constructor;",
    'const f = [].map["constructor"];',
    "const f = [].map[`constructor`];",
    "const o = { __proto__: null };",
    'const o = { "__proto__": null };',
    "const p = Object.getPrototypeOf({});",
    "Object.defineProperty({}, 'x', {});",
    "const { prototype } = Object;",
    "class C {\n  prototype() {}\n}",
    "const s = 'caller';",
    "Error.prepareStackTrace = null;",
  ];
  for (const body of cases) {
    const rules = findings(`${body}\n`).map(([rule]) => rule);
    assert.ok(rules.length > 0 && rules.every((rule) => rule === "forbidden_property"), body);
  }
});

test("a class may have a constructor", () => {
  assert.deepEqual(findings("export class A {\n  constructor() {}\n}\n"), []);
});

test("a .js file needs import or export, a .mjs file not", () => {
  const helper = { "helper.js": "const x = 1;\n" };
  assert.deepEqual(findings('import "./helper.js";\n', helper), [["not_module", 1]]);
  const report = check({ "bot.js": HEADER, "helper.mjs": "const x = 1;\n" });
  assert.deepEqual(report.findings, []);
});

test("encoding and syntax errors", () => {
  const broken = analyze(new Map([["bot.js", new Uint8Array([0x69, 0xff, 0x0a])]]));
  assert.deepEqual(
    broken.findings.map((f) => [f.rule, f.line]),
    [["encoding", null]],
  );
  assert.deepEqual(findings("const = 1;\n"), [["syntax_error", 2]]);
  // with is not allowed in a module, which is strict.
  assert.deepEqual(findings("with (Math) max(1);\n"), [["syntax_error", 2]]);
  const deep = `${"[".repeat(200_000)}${"]".repeat(200_000)};\n`;
  // acorn reports a stack overflow as a syntax error.
  assert.deepEqual(findings(deep), [["syntax_error", 2]]);
});

test("findings are sorted, without duplicates and limited", () => {
  const report = check({
    "b.js": "process;\nprocess;\n",
    "a.js": "eval;\n",
  });
  assert.deepEqual(
    report.findings.map((f) => [f.file, f.line, f.rule]),
    [
      ["a.js", 1, "not_module"],
      ["a.js", 1, "forbidden_name"],
      ["b.js", 1, "not_module"],
      ["b.js", 1, "forbidden_name"],
      ["b.js", 2, "forbidden_name"],
    ].sort(),
  );
  const finding = { file: "a.js", line: 1, rule: "x", message: "m" };
  const limited = makeReport("r", [finding, finding, { ...finding, line: 2 }], 1);
  assert.deepEqual(reportJson(limited), {
    ruleset: "r",
    ok: false,
    truncated: true,
    findings: [{ rule: "x", file: "a.js", line: 1, message: "m" }],
  });
  assert.equal(loadRules().maxFindings, 100);
});
