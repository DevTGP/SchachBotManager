// An uploaded bot as the verification sees it: an own module and a data file (E94, E227).
import * as sbm from "schachbotmanager";

import { firstMove } from "./opening.js";

class Uploaded extends sbm.Bot {
  onGameStart() {
    this.book = new TextDecoder().decode(sbm.loadData("book.txt")).split(/\s+/);
  }

  chooseMove(board) {
    return firstMove(board, this.book);
  }
}

if (import.meta.main) {
  await sbm.run(Uploaded);
}
