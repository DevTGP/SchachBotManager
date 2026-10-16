// Loads the addon sbm.node for this platform (E201) and hands it the error classes, so that
// errors of the core arrive as ChessError and its subclasses.
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  ChessError,
  DataNotFoundError,
  IllegalMoveError,
  InvalidArgumentError,
  InvalidFenError,
  InvalidStateError,
  InvalidUciError,
} from "./errors.ts";

/** One board of the core; returns plain values only, src/board.ts builds the API on it. */
export interface NativeBoard {
  fen(): string;
  toText(): string;
  copy(): NativeBoard;
  hash(): bigint;
  hash32(): Uint32Array;
  moveHistory(): Uint16Array;

  legalMoves(): Uint16Array;
  legalCaptures(): Uint16Array;
  allMovesFrom(square: number): Uint16Array;
  isLegal(move: number): boolean;
  parseMove(uci: string): number;
  san(move: number): string;
  makeMove(move: number): void;
  undoMove(): void;
  makeNullMove(): void;
  undoNullMove(): void;

  pieceAt(square: number): number;
  pieces(color: number, pieceType: number): Uint8Array;
  sideToMove(): number;
  castlingRights(): number;
  enPassantSquare(): number;
  halfmoveClock(): number;
  fullmoveNumber(): number;
  kingSquare(color: number): number;

  bitboard(color: number, pieceType: number): bigint;
  bitboard32(color: number, pieceType: number): Uint32Array;
  bitboards(): BigUint64Array;
  bitboards32(): Uint32Array;
  squares(): Uint8Array;
  occupied(): bigint;
  occupied32(): Uint32Array;
  occupiedBy(color: number): bigint;
  occupiedBy32(color: number): Uint32Array;
  pieceCount(color: number, pieceType: number): number;
  attacksFrom(square: number): bigint;
  attacksFrom32(square: number): Uint32Array;
  attackersOf(square: number, color: number): bigint;
  attackersOf32(square: number, color: number): Uint32Array;
  isAttacked(square: number, color: number): boolean;
  checkers(): bigint;
  checkers32(): Uint32Array;
  pinned(color: number): bigint;
  pinned32(color: number): Uint32Array;

  isCheck(): boolean;
  isCheckmate(): boolean;
  isStalemate(): boolean;
  isRepetition(count: number): boolean;
  isFiftyMoveRule(): boolean;
  isInsufficientMaterial(): boolean;
  hasInsufficientMaterial(color: number): boolean;
  isDraw(): boolean;
  isGameOver(): boolean;
}

interface NativeModule {
  NativeBoard: new (fen?: string) => NativeBoard;
  moveParse(uci: string): number;
  moveUci(value: number): string;
  version: string;
  setErrorClasses(classes: Record<string, typeof ChessError>): void;
}

// src/native.ts and dist/native.js both sit one level below the package root.
const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const addonPath = path.join(root, "prebuilds", `${process.platform}-${process.arch}`, "sbm.node");

function load(): NativeModule {
  try {
    return createRequire(import.meta.url)(addonPath) as NativeModule;
  } catch (error) {
    throw new Error(
      `schachbotmanager: no native addon for ${process.platform}-${process.arch} at ${addonPath}`,
      { cause: error },
    );
  }
}

export const native: NativeModule = load();

native.setErrorClasses({
  ChessError,
  InvalidArgumentError,
  InvalidFenError,
  InvalidUciError,
  IllegalMoveError,
  InvalidStateError,
  DataNotFoundError,
});
