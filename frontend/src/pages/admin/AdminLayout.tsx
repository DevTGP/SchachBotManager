import { useTranslation } from "react-i18next";
import { NavLink, Outlet } from "react-router";

import { RequireRole } from "../../session/RequireRole";

const SECTIONS = [
  { to: "/admin", key: "admin.matches", end: true },
  { to: "/admin/users", key: "admin.users", end: false },
  { to: "/admin/invites", key: "admin.invites", end: false },
  { to: "/admin/disciplines", key: "admin.disciplines", end: false },
  { to: "/admin/play", key: "admin.play", end: false },
  { to: "/admin/audit", key: "admin.audit", end: false },
] as const;

/** The admin pages, only for admins; the API checks the role again on every request (E85). */
export function AdminLayout() {
  const { t } = useTranslation();
  return (
    <RequireRole role="admin">
      <h1>{t("admin.title")}</h1>
      <nav className="tabs" aria-label={t("admin.title")}>
        {SECTIONS.map(({ to, key, end }) => (
          <NavLink key={to} to={to} end={end}>
            {t(key)}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </RequireRole>
  );
}
