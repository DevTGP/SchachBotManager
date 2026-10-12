import { act, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { CompetitionGame, MatchSummary, Readiness } from "../api/types";
import { loadSeat, saveSeat } from "../play/seats";
import { FakeSocket } from "../test/fakeSocket";
import { BOTS, PLAYER, START_FEN, side, summary } from "../test/fixtures";
import { mockApi, renderRoute } from "../test/render";

const MATCH_ID = "665f00000000000000000f02";
const SEAT = "Xq3v7dK2mP9sL1wR8tY4uB6nC0eF5gH2jA7kZ3xQ_-M";
const DEADLINE = "2026-05-03T12:00:00.000Z";

function readiness(overrides: Partial<Readiness> = {}): Readiness {
  return {
    released_at: "2026-05-01T12:00:00.000Z",
    deadline: DEADLINE,
    started_at: null,
    white: { ready: false, present: false },
    black: null,
    ...overrides,
  };
}

/** A league game of pat with White against Material. */
function game(
  overrides: Partial<MatchSummary> = {},
  estimatedStart: string | null = null,
): CompetitionGame {
  return {
    color: "white",
    estimated_start: estimatedStart,
    match: summary({
      id: MATCH_ID,
      type: "league",
      status: "queued",
      white: { ...side("pat", "", null), kind: "human", bot_id: null, sdk: null, lang: null },
      black: side("Material", BOTS[1]!.id),
      rated: true,
      result: null,
      termination: null,
      ply_count: 0,
      started_at: null,
      finished_at: null,
      league: {
        league_id: "665f0000000000000000e001",
        league_name: "Bundesliga",
        season_id: "665f0000000000000000f001",
        season_number: 2,
        tier: 1,
        round: 1,
        board: 1,
      },
      readiness: readiness(),
      ...overrides,
    }),
  };
}

beforeEach(() => {
  FakeSocket.instances = [];
  vi.stubGlobal("WebSocket", FakeSocket);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("own competition games", () => {
  it("lists them on /play with their state", async () => {
    mockApi({
      "/session": { user: PLAYER },
      "/bots": { items: BOTS },
      "/disciplines": { items: [] },
      "/account/competition-games": {
        items: [game(), { ...game({ id: "665f00000000000000000f03", readiness: null }) }],
      },
    });
    renderRoute("/play");

    const heading = await screen.findByRole("heading", {
      name: "Your league and tournament games",
    });
    const table = heading.parentElement!.querySelector("table")!;
    const [released, waiting] = within(table).getAllByRole("row").slice(1);
    expect(released).toHaveTextContent("Bundesliga, Season 2");
    expect(released).toHaveTextContent("Material");
    expect(released).toHaveTextContent(/ready by/);
    expect(within(released!).getByRole("link", { name: "Open" })).toHaveAttribute(
      "href",
      `/play/${MATCH_ID}`,
    );
    expect(waiting).toHaveTextContent("not released yet");
  });

  it("shows no list without an account", async () => {
    const api = mockApi({
      "/session": { user: null },
      "/bots": { items: BOTS },
      "/disciplines": { items: [] },
    });
    renderRoute("/play");

    await screen.findByRole("combobox", { name: "Bot" });
    expect(screen.queryByRole("heading", { name: "Your league and tournament games" })).toBeNull();
    const paths = api.calls.map((call) => call.url.pathname);
    expect(paths).not.toContain("/api/v1/account/competition-games");
  });
});

describe("ready for a competition game", () => {
  it("says ready, keeps the seat and plays once the game started", async () => {
    const user = userEvent.setup();
    let started = false;
    const api = mockApi({
      "/session": { user: PLAYER },
      "/account/competition-games": () => ({
        items: [
          started
            ? game({ status: "running", readiness: readiness({ started_at: DEADLINE }) })
            : game(),
        ],
      }),
      [`/matches/${MATCH_ID}/ready`]: () => {
        started = true;
        return {
          match_id: MATCH_ID,
          seat: SEAT,
          color: "white",
          socket_path: "/api/v1/play/socket",
        };
      },
    });
    renderRoute(`/play/${MATCH_ID}`);

    expect(await screen.findByRole("heading", { name: "pat – Material" })).toBeVisible();
    expect(screen.getByText("Bundesliga, Season 2")).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent("You are not ready yet.");
    expect(screen.getByText("Your opponent is a bot and always ready.")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Ready" }));

    await waitFor(() => expect(FakeSocket.instances).toHaveLength(1));
    const post = api.calls.find((call) => call.method === "POST");
    expect(post?.url.pathname).toBe(`/api/v1/matches/${MATCH_ID}/ready`);
    expect(post?.body).toBeUndefined();
    expect(loadSeat(MATCH_ID, "ready")).toBe(SEAT);
    expect(loadSeat(MATCH_ID)).toBeUndefined();

    const socket = FakeSocket.latest();
    act(() => socket.open());
    expect(socket.sentMessages()).toEqual([{ type: "join", v: 1, match_id: MATCH_ID, seat: SEAT }]);
    act(() =>
      socket.receive({
        type: "state",
        v: 1,
        color: "white",
        white: "pat",
        black: "Material",
        start_fen: START_FEN,
        fen: START_FEN,
        moves: "",
        san: "",
        clock: { white: 180_000, black: 180_000 },
        running: "black",
        increment_ms: 2_000,
        legal_moves: "",
        result: null,
        termination: null,
      }),
    );
    expect(screen.getByText("Your opponent is thinking …")).toBeVisible();
  });

  it("sends the stored seat again and shows the opponent's state", async () => {
    saveSeat(MATCH_ID, SEAT, "ready");
    const api = mockApi({
      "/session": { user: PLAYER },
      "/account/competition-games": {
        items: [
          game({
            black: { ...side("sam", "", null), kind: "human", bot_id: null, sdk: null, lang: null },
            readiness: readiness({
              white: { ready: true, present: true },
              black: { ready: true, present: false },
            }),
          }),
        ],
      },
      [`/matches/${MATCH_ID}/ready`]: {
        match_id: MATCH_ID,
        seat: SEAT,
        color: "white",
        socket_path: "/api/v1/play/socket",
      },
    });
    renderRoute(`/play/${MATCH_ID}`);

    expect(await screen.findByRole("status")).toHaveTextContent("You are ready.");
    expect(
      screen.getByText("Your opponent is ready but does not have the page open right now."),
    ).toBeVisible();
    expect(screen.queryByRole("button", { name: "Ready" })).toBeNull();
    expect(api.calls.some((call) => call.method === "POST")).toBe(false);
  });

  it("counts down to the estimated start of a ready game", async () => {
    saveSeat(MATCH_ID, SEAT, "ready");
    const soon = new Date(Date.now() + 65_000).toISOString();
    mockApi({
      "/session": { user: PLAYER },
      "/account/competition-games": {
        items: [game({ readiness: readiness({ white: { ready: true, present: true } }) }, soon)],
      },
    });
    renderRoute(`/play/${MATCH_ID}`);

    expect(await screen.findByText(/The game probably starts in 1:0[45]\./)).toBeVisible();
    const bar = screen.getByRole("progressbar", { name: "Waiting time until the start" });
    expect(Number(bar.getAttribute("max"))).toBeGreaterThan(60_000);
    expect(screen.getByText(/^Ready by /)).not.toHaveTextContent("left");
  });

  it("says the game starts any moment once the estimate has passed", async () => {
    saveSeat(MATCH_ID, SEAT, "ready");
    const past = new Date(Date.now() - 5_000).toISOString();
    mockApi({
      "/session": { user: PLAYER },
      "/account/competition-games": {
        items: [game({ readiness: readiness({ white: { ready: true, present: true } }) }, past)],
      },
    });
    renderRoute(`/play/${MATCH_ID}`);

    expect(await screen.findByText("The game starts any moment now.")).toBeVisible();
  });

  it("counts down to the deadline without an estimate", async () => {
    const deadline = new Date(Date.now() + 3_600_000 + 125_000).toISOString();
    mockApi({
      "/session": { user: PLAYER },
      "/account/competition-games": { items: [game({ readiness: readiness({ deadline }) })] },
    });
    renderRoute(`/play/${MATCH_ID}`);

    expect(await screen.findByText(/^Ready by .* – 1:02:0[45] left$/)).toBeVisible();
    expect(screen.queryByRole("progressbar")).toBeNull();
  });

  it("names a game that is not open for the account", async () => {
    mockApi({ "/session": { user: PLAYER }, "/account/competition-games": { items: [] } });
    renderRoute(`/play/${MATCH_ID}`);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "not an open league or tournament game",
    );
    expect(screen.getByRole("link", { name: "To the game" })).toHaveAttribute(
      "href",
      `/matches/${MATCH_ID}`,
    );
  });

  it("names a game that is not released yet", async () => {
    mockApi({
      "/session": { user: PLAYER },
      "/account/competition-games": { items: [game({ readiness: null })] },
    });
    renderRoute(`/play/${MATCH_ID}`);

    expect(await screen.findByRole("status")).toHaveTextContent("not released yet");
    expect(screen.queryByRole("button", { name: "Ready" })).toBeNull();
  });
});
