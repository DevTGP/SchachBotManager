import { useTranslation } from "react-i18next";
import { NavLink } from "react-router";

import { useSession } from "../session/sessionContext";

/** Login for guests; upload, account and, for admins, the admin pages once logged in. */
export function AccountNav() {
  const { t } = useTranslation();
  const { user } = useSession();
  if (user === undefined) return null;
  if (user === null) {
    return (
      <nav className="account-nav" aria-label={t("nav.account")}>
        <NavLink to="/login">{t("nav.login")}</NavLink>
      </nav>
    );
  }
  return (
    <nav className="account-nav" aria-label={t("nav.account")}>
      <NavLink to="/bots/new">{t("nav.upload")}</NavLink>
      {user.role === "admin" && <NavLink to="/admin">{t("nav.admin")}</NavLink>}
      <NavLink to="/account">{user.username}</NavLink>
    </nav>
  );
}
