import { useTranslation } from "react-i18next";
import { Link } from "react-router";

const PAGES = [
  ["/matches", "nav.matches"],
  ["/ratings", "nav.ratings"],
  ["/play", "nav.play"],
  ["/", "nav.start"],
] as const;

/** Where to go from a page with nothing to show: the public parts of the site (G11). */
export function ExploreLinks() {
  const { t } = useTranslation();
  return (
    <nav aria-label={t("explore.label")}>
      <ul className="explore-links">
        {PAGES.map(([path, key]) => (
          <li key={path}>
            <Link to={path}>{t(key)}</Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
