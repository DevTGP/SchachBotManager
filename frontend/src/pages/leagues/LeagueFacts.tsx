import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import type { LeagueSettings, Recurrence } from "../../api/types";
import { RecurrenceText } from "../../components/RecurrenceText";
import { formatPoints } from "../../format/points";

/**
 * The settings of a league, or the copy a season keeps from its start (E131); the calendar
 * belongs to the league only (E171).
 */
export function LeagueFacts({
  settings,
  discipline,
  recurrence,
}: {
  settings: LeagueSettings;
  discipline: string;
  recurrence?: Recurrence | null;
}) {
  const { t } = useTranslation();
  const { win, draw, loss } = settings.points;
  const tiebreaks = settings.tiebreaks.map((name) => t(`tiebreak.${name}`));
  const rows: [string, ReactNode][] = [
    [t("leagues.discipline"), discipline],
    [t("leagues.tiers"), String(settings.tiers)],
    [t("leagues.tierSize"), String(settings.tier_size)],
    [t("leagues.gamesPerPairing"), String(settings.games_per_pairing)],
    [t("leagues.promotions"), String(settings.promotions)],
    [t("leagues.points"), [win, draw, loss].map(formatPoints).join(" / ")],
    [t("leagues.tiebreaks"), [...tiebreaks, t("tiebreak.lot")].join(", ")],
    [t("leagues.minParticipants"), String(settings.min_participants)],
    [t("admin.priority"), String(settings.priority)],
    [t("registration.readyHours"), String(settings.ready_hours)],
  ];
  if (recurrence !== undefined) {
    rows.push([t("recurrence.title"), <RecurrenceText recurrence={recurrence} />]);
  }
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
