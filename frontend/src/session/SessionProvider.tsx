import { type ReactNode, useEffect, useMemo, useState } from "react";

import { fetchSession } from "../api/account";
import type { CurrentUser } from "../api/types";
import { SessionContext } from "./sessionContext";

/** Asks the API once who is logged in; the session cookie itself is HttpOnly (E84). */
export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null | undefined>(undefined);

  useEffect(() => {
    const controller = new AbortController();
    fetchSession(controller.signal).then(
      (current) => setUser(current),
      () => {
        // Unreachable API: the pages show that themselves; until then it is a guest.
        if (!controller.signal.aborted) setUser(null);
      },
    );
    return () => controller.abort();
  }, []);

  const session = useMemo(() => ({ user, setUser }), [user]);
  return <SessionContext value={session}>{children}</SessionContext>;
}
