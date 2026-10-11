import type {
  BotSeason,
  League,
  LeagueDetail,
  LeagueRegistration,
  ScheduleGame,
  Season,
  SeasonSchedule,
  TableRow,
} from "../api/types";

export const LEAGUE_ID = "665f0000000000000000e001";
export const SEASON_ID = "665f0000000000000000f001";

export function league(overrides: Partial<League> = {}): League {
  return {
    id: LEAGUE_ID,
    name: "Bundesliga",
    discipline_name: "Blitz",
    discipline_id: "665f0000000000000000d001",
    tiers: 2,
    tier_size: 4,
    games_per_pairing: 2,
    promotions: 1,
    points: { win: 1, draw: 0.5, loss: 0 },
    tiebreaks: ["wins", "head_to_head"],
    min_participants: 4,
    recurrence: null,
    priority: 50,
    archived: false,
    registered: 1,
    season: {
      id: SEASON_ID,
      number: 1,
      status: "planned",
      starts_after: null,
      participants: 0,
      started_at: null,
      finished_at: null,
    },
    created_at: "2026-05-01T10:00:00.000Z",
    updated_at: "2026-05-01T10:00:00.000Z",
    ...overrides,
  };
}

export function registration(overrides: Partial<LeagueRegistration> = {}): LeagueRegistration {
  return {
    league_id: LEAGUE_ID,
    league_name: "Bundesliga",
    bot: { bot_id: "665f0000000000000000000a", name: "Random", version: "1.0.0" },
    created_at: "2026-05-01T10:00:00.000Z",
    tier: null,
    ...overrides,
  };
}

export function leagueDetail(overrides: Partial<LeagueDetail> = {}): LeagueDetail {
  const base = league();
  return {
    ...base,
    seasons: base.season ? [base.season] : [],
    registrations: [registration()],
    ...overrides,
  };
}

function row(name: string, botId: string, overrides: Partial<TableRow>): TableRow {
  return {
    bot: { bot_id: botId, name, version: "1.0.0" },
    rank: 1,
    games: 2,
    wins: 2,
    forfeit_wins: 0,
    draws: 0,
    losses: 0,
    points: 2,
    withdrawn: false,
    outcome: null,
    ...overrides,
  };
}

/** A finished season of one tier: Material won, Random withdrew. */
export function season(overrides: Partial<Season> = {}): Season {
  const settings: Omit<League, "season"> = league();
  delete (settings as Partial<League>).season;
  return {
    id: SEASON_ID,
    league_id: LEAGUE_ID,
    league_name: "Bundesliga",
    number: 1,
    status: "finished",
    starts_after: "2026-05-01T10:00:00.000Z",
    started_at: "2026-05-01T10:00:00.000Z",
    finished_at: "2026-05-02T10:00:00.000Z",
    settings,
    discipline: {
      name: "Blitz",
      initial_time_ms: 180_000,
      increment_ms: 2_000,
      startup_ms: 10_000,
      tolerance_ms: 20,
      max_moves: 500,
      discipline_id: settings.discipline_id,
    },
    tiers: [
      {
        tier: 1,
        games: 2,
        finished: 2,
        table: [
          row("Material", "665f0000000000000000000b", {
            wins: 2,
            forfeit_wins: 1,
            outcome: "stayed",
          }),
          row("Random", "665f0000000000000000000a", {
            rank: null,
            wins: 0,
            losses: 2,
            points: 0,
            withdrawn: true,
            outcome: "withdrawn",
          }),
        ],
      },
    ],
    ...overrides,
  };
}

const RANDOM = { bot_id: "665f0000000000000000000a", name: "Random", version: "1.0.0" };
const MATERIAL = { bot_id: "665f0000000000000000000b", name: "Material", version: "1.0.0" };

function game(overrides: Partial<ScheduleGame>): ScheduleGame {
  return {
    match_id: "m1",
    board: 1,
    white: MATERIAL,
    black: RANDOM,
    status: "finished",
    result: "1-0",
    termination: "checkmate",
    ...overrides,
  };
}

/** Tier 1 of the season: round 1 is over, one of its games lost by forfeit; round 2 waits. */
export function schedule(): SeasonSchedule {
  return {
    tier: 1,
    rounds: [
      {
        round: 1,
        bye: null,
        games: [game({ match_id: "m1", result: "0-1", termination: "forfeit_withdrawn" })],
      },
      {
        round: 2,
        bye: { bot_id: "665f0000000000000000000c", name: "Sharp", version: "1.0.0" },
        games: [
          game({
            match_id: "m2",
            white: RANDOM,
            black: MATERIAL,
            status: "queued",
            result: null,
            termination: null,
          }),
        ],
      },
    ],
  };
}

export function botSeason(overrides: Partial<BotSeason> = {}): BotSeason {
  return {
    season_id: SEASON_ID,
    league_id: LEAGUE_ID,
    league_name: "Bundesliga",
    number: 1,
    status: "finished",
    started_at: "2026-05-01T10:00:00.000Z",
    finished_at: "2026-05-02T10:00:00.000Z",
    tier: 1,
    rank: 2,
    tier_size: 4,
    games: 6,
    points: 3.5,
    withdrawn: false,
    outcome: "stayed",
    ...overrides,
  };
}
