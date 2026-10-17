// Move as an immutable, interned class (E224).
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  Board,
  E2,
  E4,
  E7,
  E8,
  InvalidArgumentError,
  InvalidUciError,
  Move,
  NULL_MOVE,
  PROMOTION_QUEEN,
  RESIGN,
} from "../src/index.ts";

test("equal values give the same object", () => {
  assert.equal(Move.fromValue(796), Move.fromValue(796));
  assert.equal(Move.parse("e2e4"), Move.parse("e2e4"));
  assert.equal(Move.create(E2, E4, 0), Move.parse("e2e4"));
  const board = new Board();
  assert.equal(
    board.parseMove("e2e4"),
    board.legalMoves().find((m) => m.uci() === "e2e4"),
  );
  assert.ok(Move.parse("e2e4").equals(Move.create(E2, E4, 0)));
  assert.ok(!Move.parse("e2e4").equals(Move.parse("e2e3")));
});

test("moves are frozen", () => {
  const move = Move.parse("e2e4");
  assert.ok(Object.isFrozen(move));
  assert.throws(() => {
    (move as unknown as Record<string, unknown>).extra = 1;
  }, TypeError);
});

test("NULL_MOVE and RESIGN are moves of the class", () => {
  assert.equal(NULL_MOVE, Move.NULL_MOVE);
  assert.equal(RESIGN, Move.RESIGN);
  assert.equal(NULL_MOVE.value(), 0);
  assert.equal(RESIGN.value(), 0xffff);
});

test("toString", () => {
  assert.equal(String(Move.create(E7, E8, PROMOTION_QUEEN)), "Move(e7e8q, flags=11)");
  assert.equal(String(NULL_MOVE), "Move(NULL_MOVE)");
  assert.equal(String(RESIGN), "Move(RESIGN)");
});

test("arguments of the wrong type throw TypeError", () => {
  assert.throws(() => Move.create("e2" as unknown as number, E4, 0), TypeError);
  assert.throws(() => Move.fromValue(undefined as unknown as number), TypeError);
  assert.throws(() => Move.parse(1 as unknown as string), TypeError);
});

test("values outside their range throw InvalidArgumentError", () => {
  assert.throws(() => Move.create(64, E4, 0), InvalidArgumentError);
  assert.throws(() => Move.create(E2, E4, 6), InvalidArgumentError);
  assert.throws(() => Move.create(1.5, E4, 0), InvalidArgumentError);
  assert.throws(() => Move.fromValue(0x10000), InvalidArgumentError);
  assert.throws(() => Move.parse("e2e9"), InvalidUciError);
});

test("uci is cached and RESIGN has none", () => {
  const move = Move.parse("g1f3");
  assert.equal(move.uci(), "g1f3");
  assert.equal(move.uci(), "g1f3");
  assert.throws(() => RESIGN.uci(), InvalidArgumentError);
});
