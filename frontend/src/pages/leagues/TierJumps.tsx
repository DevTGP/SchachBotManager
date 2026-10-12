import { useTranslation } from "react-i18next";

import type { SeasonTier } from "../../api/types";
import { tierAnchor } from "../../format/anchors";

/** Jumps to the tiers of a season with more than one (E188). */
export function TierJumps({ tiers }: { tiers: SeasonTier[] }) {
  const { t } = useTranslation();
  if (tiers.length < 2) return null;
  return (
    <nav className="jump-links" aria-label={t("seasons.tiers")}>
      {tiers.map((tier) => (
        <a key={tier.tier} href={`#${tierAnchor(tier.tier)}`}>
          {t("seasons.tier", { tier: tier.tier })}
        </a>
      ))}
    </nav>
  );
}
