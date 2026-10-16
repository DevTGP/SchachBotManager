// Tries to run code from strings or WebAssembly; exits with 42 if it can (E207).
import * as sbm from "schachbotmanager";

function evaluates(attempt) {
  try {
    return attempt() === 2;
  } catch {
    return false;
  }
}

const ATTEMPTS = [
  () => eval("1 + 1"),
  () => new Function("return 1 + 1")(),
  () => (0, eval)("1 + 1"),
  () => (typeof WebAssembly === "undefined" ? 0 : 2),
];

class Codegen extends sbm.Bot {
  chooseMove(board) {
    if (ATTEMPTS.some(evaluates)) {
      process.exit(42);
    }
    return board.legalMoves()[0];
  }
}

if (import.meta.main) {
  await sbm.run(Codegen);
}
