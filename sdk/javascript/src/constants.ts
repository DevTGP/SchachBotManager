// Named constants of the bot API (spec/api/constants.json) as plain numbers (E224). NULL_MOVE
// and RESIGN are Move objects and live in src/move.ts.

/** WHITE = 0, BLACK = 1; NO_COLOR = 2. */
export type Color = number;
/** PAWN = 0 to KING = 5; NO_PIECE_TYPE = 6. */
export type PieceType = number;
/** color * 6 + piece type (0 to 11); NO_PIECE = 12. */
export type Piece = number;
/** rank * 8 + file, a1 = 0 to h8 = 63; NO_SQUARE = 64. */
export type Square = number;
/** Set of squares; bit i stands for square i. */
export type Bitboard = bigint;
/** Bit set of WHITE_KINGSIDE, WHITE_QUEENSIDE, BLACK_KINGSIDE, BLACK_QUEENSIDE. */
export type CastlingRights = number;
/** Bits 12 to 15 of a move. */
export type MoveFlags = number;
/** TRACE = 0 to OFF = 5. */
export type LogLevel = number;

// Color; NO_COLOR stands for both colors
export const WHITE: Color = 0;
export const BLACK: Color = 1;
export const NO_COLOR: Color = 2;

// PieceType
export const PAWN: PieceType = 0;
export const KNIGHT: PieceType = 1;
export const BISHOP: PieceType = 2;
export const ROOK: PieceType = 3;
export const QUEEN: PieceType = 4;
export const KING: PieceType = 5;
export const NO_PIECE_TYPE: PieceType = 6;

// Piece: color * 6 + piece type
export const WHITE_PAWN: Piece = 0;
export const WHITE_KNIGHT: Piece = 1;
export const WHITE_BISHOP: Piece = 2;
export const WHITE_ROOK: Piece = 3;
export const WHITE_QUEEN: Piece = 4;
export const WHITE_KING: Piece = 5;
export const BLACK_PAWN: Piece = 6;
export const BLACK_KNIGHT: Piece = 7;
export const BLACK_BISHOP: Piece = 8;
export const BLACK_ROOK: Piece = 9;
export const BLACK_QUEEN: Piece = 10;
export const BLACK_KING: Piece = 11;
export const NO_PIECE: Piece = 12;

// Square: rank * 8 + file
export const A1: Square = 0;
export const B1: Square = 1;
export const C1: Square = 2;
export const D1: Square = 3;
export const E1: Square = 4;
export const F1: Square = 5;
export const G1: Square = 6;
export const H1: Square = 7;
export const A2: Square = 8;
export const B2: Square = 9;
export const C2: Square = 10;
export const D2: Square = 11;
export const E2: Square = 12;
export const F2: Square = 13;
export const G2: Square = 14;
export const H2: Square = 15;
export const A3: Square = 16;
export const B3: Square = 17;
export const C3: Square = 18;
export const D3: Square = 19;
export const E3: Square = 20;
export const F3: Square = 21;
export const G3: Square = 22;
export const H3: Square = 23;
export const A4: Square = 24;
export const B4: Square = 25;
export const C4: Square = 26;
export const D4: Square = 27;
export const E4: Square = 28;
export const F4: Square = 29;
export const G4: Square = 30;
export const H4: Square = 31;
export const A5: Square = 32;
export const B5: Square = 33;
export const C5: Square = 34;
export const D5: Square = 35;
export const E5: Square = 36;
export const F5: Square = 37;
export const G5: Square = 38;
export const H5: Square = 39;
export const A6: Square = 40;
export const B6: Square = 41;
export const C6: Square = 42;
export const D6: Square = 43;
export const E6: Square = 44;
export const F6: Square = 45;
export const G6: Square = 46;
export const H6: Square = 47;
export const A7: Square = 48;
export const B7: Square = 49;
export const C7: Square = 50;
export const D7: Square = 51;
export const E7: Square = 52;
export const F7: Square = 53;
export const G7: Square = 54;
export const H7: Square = 55;
export const A8: Square = 56;
export const B8: Square = 57;
export const C8: Square = 58;
export const D8: Square = 59;
export const E8: Square = 60;
export const F8: Square = 61;
export const G8: Square = 62;
export const H8: Square = 63;
export const NO_SQUARE: Square = 64;

// CastlingRights: bit mask
export const WHITE_KINGSIDE: CastlingRights = 1;
export const WHITE_QUEENSIDE: CastlingRights = 2;
export const BLACK_KINGSIDE: CastlingRights = 4;
export const BLACK_QUEENSIDE: CastlingRights = 8;
export const NO_CASTLING: CastlingRights = 0;
export const ALL_CASTLING: CastlingRights = 15;

// MoveFlags: bits 12 to 15 of a move
export const QUIET: MoveFlags = 0;
export const DOUBLE_PAWN_PUSH: MoveFlags = 1;
export const KING_CASTLE: MoveFlags = 2;
export const QUEEN_CASTLE: MoveFlags = 3;
export const CAPTURE: MoveFlags = 4;
export const EN_PASSANT: MoveFlags = 5;
export const PROMOTION_KNIGHT: MoveFlags = 8;
export const PROMOTION_BISHOP: MoveFlags = 9;
export const PROMOTION_ROOK: MoveFlags = 10;
export const PROMOTION_QUEEN: MoveFlags = 11;
export const PROMOTION_CAPTURE_KNIGHT: MoveFlags = 12;
export const PROMOTION_CAPTURE_BISHOP: MoveFlags = 13;
export const PROMOTION_CAPTURE_ROOK: MoveFlags = 14;
export const PROMOTION_CAPTURE_QUEEN: MoveFlags = 15;

// LogLevel
export const TRACE: LogLevel = 0;
export const DEBUG: LogLevel = 1;
export const INFO: LogLevel = 2;
export const WARN: LogLevel = 3;
export const ERROR: LogLevel = 4;
export const OFF: LogLevel = 5;
