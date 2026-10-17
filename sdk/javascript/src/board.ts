// Board (spec/api/board*.json): a position with move history, backed by one board of the core.
// The native handle is freed with the object by the garbage collector (E22).
import type { Bitboard, CastlingRights, Color, Piece, PieceType, Square } from "./constants.ts";
import { NO_COLOR, NO_PIECE_TYPE } from "./constants.ts";
import { intern, Move, moveList } from "./move.ts";
import type { NativeBoard } from "./native.ts";
import { native } from "./native.ts";
import type { PlacedPiece } from "./records.ts";

// Set while fromNative wraps an existing native board.
let adopted: NativeBoard | undefined;

function wrap(board: NativeBoard): Board {
  adopted = board;
  try {
    return new Board();
  } finally {
    adopted = undefined;
  }
}

function moveValue(move: Move, what: string): number {
  if (!(move instanceof Move)) {
    throw new TypeError(`${what}: move must be a Move`);
  }
  return move.value();
}

/** Chess position with move history. new Board() is the start position. */
export class Board {
  readonly #native: NativeBoard;

  constructor() {
    this.#native = adopted ?? new native.NativeBoard();
  }

  /** The position of a FEN string; throws InvalidFenError. */
  static fromFen(fen: string): Board {
    return wrap(new native.NativeBoard(fen));
  }

  /** The position as FEN. */
  fen(): string {
    return this.#native.fen();
  }

