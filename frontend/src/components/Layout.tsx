import { useTranslation } from "react-i18next";
import { Link, NavLink, Outlet } from "react-router";

import { AccountNav } from "./AccountNav";
import { LanguageSwitch } from "./LanguageSwitch";

const NAV = [
  { to: "/", key: "nav.start", end: true },
  { to: "/matches", key: "nav.matches", end: false },
  { to: "/queue", key: "nav.queue", end: false },
  { to: "/bots", key: "nav.bots", end: false },
  { to: "/play", key: "nav.play", end: false },
] as const;

export function Layout() {
  const { t } = useTranslation();
  return (
    <div className="layout">
      <header className="site-header">
        <Link to="/" className="brand">
          {t("app.name")}
        </Link>
        <nav aria-label="main">
          {NAV.map(({ to, key, end }) => (
            <NavLink key={to} to={to} end={end}>
              {t(key)}
            </NavLink>
          ))}
        </nav>
        <AccountNav />
        <LanguageSwitch />
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
