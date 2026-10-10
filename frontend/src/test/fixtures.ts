import type {
  Bot,
  BotDetail,
  CurrentUser,
  Match,
  MatchSummary,
  Move,
  Queue,
  StoredDiscipline,
  User,
} from "../api/types";

export const START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

const BLITZ = {
  name: "blitz",
  initial_time_ms: 180_000,
  increment_ms: 2_000,
  startup_ms: 10_000,
  tolerance_ms: 500,
  max_moves: 500,
  discipline_id: null,
};

function move(ply: number, uci: string, san: string, fen: string, clock: number): Move {
  return { ply, uci, san, fen, spent_ms: 1_500 * ply, clock_ms: clock, info: null };
}

export const OPENING: Move[] = [
  {
    ...move(1, "e2e4", "e4", "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1", 179_000),
    info: { depth: 4, score_cp: 35, nodes: 12_345, pv: ["e2e4", "e7e5"] },
  },
  {
    ...move(
      2,
      "e7e5",
      "e5",
      "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
      178_000,
    ),
    info: { score_cp: 20, text: "book" },
  },
  move(3, "g1f3", "Nf3", "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2", 176_500),
];

export function side(name: string, botId: string, version: string | null = "1.0.0") {
  return {
    kind: "bot" as const,
    bot_id: botId,
    name,
    version,
    sdk: "python",
    lang: "python",
    rating: null,
  };
}

export function summary(overrides: Partial<MatchSummary> = {}): MatchSummary {
  return {
    id: "665f00000000000000000001",
    type: "single",
    status: "finished",
    white: side("Random", "665f0000000000000000000a"),
    black: side("Material", "665f0000000000000000000b"),
    discipline: BLITZ,
    rated: false,
    result: "0-1",
    termination: "resignation",
    ply_count: 3,
    created_at: "2026-05-01T11:59:00.000Z",
    started_at: "2026-05-01T12:00:00.000Z",
    finished_at: "2026-05-01T12:05:00.000Z",
    ...overrides,
  };
}

export function match(overrides: Partial<Match> = {}): Match {
  return { ...summary(), start_fen: START_FEN, moves: OPENING, ...overrides };
}

export const BOTS: Bot[] = [
  {
    id: "665f0000000000000000000a",
    name: "Random",
    version: "1.0.0",
    language: "python",
    status: "verified",
    builtin: true,
    description: "",
    rating: { value: 2500, games: 0 },
    created_at: "2026-05-01T10:00:00.000Z",
  },
  {
    id: "665f0000000000000000000b",
    name: "Material",
    version: "1.0.0",
    language: "python",
    status: "verified",
    builtin: true,
    description: "",
    rating: { value: 2500, games: 0 },
    created_at: "2026-05-01T10:00:00.000Z",
  },
];

export function queue(overrides: Partial<Queue> = {}): Queue {
  return { paused: false, running: [], waiting: [], waiting_total: 0, ...overrides };
}

export function storedDiscipline(overrides: Partial<StoredDiscipline> = {}): StoredDiscipline {
  return {
    id: "665f0000000000000000d001",
    name: "Blitz",
    initial_time_ms: 180_000,
    increment_ms: 2_000,
    startup_ms: 10_000,
    tolerance_ms: 20,
    max_moves: 500,
    archived: false,
    created_at: "2026-05-01T10:00:00.000Z",
    updated_at: "2026-05-01T10:00:00.000Z",
    ...overrides,
  };
}

export const ADMIN: CurrentUser = {
  id: "665f0000000000000000a001",
  username: "admin",
  role: "admin",
};
export const CODER: CurrentUser = {
  id: "665f0000000000000000a002",
  username: "bob",
  role: "coder",
};

export const PLAYER: CurrentUser = {
  id: "665f0000000000000000a003",
  username: "pat",
  role: "player",
};

export function user(current: CurrentUser, overrides: Partial<User> = {}): User {
  return {
    ...current,
    active: true,
    created_at: "2026-05-01T10:00:00.000Z",
    last_login_at: null,
    ...overrides,
  };
}

export const SHARP_ID = "665f0000000000000000000c";

/** An uploaded bot as its owner sees it, rejected by the static analysis; its only version. */
export function botDetail(overrides: Partial<BotDetail> = {}): BotDetail {
  const bot: Bot = {
    id: SHARP_ID,
    name: "Sharp",
    version: "1.0.0",
    language: "python",
    status: "rejected",
    builtin: false,
    description: "",
    rating: { value: 2500, games: 0 },
    created_at: "2026-05-01T10:00:00.000Z",
  };
  const { details, versions, ...fields } = overrides;
  const shown = { ...bot, ...fields };
  return {
    ...shown,
    versions: versions ?? [shown],
    details:
      details !== undefined
        ? details
        : {
            owner: "bob",
            entry: "bot.py",
            files: [
              { path: "bot.py", kind: "source", size: 1234 },
              { path: "data/book.txt", kind: "data", size: 5 },
            ],
            sdk_version: "0.4.0",
            runtime_version: "3.12.1",
            verified_at: null,
            rejected_at: "2026-05-01T10:01:00.000Z",
            rejection: { stage: "analysis", reason: "1 finding" },
            overridden_at: null,
            recheck_pending: false,
            rechecks: [],
            report: {
              result: "failed",
              ruleset: "python-1",
              runtime: { python: "3.12.1", sdk: "0.4.0" },
              started_at: "2026-05-01T10:00:30.000Z",
              finished_at: "2026-05-01T10:01:00.000Z",
              stages: [
                {
                  stage: "analysis",
                  status: "failed",
                  duration_ms: 1200,
                  problem: "1 finding",
                  findings: [
                    { rule: "import", file: "bot.py", line: 3, message: "socket is not allowed" },
                  ],
                  truncated: false,
                },
              ],
            },
          },
  };
}
