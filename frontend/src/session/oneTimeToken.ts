import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router";

/**
 * The token of an invite or reset link sits after the # so it stays out of server logs (E83).
 * It is read once and then removed from the address bar and the history.
 */
export function useOneTimeToken(): string {
  const location = useLocation();
  const navigate = useNavigate();
  const [token] = useState(() => location.hash.replace(/^#/, ""));

  useEffect(() => {
    if (location.hash) void navigate(location.pathname, { replace: true });
  }, [location.hash, location.pathname, navigate]);

  return token;
}
