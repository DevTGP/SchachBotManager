import { useEffect, useState } from "react";

const TICK_MS = 1_000;

/** The current time in milliseconds, renewed every second for countdowns. */
export function useNow(): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), TICK_MS);
    return () => window.clearInterval(timer);
  }, []);
  return now;
}
