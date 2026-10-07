import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Navigate, useLocation } from "react-router";

import type { Role } from "../api/types";
import { Loading } from "../components/Loading";
import { useSession } from "./sessionContext";

/** Guests go to the login and come back; coders on an admin page are told no. */
export function RequireRole({ role, children }: { role?: Role; children: ReactNode }) {
  const { t } = useTranslation();
  const { user } = useSession();
  const location = useLocation();
  if (user === undefined) return <Loading />;
  if (user === null) {
    const next = location.pathname + location.search;
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace />;
  }
  if (role === "admin" && user.role !== "admin") {
    return (
      <p className="error" role="alert">
        {t("error.forbidden")}
      </p>
    );
  }
  return children;
}
