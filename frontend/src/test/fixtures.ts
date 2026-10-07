import type { Bot, Match, MatchSummary, Move, Queue } from "../api/types";

export const START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

const BLITZ = {
  name: "blitz",
  initial_time_ms: 180_000,
  increment_ms: 2_000,
  startup_ms: 10_000,
  tolerance_ms: 500,
  max_moves: 500,
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

export function side(name: string, botId: string) {
  return { kind: "bot" as const, bot_id: botId, name, sdk: "python", lang: "python" };
}

export function summary(overrides: Partial<MatchSummary> = {}): MatchSummary {
  return {
    id: "665f00000000000000000001",
    type: "single",
    status: "finished",
    white: side("Random", "665f0000000000000000000a"),
    black: side("Material", "665f0000000000000000000b"),
    discipline: BLITZ,
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
    language: "python",
    status: "verified",
    builtin: true,
    created_at: "2026-05-01T10:00:00.000Z",
  },
  {
    id: "665f0000000000000000000b",
    name: "Material",
    language: "python",
    status: "verified",
    builtin: true,
    created_at: "2026-05-01T10:00:00.000Z",
  },
];

export function queue(overrides: Partial<Queue> = {}): Queue {
  return { paused: false, running: [], waiting: [], waiting_total: 0, ...overrides };
}
