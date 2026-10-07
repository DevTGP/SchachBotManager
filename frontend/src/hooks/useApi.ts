import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "../api/client";

export interface ApiState<T> {
  data: T | undefined;
  error: ApiError | undefined;
  loading: boolean;
}

/** A fixed interval, or one that depends on the loaded data (for example only while a match runs). */
export type PollInterval<T> = number | undefined | ((data: T | undefined) => number | undefined);

/**
 * Loads data for `key` and, with an interval, reloads it while the page is open. Data stays
 * visible while a reload runs or fails, so a running match does not flicker.
 */
export function useApi<T>(
  load: (signal: AbortSignal) => Promise<T>,
  key: string,
  poll?: PollInterval<T>,
): ApiState<T> {
  const [state, setState] = useState<ApiState<T> & { key: string }>({
    data: undefined,
    error: undefined,
    loading: true,
    key,
  });
  const loadRef = useRef(load);
  useEffect(() => {
    loadRef.current = load;
  });

  const current = state.key === key ? state.data : undefined;
  const interval = typeof poll === "function" ? poll(current) : poll;

  const run = useCallback(
    async (signal: AbortSignal) => {
      try {
        const data = await loadRef.current(signal);
        if (!signal.aborted) setState({ data, error: undefined, loading: false, key });
      } catch (error) {
        if (signal.aborted) return;
        const failure =
          error instanceof ApiError ? error : new ApiError("network", 0, String(error));
        setState((previous) => ({
          data: previous.key === key ? previous.data : undefined,
          error: failure,
          loading: false,
          key,
        }));
      }
    },
    [key],
  );

  // Loads once per key; a later interval only adds the reloads.
  useEffect(() => {
    const controller = new AbortController();
    void run(controller.signal);
    return () => controller.abort();
  }, [run]);

  useEffect(() => {
    if (!interval) return;
    const controller = new AbortController();
    const timer = window.setInterval(() => void run(controller.signal), interval);
    return () => {
      controller.abort();
      window.clearInterval(timer);
    };
  }, [run, interval]);

  // A new key shows nothing until its data arrives, not the data of the previous key.
  if (state.key !== key) return { data: undefined, error: undefined, loading: true };
  return { data: state.data, error: state.error, loading: state.loading };
}