  /** An independent copy including the move history. */
  copy(): Board {
    return wrap(this.#native.copy());
  }

  /** Zobrist hash, equal to the Polyglot book key of the position. */
  hash(): bigint {
    return this.#native.hash();
  }

  /** hash as low and high 32 bits. */
  hash32(): Uint32Array {
    return this.#native.hash32();
  }

  /** Moves made on this board that are not undone; NULL_MOVE for a null move. */
  moveHistory(): Move[] {
    return moveList(this.#native.moveHistory());
  }

  /** Readable diagram for debugging; the exact layout is not part of the API. */
  toText(): string {
    return this.#native.toText();
  }

  toString(): string {
    return `Board(${this.fen()})`;
  }

  // Moves (spec/api/board_moves.json)

  /** All legal moves of the side to move. */
  legalMoves(): Move[] {
    return moveList(this.#native.legalMoves());
  }

  /** The legal captures, including en passant and capturing promotions. */
  legalCaptures(): Move[] {
    return moveList(this.#native.legalCaptures());
  }

  /** Pseudo-legal moves of the piece on the square, whichever color is to move (E190). */
  allMovesFrom(square: Square): Move[] {
    return moveList(this.#native.allMovesFrom(square));
  }

  /** Whether a legal move with the same from-square, to-square and promotion exists. */
  isLegal(move: Move): boolean {
    return this.#native.isLegal(moveValue(move, "Board.isLegal"));
  }

  /** Reads UCI notation and looks the move up in this position. */
  parseMove(uci: string): Move {
    return intern(this.#native.parseMove(uci));
  }

  /** Standard algebraic notation of a legal move in this position. */
  san(move: Move): string {
    return this.#native.san(moveValue(move, "Board.san"));
  }

  /** Plays a legal move and appends it to the history; on error the board is unchanged. */
  makeMove(move: Move): void {
    this.#native.makeMove(moveValue(move, "Board.makeMove"));
  }

  /** Takes back the last move; InvalidStateError if there is none or it is a null move. */
  undoMove(): void {
    this.#native.undoMove();
  }

  /** Passes the turn for null-move pruning; InvalidStateError while in check. */
  makeNullMove(): void {
    this.#native.makeNullMove();
  }

  /** Takes back the last null move. */
  undoNullMove(): void {
    this.#native.undoNullMove();
  }

  // Queries (spec/api/board_query.json)

  /** The piece on the square or NO_PIECE. */
  pieceAt(square: Square): Piece {
    return this.#native.pieceAt(square);
  }

  /** The pieces with their squares, of one color or both and of one type or all (E190). */
  pieces(color: Color = NO_COLOR, pieceType: PieceType = NO_PIECE_TYPE): PlacedPiece[] {
    const pairs = this.#native.pieces(color, pieceType);
    const result: PlacedPiece[] = [];
    for (let i = 0; i < pairs.length; i += 2) {
      result.push(Object.freeze({ square: pairs[i], piece: pairs[i + 1] }));
    }
    return result;
  }

  sideToMove(): Color {
    return this.#native.sideToMove();
  }

  castlingRights(): CastlingRights {
    return this.#native.castlingRights();
  }

  /** Target square of a legal en passant capture or NO_SQUARE. */
  enPassantSquare(): Square {
    return this.#native.enPassantSquare();
  }

  halfmoveClock(): number {
    return this.#native.halfmoveClock();
  }

  fullmoveNumber(): number {
    return this.#native.fullmoveNumber();
  }

  /** The square of the king of that color. */
  kingSquare(color: Color): Square {
    return this.#native.kingSquare(color);
  }

  // Raw access (spec/api/board_raw.json); the variants ending in 32 give low and high half.

  bitboard(color: Color, pieceType: PieceType): Bitboard {
    return this.#native.bitboard(color, pieceType);
  }

  bitboard32(color: Color, pieceType: PieceType): Uint32Array {
    return this.#native.bitboard32(color, pieceType);
  }

  /** The twelve bitboards in the order of Piece. */
  bitboards(): BigUint64Array {
    return this.#native.bitboards();
  }

  /** The twelve bitboards as 24 halves, low half first. */
  bitboards32(): Uint32Array {
    return this.#native.bitboards32();
  }

  /** The piece on each of the 64 squares, NO_PIECE for empty ones. */
  squares(): Uint8Array {
    return this.#native.squares();
  }

  occupied(): Bitboard {
    return this.#native.occupied();
  }

  occupied32(): Uint32Array {
    return this.#native.occupied32();
  }

  occupiedBy(color: Color): Bitboard {
    return this.#native.occupiedBy(color);
  }

  occupiedBy32(color: Color): Uint32Array {
    return this.#native.occupiedBy32(color);
  }

  pieceCount(color: Color, pieceType: PieceType): number {
    return this.#native.pieceCount(color, pieceType);
  }

  /** Squares attacked by the piece on that square; pins are ignored. */
  attacksFrom(square: Square): Bitboard {
    return this.#native.attacksFrom(square);
  }

  attacksFrom32(square: Square): Uint32Array {
    return this.#native.attacksFrom32(square);
  }

  /** Pieces of that color that attack the square; pins are ignored. */
  attackersOf(square: Square, color: Color): Bitboard {
    return this.#native.attackersOf(square, color);
  }

  attackersOf32(square: Square, color: Color): Uint32Array {
    return this.#native.attackersOf32(square, color);
  }

  isAttacked(square: Square, color: Color): boolean {
    return this.#native.isAttacked(square, color);
  }

  /** Pieces giving check to the side to move. */
  checkers(): Bitboard {
    return this.#native.checkers();
  }

  checkers32(): Uint32Array {
    return this.#native.checkers32();
  }

  /** Pieces of that color pinned to their king. */
  pinned(color: Color): Bitboard {
    return this.#native.pinned(color);
  }

  pinned32(color: Color): Uint32Array {
    return this.#native.pinned32(color);
  }

  // State (spec/api/board_state.json)

  isCheck(): boolean {
    return this.#native.isCheck();
  }

  isCheckmate(): boolean {
    return this.#native.isCheckmate();
  }

  isStalemate(): boolean {
    return this.#native.isStalemate();
  }

  /** The position has occurred at least count times, counting itself; 3 is threefold. */
  isRepetition(count: number): boolean {
    return this.#native.isRepetition(count);
  }

  isFiftyMoveRule(): boolean {
    return this.#native.isFiftyMoveRule();
  }

  isInsufficientMaterial(): boolean {
    return this.#native.isInsufficientMaterial();
  }

  hasInsufficientMaterial(color: Color): boolean {
    return this.#native.hasInsufficientMaterial(color);
  }

  isDraw(): boolean {
    return this.#native.isDraw();
  }

  isGameOver(): boolean {
    return this.#native.isGameOver();
  }
}
