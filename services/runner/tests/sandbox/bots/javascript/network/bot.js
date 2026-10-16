// Tries to reach anything over a socket; exits with 42 if it gets through (sandbox.md).
import { connect } from "node:net";

import * as sbm from "schachbotmanager";

const TARGETS = [
  { host: "1.1.1.1", port: 53 },
  { host: "127.0.0.1", port: 47123 },
  { host: "2606:4700:4700::1111", port: 53 },
  { path: "/var/run/docker.sock" },
];

function reachable(target) {
  return new Promise((resolve) => {
    const socket = connect({ ...target, timeout: 2000 });
    socket.on("connect", () => {
      socket.destroy();
      resolve(true);
    });
    socket.on("error", () => resolve(false));
    socket.on("timeout", () => {
      socket.destroy();
      resolve(false);
    });
  });
}

class Network extends sbm.Bot {
  async chooseMove(board) {
    const results = await Promise.all(TARGETS.map(reachable));
    if (results.some(Boolean)) {
      process.exit(42);
    }
    return board.legalMoves()[0];
  }
}

if (import.meta.main) {
  await sbm.run(Network);
}
