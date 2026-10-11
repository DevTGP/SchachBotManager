import type {
  Tournament,
  TournamentFormat,
  TournamentRequest,
  TournamentTiebreak,
} from "../../api/types";
import {
  DEFAULT_RECURRENCE_FORM,
  type RecurrenceForm,
  recurrenceForm,
  recurrenceRequest,
} from "./recurrenceForm";

export const FORMATS: TournamentFormat[] = ["round_robin", "swiss", "knockout"];

export const TOURNAMENT_TIEBREAKS: TournamentTiebreak[] = [
  "buchholz",
  "wins",
  "head_to_head",
  "sonneborn_berger",
  "fewer_moves",
];

/** The tiebreaks the API takes when none are given, by format (E177). */
export const DEFAULT_TIEBREAKS: Record<TournamentFormat, TournamentTiebreak[]> = {
  round_robin: ["wins", "head_to_head", "sonneborn_berger"],
  swiss: ["buchholz", "sonneborn_berger", "wins"],
  knockout: [],
};

/**
 * The tournament form as typed; the API checks the ranges (E172). Fields of other formats are
 * kept and sent too, so switching back keeps them.
 */
export interface TournamentForm {
  name: string;
  disciplineId: string;
  format: TournamentFormat;
  gamesPerPairing: string;
  rounds: string;
  tiebreaks: TournamentTiebreak[];
  /** "" for the tournament's own discipline. */
  tiebreakDisciplineId: string;
  tiebreakPairs: string;
  minParticipants: string;
  priority: string;
  recurrence: RecurrenceForm;
}

/** The defaults of the API (E172). */
export const DEFAULT_TOURNAMENT_FORM: TournamentForm = {
  name: "",
  disciplineId: "",
  format: "round_robin",
  gamesPerPairing: "2",
  rounds: "5",
  tiebreaks: DEFAULT_TIEBREAKS.round_robin,
  tiebreakDisciplineId: "",
  tiebreakPairs: "1",
  minParticipants: "2",
  priority: "40",
  recurrence: DEFAULT_RECURRENCE_FORM,
};

/** Another format brings its default tiebreaks along. */
export function withFormat(form: TournamentForm, format: TournamentFormat): TournamentForm {
  return { ...form, format, tiebreaks: DEFAULT_TIEBREAKS[format] };
}

export function tournamentForm(tournament: Tournament): TournamentForm {
  return {
    name: tournament.name,
    disciplineId: tournament.discipline_id,
    format: tournament.format,
    gamesPerPairing: String(tournament.games_per_pairing),
    rounds: String(tournament.rounds),
    tiebreaks: tournament.tiebreaks,
    tiebreakDisciplineId: tournament.tiebreak_discipline_id ?? "",
    tiebreakPairs: String(tournament.tiebreak_pairs),
    minParticipants: String(tournament.min_participants),
    priority: String(tournament.priority),
    recurrence: recurrenceForm(tournament.recurrence),
  };
}

export function tournamentRequest(form: TournamentForm): TournamentRequest {
  return {
    name: form.name,
    discipline_id: form.disciplineId,
    format: form.format,
    games_per_pairing: Number(form.gamesPerPairing),
    rounds: Number(form.rounds),
    tiebreaks: form.tiebreaks,
    tiebreak_discipline_id: form.tiebreakDisciplineId || null,
    tiebreak_pairs: Number(form.tiebreakPairs),
    min_participants: Number(form.minParticipants),
    priority: Number(form.priority),
    recurrence: recurrenceRequest(form.recurrence),
  };
}
