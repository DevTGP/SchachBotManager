// Errors of the bot API (spec/api/errors.json, E49, E224), all derived from ChessError.

/** Base class of all errors of the bot API; also thrown for internal errors of the core. */
export class ChessError extends Error {
  constructor(message?: string, options?: ErrorOptions) {
    super(message, options);
    this.name = new.target.name;
  }
}

/** A value is outside its range, e.g. a square above 63. */
export class InvalidArgumentError extends ChessError {}

/** A FEN string is malformed or describes an impossible position. */
export class InvalidFenError extends ChessError {}

/** A string is not a move in UCI notation. */
export class InvalidUciError extends ChessError {}

/** A well-formed move is not legal in the current position. */
export class IllegalMoveError extends ChessError {}

/** The operation is not possible in the current state, e.g. undo without history. */
export class InvalidStateError extends ChessError {}

/** loadData found no data file with that name. */
export class DataNotFoundError extends ChessError {}
