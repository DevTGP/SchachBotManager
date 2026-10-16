// Log: line format, levels and the optional file.
import assert from "node:assert/strict";
import { closeSync, mkdtempSync, openSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";

import { DEBUG, ERROR, INFO, InvalidArgumentError, Log, OFF, TRACE, WARN } from "../src/index.ts";
import type { LogLevel } from "../src/index.ts";
import { configure, setPly } from "../src/log.ts";
import { captureLog } from "./capture.ts";

const lines = captureLog();
const LINE = /^\d\d:\d\d:\d\d\.\d\d\d \[ply (-|\d+)\] (TRACE|DEBUG|INFO |WARN |ERROR) (.*)\n$/s;

test("a line carries time, ply and level", () => {
  Log.info("before the first turn");
  setPly(12);
  Log.warn("in turn 12");
  assert.equal(lines.length, 2);
  assert.match(lines[0], LINE);
  assert.ok(lines[0].endsWith(" [ply -] INFO  before the first turn\n"));
  assert.ok(lines[1].endsWith(" [ply 12] WARN  in turn 12\n"));
});

test("the level filters lines", () => {
  Log.trace("t");
  Log.debug("d");
  Log.info("i");
  Log.setLevel(ERROR);
  Log.warn("w");
  Log.error("e");
  Log.setLevel(TRACE);
  Log.trace("t2");
  Log.setLevel(OFF);
  Log.error("never");
  assert.deepEqual(
    lines.map((line) => LINE.exec(line)?.slice(2)),
    [
      ["INFO ", "i"],
      ["ERROR", "e"],
      ["TRACE", "t2"],
    ],
  );
});

test("level and isEnabled", () => {
  assert.equal(Log.level(), INFO);
  assert.ok(!Log.isEnabled(DEBUG));
  assert.ok(Log.isEnabled(INFO));
  assert.ok(Log.isEnabled(ERROR));
  assert.ok(!Log.isEnabled(OFF));
  Log.setLevel(WARN);
  assert.equal(Log.level(), WARN);
  assert.ok(!Log.isEnabled(INFO));
});

test("unknown levels are rejected", () => {
  for (const level of [-1, 6, 2.5]) {
    assert.throws(() => Log.setLevel(level as LogLevel), InvalidArgumentError);
    assert.throws(() => Log.isEnabled(level as LogLevel), InvalidArgumentError);
  }
  assert.throws(() => Log.setLevel("INFO" as unknown as LogLevel), TypeError);
  assert.equal(Log.level(), INFO);
});

test("messages of any type are written as text", () => {
  Log.info(42 as unknown as string);
  Log.info("two\nlines");
  assert.ok(lines[0].endsWith(" INFO  42\n"));
  assert.ok(lines[1].endsWith(" INFO  two\nlines\n"));
});

test("a log file receives the same lines", () => {
  const directory = mkdtempSync(path.join(tmpdir(), "sbm-log-"));
  try {
    const file = openSync(path.join(directory, "bot.log"), "a");
    configure(DEBUG, file);
    Log.debug("to both");
    configure(INFO, undefined);
    Log.info("only to the output");
    closeSync(file);
    assert.equal(readFileSync(path.join(directory, "bot.log"), "utf-8"), lines[0]);
    assert.equal(lines.length, 2);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Log has no instances", () => {
  assert.throws(() => new (Log as unknown as new () => unknown)(), TypeError);
});
