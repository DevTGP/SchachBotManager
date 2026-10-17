// Imports a module the analysis does not allow; it must find it (E228).
import * as sbm from "schachbotmanager";
import { hostname } from "node:os";

class Forbidden extends sbm.Bot {
  chooseMove(board) {
    hostname();
    return board.legalMoves()[0];
  }
}

if (import.meta.main) {
  await sbm.run(Forbidden);
}
