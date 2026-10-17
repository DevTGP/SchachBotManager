// The package carries the version of the core (E222).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";

import * as sbm from "../src/index.ts";
import { load, ROOT } from "./spec.ts";

function coreVersion(): string {
  const cmake = readFileSync(path.join(ROOT, "sdk", "core", "CMakeLists.txt"), "utf-8");
  const match = /project\(\s*sbm_core\s+VERSION\s+(\d+\.\d+\.\d+)/.exec(cmake);
  assert.ok(match, "no version in sdk/core/CMakeLists.txt");
  return match[1];
}

test("package.json carries the version of the core", () => {
  const manifest = load<{ version: string }>(path.join(ROOT, "sdk", "javascript", "package.json"));
  assert.equal(manifest.version, coreVersion());
});

test("version is the one of the native core", () => {
  assert.equal(sbm.version, coreVersion());
});
