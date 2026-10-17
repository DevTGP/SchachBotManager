// Board beyond the vectors: the variants ending in 32, typed arrays and argument checks.
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  BLACK,
  BLACK_KING,
  Board,
  E1,
  E4,
  KING,
  Move,
  NO_COLOR,
  NO_PIECE_TYPE,
  PAWN,
  WHITE,
  WHITE_KING,
} from "../src/index.ts";

const POSITIONS = [
  "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
  "4k3/8/8/8/1b6/8/3P4/4K3 w - - 0 1",
  "4k3/8/8/8/8/8/8/R3K2q w Q - 0 1",
];

function join(halves: Uint32Array, index = 0): bigint {
  return BigInt(halves[2 * index]) | (BigInt(halves[2 * index + 1]) << 32n);
}

test("the variants ending in 32 give low and high half of the bigint", () => {
  for (const fen of POSITIONS) {
    const board = Board.fromFen(fen);
    assert.equal(join(board.hash32()), board.hash());
    assert.equal(join(board.occupied32()), board.occupied());
    assert.equal(join(board.checkers32()), board.checkers());
    const bitboards = board.bitboards();
    const halves = board.bitboards32();
    assert.equal(bitboards.length, 12);
    assert.equal(halves.length, 24);
    for (let piece = 0; piece < 12; piece += 1) {
      assert.equal(join(halves, piece), bitboards[piece]);
    }
    for (const color of [WHITE, BLACK]) {
      assert.equal(join(board.occupiedBy32(color)), board.occupiedBy(color));
      assert.equal(join(board.pinned32(color)), board.pinned(color));
      assert.equal(join(board.bitboard32(color, PAWN)), board.bitboard(color, PAWN));
      assert.equal(join(board.attackersOf32(E4, color)), board.attackersOf(E4, color));
    }
    for (let square = 0; square < 64; square += 1) {
      assert.equal(join(board.attacksFrom32(square)), board.attacksFrom(square));
    }
  }
});

test("bitboards and squares are typed arrays", () => {
  const board = new Board();
  assert.ok(board.bitboards() instanceof BigUint64Array);
  const squares = board.squares();
  assert.ok(squares instanceof Uint8Array);
  assert.equal(squares.length, 64);
  assert.equal(squares[E1], WHITE_KING);
  assert.equal(squares[60], BLACK_KING);
});

test("pieces has optional color and type and gives frozen records", () => {
  const board = new Board();
  assert.equal(board.pieces().length, 32);
  assert.deepEqual(board.pieces(NO_COLOR, KING), board.pieces(undefined, KING));
  assert.equal(board.pieces(WHITE).length, 16);
  assert.deepEqual(board.pieces(BLACK, KING), [{ square: 60, piece: BLACK_KING }]);
  assert.equal(board.pieces(WHITE, NO_PIECE_TYPE).length, 16);
  assert.ok(Object.isFrozen(board.pieces()[0]));
});

test("copy is independent and moves are shared values", () => {
  const board = new Board();
  const copy = board.copy();
  copy.makeMove(copy.parseMove("e2e4"));
  assert.equal(board.moveHistory().length, 0);
  assert.equal(copy.moveHistory()[0], Move.fromValue(copy.moveHistory()[0].value()));
  assert.notEqual(copy.fen(), board.fen());
});

test("a move that is not a Move throws TypeError", () => {
  const board = new Board();
  assert.throws(() => board.makeMove("e2e4" as unknown as Move), TypeError);
  assert.throws(() => board.isLegal({} as Move), TypeError);
  assert.throws(() => board.san(796 as unknown as Move), TypeError);
});

test("toString shows the FEN", () => {
  assert.equal(String(new Board()), `Board(${new Board().fen()})`);
});

test("many boards can be created and dropped", () => {
  for (let i = 0; i < 20_000; i += 1) {
    new Board().copy();
  }
});
