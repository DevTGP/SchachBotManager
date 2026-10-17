// Every function of spec/api/ exists in camelCase with its kind and parameter count (E224).
import assert from "node:assert/strict";
import { test } from "node:test";

import * as sbm from "../src/index.ts";
import { apiFunctions, camel, CORE_MODULES } from "./spec.ts";

const MODULES = [...CORE_MODULES, "bot", "clock", "log", "runtime"];

// Not part of this SDK until step 3 of E220.
const LATER = new Set(["play"]);

// Parameters with a default value, which Function.length does not count.
const DEFAULTS: Record<string, number> = { "Board.pieces": 2, run: 1 };

// The constructor of a class as spec create; Move has a static create instead (E224).
const CONSTRUCTORS: Record<string, string> = { Board: "constructor", Move: "static" };

type Owner = Record<string, unknown> & { prototype: Record<string, unknown> };

const exports = sbm as unknown as Record<string, unknown>;

for (const spec of apiFunctions(MODULES)) {
  const name = camel(spec.name);
  const full = spec.owner ? `${spec.owner}.${name}` : name;
  if (LATER.has(name)) {
    test(`${full} comes later`, () => assert.equal(exports[name], undefined));
    continue;
  }
  test(full, () => {
    let member: unknown;
    if (spec.kind === "free") {
      member = exports[name];
    } else {
      const owner = exports[spec.owner!] as Owner;
      assert.equal(typeof owner, "function", `${spec.owner} is not exported`);
      if (spec.kind === "constructor") {
        member = CONSTRUCTORS[spec.owner!] === "static" ? owner[name] : owner;
      } else if (spec.kind === "static") {
        member = owner[name];
      } else if (spec.kind === "callback" && name === "chooseMove") {
        // Abstract: the bot defines it, run checks that it exists.
        return;
      } else {
        member = owner.prototype[name];
      }
    }
    assert.equal(typeof member, "function", `${full} is missing`);
    const expected = spec.params.length - (DEFAULTS[full] ?? 0);
    assert.equal((member as (...args: unknown[]) => unknown).length, expected);
  });
}

test("constructors and Log are guarded", () => {
  assert.throws(() => new (sbm.Move as unknown as new (value: number) => unknown)(1), TypeError);
  assert.throws(() => new (sbm.Log as unknown as new () => unknown)(), TypeError);
});

test("error classes derive from ChessError and carry their name", () => {
  for (const name of [
    "InvalidArgument",
    "InvalidFen",
    "InvalidUci",
    "IllegalMove",
    "InvalidState",
    "DataNotFound",
  ]) {
    const ErrorClass = exports[`${name}Error`] as new (message: string) => Error;
    const error = new ErrorClass("x");
    assert.ok(error instanceof sbm.ChessError);
    assert.ok(error instanceof Error);
    assert.equal(error.name, `${name}Error`);
  }
});
