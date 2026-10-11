import { useTranslation } from "react-i18next";

import type { LeagueSettings } from "../../api/types";
import { formatPoints } from "../../format/points";

/** The settings of a league, or the copy a season keeps from its start (E131). */
export function LeagueFacts({
  settings,
  discipline,
}: {
  settings: LeagueSettings;
  discipline: string;
}) {
  const { t } = useTranslation();
  const { win, draw, loss } = settings.points;
  const tiebreaks = settings.tiebreaks.map((name) => t(`tiebreak.${name}`));
  const rows: [string, string][] = [
    [t("leagues.discipline"), discipline],
    [t("leagues.tiers"), String(settings.tiers)],
    [t("leagues.tierSize"), String(settings.tier_size)],
    [t("leagues.gamesPerPairing"), String(settings.games_per_pairing)],
    [t("leagues.promotions"), String(settings.promotions)],
    [t("leagues.points"), [win, draw, loss].map(formatPoints).join(" / ")],
    [t("leagues.tiebreaks"), [...tiebreaks, t("tiebreak.lot")].join(", ")],
    [t("leagues.minParticipants"), String(settings.min_participants)],
    [t("leagues.pauseMinutes"), String(settings.pause_minutes)],
    [t("admin.priority"), String(settings.priority)],
  ];
  return (
    <dl className="details">
      {rows.map(([term, value]) => (
        <div key={term}>
          <dt>{term}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
