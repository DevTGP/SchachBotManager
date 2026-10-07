import { useCallback, useEffect, useState } from "react";

import type { Move } from "../api/types";
import { playbackDelay, type Speed } from "./playback";

export interface Playback {
  playing: boolean;
  speed: Speed;
  setSpeed: (speed: Speed) => void;
  toggle: () => void;
}

/** Steps through the moves; playing from the last move starts again at the beginning. */
export function usePlayback(moves: Move[], ply: number, goTo: (ply: number) => void): Playback {
  const [wanted, setWanted] = useState(false);
  const [speed, setSpeed] = useState<Speed>(1);
  const total = moves.length;
  const playing = wanted && ply < total;
  const delay = playbackDelay(speed, moves[ply]);

  useEffect(() => {
    if (!playing) return;
    const timer = window.setTimeout(() => {
      goTo(ply + 1);
      // Playback stops at the last move; a running match is watched with "follow live" instead.
      if (ply + 1 >= total) setWanted(false);
    }, delay);
    return () => window.clearTimeout(timer);
  }, [playing, ply, total, delay, goTo]);

  const toggle = useCallback(() => {
    if (playing) {
      setWanted(false);
      return;
    }
    if (ply >= total) goTo(0);
    setWanted(true);
  }, [playing, ply, total, goTo]);

  return { playing, speed, setSpeed, toggle };
}
