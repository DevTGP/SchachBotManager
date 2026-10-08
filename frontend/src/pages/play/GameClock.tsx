import { useEffect, useState } from "react";

import { formatClock } from "../../format/clock";
import { type PlayColor, type PlayState, remainingMs } from "../../play/protocol";

const TICK_MS = 100;

/** A side's name and clock; the running clock counts down between the server's states. */
export function GameClock({
  state,
  color,
  receivedAt,
}: {
  state: PlayState;
  color: PlayColor;
  receivedAt: number;
}) {
  const running = state.running === color;
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!running) return;
    const timer = setInterval(() => setNow(Date.now()), TICK_MS);
    return () => clearInterval(timer);
  }, [running]);
  const elapsed = running ? Math.max(0, now - receivedAt) : 0;
  return (
    <div className={`player-bar${running ? " to-move" : ""}`} data-testid={`clock-${color}`}>
      <span className={`piece-dot ${color === "white" ? "w" : "b"}`} />
      <span className="player-name">{state[color]}</span>
      <span className="clock" role="timer">
        {formatClock(remainingMs(state, color, elapsed))}
      </span>
    </div>
  );
}
