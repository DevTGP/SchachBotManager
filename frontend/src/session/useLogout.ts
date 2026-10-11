import { startTransition } from "react";
import { useNavigate } from "react-router";

import { logout } from "../api/account";
import { useSubmit } from "../hooks/useSubmit";
import { useSession } from "./sessionContext";

/** Ends the session and goes to the start page (E83); the account nav offers it (G7). */
export function useLogout() {
  const { setUser } = useSession();
  const navigate = useNavigate();
  const { pending, error, submit } = useSubmit();

  function leave() {
    void submit(async () => {
      await logout();
      // The router renders navigations as transitions; clearing the user in one as well
      // keeps a protected page from seeing a guest and sending them to the login first.
      await navigate("/", { replace: true });
      startTransition(() => setUser(null));
    });
  }

  return { pending, error, leave };
}
