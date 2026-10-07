import { createContext, useContext } from "react";

import type { CurrentUser } from "../api/types";

export interface Session {
  /** null for guests; undefined while the first answer is outstanding. */
  user: CurrentUser | null | undefined;
  /** After a login, logout or redeemed link. */
  setUser: (user: CurrentUser | null) => void;
}

export const SessionContext = createContext<Session>({
  user: null,
  setUser: () => undefined,
});

export function useSession(): Session {
  return useContext(SessionContext);
}
