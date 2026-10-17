// Template bot for SchachBotManager: book moves from a data file, then a simple capture rule.
//
// Replace chooseMove with your own search. Start it with
//     node bot.js         talks to a referee over stdin/stdout, as on the server
//     node bot.js --tcp   connects to a waiting sbm-arena, e.g. from the debugger

import * as sbm from "schachbotmanager";

// Centipawns per piece type: PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING.
const PIECE_VALUES = [100, 300, 300, 500, 900, 0];
const MATE = 100_000;

export function pieceValue(piece) {
  // A piece is color * 6 + type, e.g. sbm.BLACK_QUEEN === 6 + sbm.QUEEN.
  return piece === sbm.NO_PIECE ? 0 : PIECE_VALUES[piece % 6];
}

/** The first four FEN fields: pieces, side to move, castling rights, en passant. */
export function positionKey(board) {
  return board.fen().split(" ").slice(0, 4).join(" ");
}

/** Lines "position | uci uci ..." from data/book.txt; # starts a comment. */
export function loadBook() {
  const book = new Map();
  for (const line of new TextDecoder().decode(sbm.loadData("book.txt")).split(/\r?\n/)) {
    if (line.trim() && !line.startsWith("#")) {
      const [position, moves] = line.split("|");
      book.set(position.trim(), moves.trim().split(/\s+/));
    }
  }
  return book;
}

function randomChoice(items) {
  return items[Math.floor(Math.random() * items.length)];
}

export class TemplateBot extends sbm.Bot {
  onGameStart(info) {
    // Runs within the start-up budget: the place to load data and build tables.
    this.book = loadBook();
    const color = info.color === sbm.WHITE ? "White" : "Black";
    sbm.Log.info(`playing ${color} against ${info.opponentName}`);
  }

  chooseMove(board, clock) {
    const bookMoves = this.book.get(positionKey(board)) ?? [];
    if (bookMoves.length > 0) {
      this.report({ text: "book" });
      return board.parseMove(randomChoice(bookMoves));
    }

    const moves = board.legalMoves();
    const scores = new Map(moves.map((move) => [move, this.score(board, move)]));
    const best = Math.max(...scores.values());
    sbm.Log.debug(`${moves.length} moves, best score ${best}, ${clock.remainingMs()} ms left`);
    this.report({ depth: 1, scoreCp: best });
    return randomChoice(moves.filter((move) => scores.get(move) === best));
  }

  /** Value of the captured piece, minus the moved piece if it can be taken back. */
  score(board, move) {
    let gain = pieceValue(board.pieceAt(move.toSquare()));
    const moved = pieceValue(board.pieceAt(move.fromSquare()));
    board.makeMove(move);
    if (board.isCheckmate()) {
      gain = MATE;
    } else if (board.isAttacked(move.toSquare(), board.sideToMove())) {
      gain -= moved;
    }
    board.undoMove();
    return gain;
  }

  onGameEnd(result) {
    sbm.Log.info(`game over: ${result.result} ${result.termination}`);
  }
}

if (import.meta.main) {
  await sbm.run(TemplateBot);
}
