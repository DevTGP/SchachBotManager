import type { League, LeagueRequest, Tiebreak } from "../../api/types";

export const TIEBREAKS: Tiebreak[] = ["wins", "head_to_head", "sonneborn_berger", "fewer_moves"];

/** The league form as typed; the API checks the ranges and the promotions (E131). */
export interface LeagueForm {
  name: string;
  disciplineId: string;
  tiers: string;
  tierSize: string;
  gamesPerPairing: string;
  promotions: string;
  win: string;
  draw: string;
  loss: string;
  tiebreaks: Tiebreak[];
  minParticipants: string;
  pauseMinutes: string;
  priority: string;
}

/** The defaults of the API (E131). */
export const DEFAULT_LEAGUE_FORM: LeagueForm = {
  name: "",
  disciplineId: "",
  tiers: "1",
  tierSize: "10",
  gamesPerPairing: "2",
  promotions: "2",
  win: "1",
  draw: "0.5",
  loss: "0",
  tiebreaks: ["wins", "head_to_head", "sonneborn_berger"],
  minParticipants: "2",
  pauseMinutes: "60",
  priority: "50",
};

export function leagueForm(league: League): LeagueForm {
  return {
    name: league.name,
    disciplineId: league.discipline_id,
    tiers: String(league.tiers),
    tierSize: String(league.tier_size),
    gamesPerPairing: String(league.games_per_pairing),
    promotions: String(league.promotions),
    win: String(league.points.win),
    draw: String(league.points.draw),
    loss: String(league.points.loss),
    tiebreaks: league.tiebreaks,
    minParticipants: String(league.min_participants),
    pauseMinutes: String(league.pause_minutes),
    priority: String(league.priority),
  };
}

export function leagueRequest(form: LeagueForm): LeagueRequest {
  return {
    name: form.name,
    discipline_id: form.disciplineId,
    tiers: Number(form.tiers),
    tier_size: Number(form.tierSize),
    games_per_pairing: Number(form.gamesPerPairing),
    promotions: Number(form.promotions),
    points: { win: Number(form.win), draw: Number(form.draw), loss: Number(form.loss) },
    tiebreaks: form.tiebreaks,
    min_participants: Number(form.minParticipants),
    pause_minutes: Number(form.pauseMinutes),
    priority: Number(form.priority),
  };
}
