// Every Board and Move call vector of spec/testvectors/ against the binding (E55).
import assert from "node:assert/strict";
import { test } from "node:test";

import * as sbm from "../src/index.ts";
import type { CallVector } from "./spec.ts";
import { callVectors, camel, coreFunctions } from "./spec.ts";

const FUNCTIONS = coreFunctions();
const VECTORS = callVectors();

// Types whose vector value is the string 0x plus 16 hex digits.
const HEX_TYPES = new Set(["u64", "Bitboard"]);

type Callable = (...args: unknown[]) => unknown;

function decode(value: unknown, type: string): unknown {
  return type === "Move" ? sbm.Move.fromValue(value as number) : value;
}

function encode(value: unknown, type: string): unknown {
  if (type.startsWith("list<")) {
    const item = type.slice("list<".length, -1);
    return [...(value as Iterable<unknown>)].map((entry) => encode(entry, item));
  }
  if (type === "Move") {
    return (value as sbm.Move).value();
  }
  if (type === "Board") {
    return (value as sbm.Board).fen();
  }
  if (type === "PlacedPiece") {
    const placed = value as sbm.PlacedPiece;
    return { square: placed.square, piece: placed.piece };
  }
  if (HEX_TYPES.has(type)) {
    return `0x${(value as bigint).toString(16).padStart(16, "0")}`;
  }
  return value;
}

function setupBoard(board: { fen: string; moves: string[] }): sbm.Board {
  const result = sbm.Board.fromFen(board.fen);
  for (const uci of board.moves) {
    if (uci === "0000") {
      result.makeNullMove();
    } else {
      result.makeMove(result.parseMove(uci));
    }
  }
  return result;
}

function call(vector: CallVector, board: sbm.Board | undefined): unknown {
  const spec = FUNCTIONS.get(vector.function)!;
  assert.equal(vector.args.length, spec.params.length);
  const args = vector.args.map((value, i) => decode(value, spec.params[i].type));
  const owner = spec.owner === "Board" ? sbm.Board : sbm.Move;
  if (spec.kind === "constructor") {
    // Move has no public constructor, its create is static (E224).
    return owner === sbm.Board
      ? new sbm.Board()
      : sbm.Move.create(...(args as [number, number, number]));
  }
  if (spec.kind === "static") {
    return (owner as unknown as Record<string, Callable>)[camel(spec.name)](...args);
  }
  const target = spec.owner === "Board" ? board! : sbm.Move.fromValue(vector.move!);
  const method = (target as unknown as Record<string, Callable>)[camel(spec.name)];
  return method.apply(target, args);
}

test("vectors found", () => {
  assert.ok(VECTORS.length > 500);
});

for (const vector of VECTORS) {
  test(vector.id, () => {
    const spec = FUNCTIONS.get(vector.function);
    assert.ok(spec, `unknown function ${vector.function}`);
    const board = vector.board ? setupBoard(vector.board) : undefined;
    if (vector.error !== undefined) {
      const expected = (sbm as unknown as Record<string, new () => Error>)[`${vector.error}Error`];
      assert.throws(
        () => call(vector, board),
        (error: unknown) => (error as object).constructor === expected,
      );
    } else {
      const result = call(vector, board);
      const returns = spec.returns?.type;
      const actual = returns ? encode(result, returns) : result;
      if (vector.result_contains !== undefined) {
        assert.ok(contains(actual, vector.result_contains));
      } else if (vector.unordered) {
        assert.deepEqual(sortJson(actual as unknown[]), sortJson(vector.result as unknown[]));
      } else if (returns) {
        assert.deepEqual(actual, vector.result);
      } else {
        // Functions without a result return undefined; the vectors write null.
        assert.equal(actual, undefined);
        assert.equal(vector.result ?? null, null);
      }
    }
    if (vector.board_after !== undefined) {
      assert.equal(board!.fen(), vector.board_after);
    }
  });
}

/** Like Python's in: a substring of a string or an element of a list. */
function contains(actual: unknown, expected: unknown): boolean {
  if (typeof actual === "string") {
    return actual.includes(expected as string);
  }
  return (actual as unknown[]).some((item) => isDeepEqual(item, expected));
}

function isDeepEqual(a: unknown, b: unknown): boolean {
  try {
    assert.deepEqual(a, b);
    return true;
  } catch {
    return false;
  }
}

function sortJson(values: unknown[]): string[] {
  return values.map((value) => JSON.stringify(value)).sort();
}
