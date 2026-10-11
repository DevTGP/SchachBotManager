import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import type { Recurrence, TournamentSettings } from "../../api/types";
import { RecurrenceText } from "../../components/RecurrenceText";

/**
 * The settings of a tournament, or the copy an edition keeps from its start (E172), with the
 * fields of its format only; the calendar belongs to the tournament (E171).
 */
export function TournamentFacts({
  settings,
  discipline,
  tiebreakDiscipline,
  recurrence,
}: {
  settings: TournamentSettings;
  discipline: string;
  /** null: the tiebreak games use the tournament's discipline. */
  tiebreakDiscipline: string | null;
  recurrence?: Recurrence | null;
}) {
  const { t } = useTranslation();
  const rows: [string, ReactNode][] = [
    [t("tournaments.format"), t(`tournamentFormat.${settings.format}`)],
    [t("tournaments.discipline"), discipline],
  ];
  if (settings.format === "knockout") {
    rows.push(
      [t("tournaments.gamesPerDuel"), String(settings.games_per_pairing)],
      [t("tournaments.tiebreakDiscipline"), tiebreakDiscipline ?? t("tournaments.sameDiscipline")],
      [t("tournaments.tiebreakPairs"), String(settings.tiebreak_pairs)],
      [t("tournaments.armageddon"), t("tournaments.armageddonRule")],
    );
  } else {
    if (settings.format === "swiss") {
      rows.push([t("tournaments.rounds"), String(settings.rounds)]);
    } else {
      rows.push([t("tournaments.gamesPerPairing"), String(settings.games_per_pairing)]);
    }
    const tiebreaks = settings.tiebreaks.map((name) => t(`tiebreak.${name}`));
    rows.push([t("tournaments.tiebreaks"), [...tiebreaks, t("tiebreak.lot")].join(", ")]);
  }
  rows.push(
    [t("tournaments.seeding"), t("tournaments.seedingRule")],
    [t("tournaments.minParticipants"), String(settings.min_participants)],
    [t("admin.priority"), String(settings.priority)],
  );
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
