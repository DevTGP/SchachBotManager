import { useCallback, useState } from "react";

import { ApiError } from "../api/client";

export interface Submit {
  pending: boolean;
  /** An API error, or the translation key of a check made in the browser. */
  error: ApiError | string | undefined;
  /** Runs a change once at a time; its error stays until the next run. */
  submit: (action: () => Promise<void>) => Promise<void>;
  fail: (key: string) => void;
}

export function useSubmit(): Submit {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<ApiError | string | undefined>(undefined);

  const submit = useCallback(async (action: () => Promise<void>) => {
    setPending(true);
    setError(undefined);
    try {
      await action();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught : new ApiError("network", 0, String(caught)));
    } finally {
      setPending(false);
    }
  }, []);

  return { pending, error, submit, fail: setError };
}
