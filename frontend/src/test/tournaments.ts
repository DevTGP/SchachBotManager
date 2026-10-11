import type {
  BotEdition,
  Discipline,
  Duel,
  DuelGame,
  Edition,
  EditionTableRow,
  Tournament,
  TournamentDetail,
  TournamentRegistration,
  TournamentSettings,
} from "../api/types";

export const TOURNAMENT_ID = "665f00000000000000001001";
export const EDITION_ID = "665f00000000000000002001";

const RANDOM = { bot_id: "665f0000000000000000000a", name: "Random", version: "1.0.0" };
const MATERIAL = { bot_id: "665f0000000000000000000b", name: "Material", version: "1.0.0" };
const SHARP = { bot_id: "665f0000000000000000000c", name: "Sharp", version: "1.0.0" };

const BLITZ: Discipline = {
  name: "Blitz",
  initial_time_ms: 180_000,
  increment_ms: 2_000,
  startup_ms: 10_000,
  tolerance_ms: 20,
  max_moves: 500,
  discipline_id: "665f0000000000000000d001",
};

export function tournament(overrides: Partial<Tournament> = {}): Tournament {
  return {
    id: TOURNAMENT_ID,
    name: "Herbstcup",
    discipline_name: "Blitz",
    discipline_id: "665f0000000000000000d001",
    format: "round_robin",
    games_per_pairing: 2,
    rounds: 5,
    tiebreaks: ["wins", "head_to_head", "sonneborn_berger"],
    tiebreak_discipline_id: null,
    tiebreak_pairs: 1,
    min_participants: 2,
    priority: 40,
    tiebreak_discipline_name: null,
    recurrence: null,
    archived: false,
    registered: 1,
    edition: {
      id: EDITION_ID,
      number: 1,
      status: "planned",
      starts_after: null,
      participants: 0,
      winner: null,
      started_at: null,
      finished_at: null,
    },
    created_at: "2026-05-01T10:00:00.000Z",
    updated_at: "2026-05-01T10:00:00.000Z",
    ...overrides,
  };
}

export function tournamentRegistration(
  overrides: Partial<TournamentRegistration> = {},
): TournamentRegistration {
  return {
    tournament_id: TOURNAMENT_ID,
    tournament_name: "Herbstcup",
    bot: RANDOM,
    created_at: "2026-05-01T10:00:00.000Z",
    playing: false,
    ...overrides,
  };
}

export function tournamentDetail(overrides: Partial<TournamentDetail> = {}): TournamentDetail {
  const base = tournament();
  return {
    ...base,
    editions: base.edition ? [base.edition] : [],
    registrations: [tournamentRegistration()],
    ...overrides,
  };
}

function settings(overrides: Partial<TournamentSettings>): TournamentSettings {
  const base = tournament();
  return {
    discipline_id: base.discipline_id,
    format: base.format,
    games_per_pairing: base.games_per_pairing,
    rounds: base.rounds,
    tiebreaks: base.tiebreaks,
    tiebreak_discipline_id: null,
    tiebreak_pairs: base.tiebreak_pairs,
    min_participants: base.min_participants,
    priority: base.priority,
    ...overrides,
  };
}

function row(bot: typeof RANDOM, overrides: Partial<EditionTableRow>): EditionTableRow {
  return {
    bot,
    rank: 1,
    games: 2,
    wins: 1,
    forfeit_wins: 0,
    draws: 0,
    losses: 1,
    byes: 0,
    points: 1,
    buchholz: 0,
    withdrawn: false,
    ...overrides,
  };
}

function edition(overrides: Partial<Edition>): Edition {
  return {
    id: EDITION_ID,
    tournament_id: TOURNAMENT_ID,
    tournament_name: "Herbstcup",
    number: 1,
    status: "running",
    starts_after: "2026-05-01T10:00:00.000Z",
    started_at: "2026-05-01T10:00:00.000Z",
    finished_at: null,
    settings: settings({}),
    discipline: BLITZ,
    tiebreak_discipline: null,
    participants: [
      { bot: MATERIAL, seed: 1, rating: 1650, withdrawn: false },
      { bot: SHARP, seed: 2, rating: 1500, withdrawn: false },
      { bot: RANDOM, seed: 3, rating: 1200, withdrawn: true },
    ],
    round: 2,
    games: 4,
    finished: 3,
    table: [],
    bracket_size: null,
    bracket: [],
    placements: [],
    ...overrides,
  };
}

/** A running Swiss edition after two rounds: Material leads, Sharp had a bye, Random left. */
export function swissEdition(): Edition {
  return edition({
    settings: settings({ format: "swiss", rounds: 3, tiebreaks: ["buchholz", "wins"] }),
    table: [
      row(MATERIAL, { rank: 1, wins: 2, losses: 0, points: 2, buchholz: 1.5 }),
      row(SHARP, { rank: 2, games: 1, wins: 0, losses: 1, byes: 1, points: 1, buchholz: 2 }),
      row(RANDOM, { rank: null, wins: 0, forfeit_wins: 0, losses: 2, points: 0, withdrawn: true }),
    ],
  });
}

function duelGame(overrides: Partial<DuelGame>): DuelGame {
  return {
    match_id: "k1",
    phase: "regular",
    game: 1,
    white: MATERIAL,
    black: SHARP,
    status: "finished",
    result: "1/2-1/2",
    termination: "max_moves",
    ...overrides,
  };
}

function duel(overrides: Partial<Duel>): Duel {
  return {
    round: 1,
    slot: 1,
    a: { bot: MATERIAL, seed: 1, points: 0.5, tiebreak_points: 1 },
    b: { bot: SHARP, seed: 2, points: 0.5, tiebreak_points: 0 },
    winner: MATERIAL.bot_id,
    decided: true,
    decided_by: "tiebreak",
    games: [
      duelGame({}),
      duelGame({
        match_id: "k2",
        phase: "tiebreak",
        game: 1,
        result: "1-0",
        termination: "checkmate",
      }),
    ],
    ...overrides,
  };
}

/** A finished knockout of two bots: Material won the final after a tiebreak. */
export function knockoutEdition(): Edition {
  return edition({
    status: "finished",
    finished_at: "2026-05-02T10:00:00.000Z",
    settings: settings({ format: "knockout", games_per_pairing: 1, tiebreaks: [] }),
    tiebreak_discipline: { ...BLITZ, name: "Bullet", initial_time_ms: 60_000, increment_ms: 0 },
    participants: [
      { bot: MATERIAL, seed: 1, rating: 1650, withdrawn: false },
      { bot: SHARP, seed: 2, rating: 1500, withdrawn: false },
    ],
    round: 1,
    games: 2,
    finished: 2,
    bracket_size: 2,
    bracket: [duel({})],
    placements: [
      { bot: MATERIAL, place: 1, withdrawn: false },
      { bot: SHARP, place: 2, withdrawn: false },
    ],
  });
}

export function botEdition(overrides: Partial<BotEdition> = {}): BotEdition {
  return {
    edition_id: EDITION_ID,
    tournament_id: TOURNAMENT_ID,
    tournament_name: "Herbstcup",
    number: 1,
    format: "knockout",
    status: "finished",
    started_at: "2026-05-01T10:00:00.000Z",
    finished_at: "2026-05-02T10:00:00.000Z",
    seed: 2,
    participants: 8,
    place: 2,
    points: null,
    withdrawn: false,
    ...overrides,
  };
}
