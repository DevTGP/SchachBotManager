import { useCallback, useEffect, useRef, useState } from "react";

import {
  joinMessage,
  moveMessage,
  parseServerMessage,
  type PlayState,
  resignMessage,
  SOCKET_PATH,
} from "./protocol";

/**
 * connecting: no answer yet. waiting: the seat is taken, the game has not started. playing and
 * over: a state has come. refused: the gateway turned the seat down. ended: the connection
 * closed before a result, so the game was aborted. lost: no connection for too long.
 */
export type GamePhase =
  "connecting" | "waiting" | "playing" | "over" | "refused" | "ended" | "lost";

export interface PlayGame {
  phase: GamePhase;
  state: PlayState | undefined;
  /** When the state came, for the running clock (Date.now()). */
  receivedAt: number;
  /** The code of the last refused message or refusal. */
  problem: string | undefined;
  move: (uci: string) => void;
  resign: () => void;
}

export type SocketFactory = (url: string) => WebSocket;

const RETRY_MS = [500, 1000, 2000, 4000, 8000];
// The play runner waits 60 s for a client that went away (E113).
const GIVE_UP_MS = 55_000;
const GAME_OVER = 1000;

export function socketUrl(location: Location = window.location): string {
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  return `${scheme}://${location.host}${SOCKET_PATH}`;
}

const browserSocket: SocketFactory = (url) => new WebSocket(url);

/** The connection of one seat, joined again after a drop until the game is over. */
export function usePlayGame(
  matchId: string,
  seat: string,
  createSocket: SocketFactory = browserSocket,
): PlayGame {
  const [phase, setPhase] = useState<GamePhase>("connecting");
  const [state, setState] = useState<PlayState | undefined>(undefined);
  const [receivedAt, setReceivedAt] = useState(0);
  const [problem, setProblem] = useState<string | undefined>(undefined);
  const socketRef = useRef<WebSocket | undefined>(undefined);

  useEffect(() => {
    let stopped = false;
    let finished = false;
    let attempt = 0;
    let lostSince: number | undefined;
    let timer: ReturnType<typeof setTimeout> | undefined;

    function connect() {
      const socket = createSocket(socketUrl());
      socketRef.current = socket;
      socket.onopen = () => socket.send(joinMessage(matchId, seat));
      socket.onmessage = (event) => {
        const message = parseServerMessage(String(event.data));
        if (message === undefined) return;
        attempt = 0;
        lostSince = undefined;
        if (message.type === "joined") {
          setPhase((current) => (current === "connecting" ? "waiting" : current));
        } else if (message.type === "state") {
          finished = message.result !== null;
          setState(message);
          setReceivedAt(Date.now());
          setPhase(finished ? "over" : "playing");
        } else if (message.type === "error") {
          setProblem(message.code);
        } else {
          finished = true;
          setProblem(message.code);
          setPhase("refused");
        }
      };
      socket.onclose = (event) => {
        if (stopped || finished) return;
        if (event.code === GAME_OVER) {
          finished = true;
          setPhase("ended");
          return;
        }
        lostSince ??= Date.now();
        if (Date.now() - lostSince > GIVE_UP_MS) {
          setPhase("lost");
          return;
        }
        const delay = RETRY_MS[Math.min(attempt, RETRY_MS.length - 1)];
        attempt += 1;
        timer = setTimeout(connect, delay);
      };
    }

    connect();
    return () => {
      stopped = true;
      clearTimeout(timer);
      socketRef.current?.close();
    };
  }, [matchId, seat, createSocket]);

  const send = useCallback((text: string) => {
    const socket = socketRef.current;
    if (socket?.readyState === WebSocket.OPEN) socket.send(text);
  }, []);

  const move = useCallback(
    (uci: string) => {
      setProblem(undefined);
      send(moveMessage(uci));
    },
    [send],
  );
  const resign = useCallback(() => send(resignMessage()), [send]);

  return { phase, state, receivedAt, problem, move, resign };
}
