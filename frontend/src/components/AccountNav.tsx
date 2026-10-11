import { useState } from "react";
import { useTranslation } from "react-i18next";
import { NavLink, useMatch } from "react-router";

import { useSession } from "../session/sessionContext";
import { useLogout } from "../session/useLogout";
import { FormError } from "./FormError";

/**
 * Login for guests; own bots (not for players), admin pages, the account and logging out for
 * users (G7). On phones the links fold into a menu behind the user name (M1).
 */
export function AccountNav() {
  const { t } = useTranslation();
  const { user } = useSession();
  const [open, setOpen] = useState(false);
  // Uploading belongs to the own bots (U8).
  const uploading = useMatch("/bots/new") !== null;
  const { pending, error, leave } = useLogout();
  if (user === undefined) return null;
  if (user === null) {
    return (
      <nav className="account-nav" aria-label={t("nav.account")}>
        <NavLink to="/login">{t("nav.login")}</NavLink>
      </nav>
    );
  }
  return (
    <div className="account-menu">
      <button
        type="button"
        className="account-toggle"
        aria-expanded={open}
        aria-controls="account-nav"
        onClick={() => setOpen(!open)}
      >
        {user.username}
      </button>
      <nav
        id="account-nav"
        className={open ? "account-nav open" : "account-nav"}
        aria-label={t("nav.account")}
        onClick={() => setOpen(false)}
      >
        {user.role !== "player" && (
          <NavLink
            to="/account/bots"
            className={({ isActive }) => (isActive || uploading ? "active" : undefined)}
          >
            {t("nav.ownBots")}
          </NavLink>
        )}
        {user.role === "admin" && <NavLink to="/admin">{t("nav.admin")}</NavLink>}
        <NavLink to="/account" end>
          {user.username}
        </NavLink>
        <button type="button" className="link" onClick={leave} disabled={pending}>
          {t("account.logout")}
        </button>
        <FormError error={error} />
      </nav>
    </div>
  );
}
