import { useTranslation } from "react-i18next";
import { NavLink } from "react-router";

import { useSession } from "../session/sessionContext";

/** Login for guests; own bots (not for players), account and, for admins, the admin pages. */
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
      {user.role !== "player" && <NavLink to="/account/bots">{t("nav.ownBots")}</NavLink>}
      {user.role === "admin" && <NavLink to="/admin">{t("nav.admin")}</NavLink>}
      <NavLink to="/account" end>
        {user.username}
      </NavLink>
    </nav>
  );
}
