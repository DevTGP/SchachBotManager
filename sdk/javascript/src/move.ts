// Move (spec/api/move.json): an immutable 16-bit value. Each value has exactly one object, so
// moves compare with === as well as with equals (E204). The bit operations are computed here;
// parse and uci call the core.
import type { MoveFlags, PieceType, Square } from "./constants.ts";
import { NO_PIECE_TYPE } from "./constants.ts";
import { InvalidArgumentError } from "./errors.ts";
import { native } from "./native.ts";

const TO_SHIFT = 6;
const FLAG_SHIFT = 12;

const table: (Move | undefined)[] = [];
// Set while intern builds an object; any other call of the constructor is refused.
let interning = false;
// Set by the class itself: outside its body the name Move is not usable before the static
// fields NULL_MOVE and RESIGN exist.
let construct: (value: number) => Move;

function unusedFlags(flags: number): boolean {
  return flags === 6 || flags === 7;
}

function integer(value: unknown, what: string): number {
  if (typeof value !== "number") {
    throw new TypeError(`${what} must be a number, not ${typeof value}`);
  }
  if (!Number.isInteger(value)) {
    throw new InvalidArgumentError(`${what}: ${value} is not an integer`);
  }
  return value;
}

/** The one Move object of a valid value; the board and the parser call it with core values. */
export function intern(value: number): Move {
  let move = table[value];
  if (move === undefined) {
    interning = true;
    try {
      move = construct(value);
    } finally {
      interning = false;
    }
    table[value] = move;
  }
  return move;
}

/** A move as 16-bit value: bits 0 to 5 from-square, 6 to 11 to-square, 12 to 15 flags. */
export class Move {
  static {
    construct = (value) => new Move(value);
  }

  /** No move; also the move recorded for makeNullMove. */
  static readonly NULL_MOVE: Move = intern(0);
  /** Returned from chooseMove to resign; never a legal move. */
  static readonly RESIGN: Move = intern(0xffff);

  readonly #value: number;
  #uci: string | undefined;

  private constructor(value: number) {
    if (!interning) {
      throw new TypeError("Move has no public constructor; use Move.create, fromValue or parse");
    }
    this.#value = value;
    Object.freeze(this);
  }

  /** Builds a move from its parts without checking it against a position. */
  static create(fromSquare: Square, toSquare: Square, flags: MoveFlags): Move {
    const from = integer(fromSquare, "Move.create: fromSquare");
    const to = integer(toSquare, "Move.create: toSquare");
    const bits = integer(flags, "Move.create: flags");
    if (from < 0 || from > 63 || to < 0 || to > 63) {
      throw new InvalidArgumentError("Move: squares must be 0 to 63");
    }
    if (bits < 0 || bits > 15 || unusedFlags(bits)) {
      throw new InvalidArgumentError("Move: flags must be 0 to 5 or 8 to 15");
    }
    return intern(from | (to << TO_SHIFT) | (bits << FLAG_SHIFT));
  }

  /** Wraps a raw 16-bit value, e.g. from a transposition table. */
  static fromValue(value: number): Move {
    const number = integer(value, "Move.fromValue: value");
    if (number < 0 || number > 0xffff) {
      throw new InvalidArgumentError("Move.fromValue: value must be 0 to 65535");
    }
    if (unusedFlags(number >> FLAG_SHIFT)) {
      throw new InvalidArgumentError("Move.fromValue: flags 6 and 7 are unused");
    }
    return intern(number);
  }

  /** Reads UCI notation without a board; Board.parseMove gives the complete move. */
  static parse(uci: string): Move {
    return intern(native.moveParse(uci));
  }

  /** The raw 16-bit value. */
  value(): number {
    return this.#value;
  }

  /** Bits 0 to 5. */
  fromSquare(): Square {
    return this.#value & 0x3f;
  }

  /** Bits 6 to 11. */
  toSquare(): Square {
    return (this.#value >> TO_SHIFT) & 0x3f;
  }

  /** Bits 12 to 15. */
  flags(): MoveFlags {
    return this.#value >> FLAG_SHIFT;
  }

  /** Piece type the pawn turns into, KNIGHT to QUEEN, or NO_PIECE_TYPE. */
  promotion(): PieceType {
    const flags = this.flags();
    return flags >= 8 ? (flags & 3) + 1 : NO_PIECE_TYPE;
  }

  /** Flags 8 to 15. */
  isPromotion(): boolean {
    return this.flags() >= 8;
  }

  /** Flags 4, 5 and 12 to 15, i.e. including en passant. */
  isCapture(): boolean {
    const flags = this.flags();
    return flags === 4 || flags === 5 || flags >= 12;
  }

  /** Flags 2 and 3. */
  isCastling(): boolean {
    const flags = this.flags();
    return flags === 2 || flags === 3;
  }

  /** Flag 5. */
  isEnPassant(): boolean {
    return this.flags() === 5;
  }

  /** UCI notation, e.g. e2e4 or e7e8q; NULL_MOVE and RESIGN throw InvalidArgumentError. */
  uci(): string {
    this.#uci ??= native.moveUci(this.#value);
    return this.#uci;
  }

  /** Whether both moves have the same value; for moves the same as ===. */
  equals(other: unknown): boolean {
    return other === this;
  }

  toString(): string {
    if (this.#value === 0) {
      return "Move(NULL_MOVE)";
    }
    if (this.#value === 0xffff) {
      return "Move(RESIGN)";
    }
    return `Move(${this.uci()}, flags=${this.flags()})`;
  }
}

/** No move; also the move recorded for makeNullMove. */
export const NULL_MOVE: Move = Move.NULL_MOVE;
/** Returned from chooseMove to resign; never a legal move. */
export const RESIGN: Move = Move.RESIGN;

/** Moves from the core as Move objects. */
export function moveList(values: Uint16Array): Move[] {
  return Array.from(values, intern);
}
