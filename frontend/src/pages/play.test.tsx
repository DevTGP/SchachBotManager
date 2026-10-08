import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { PlayState } from "../play/protocol";
import { saveSeat } from "../play/seats";
import { FakeSocket } from "../test/fakeSocket";
import { ADMIN, BOTS, CODER, PLAYER, START_FEN } from "../test/fixtures";
import { type ApiCall, mockApi, renderRoute } from "../test/render";

const MATCH_ID = "665f00000000000000000f01";
const SEAT = "Xq3v7dK2mP9sL1wR8tY4uB6nC0eF5gH2jA7kZ3xQ_-M";

function state(overrides: Partial<PlayState> = {}): PlayState {
  return {
    type: "state",
    v: 1,
    color: "white",
    white: "Guest",
    black: "Material",
    start_fen: START_FEN,
    fen: START_FEN,
    moves: "",
    san: "",
    clock: { white: 300_000, black: 300_000 },
    running: "white",
    increment_ms: 0,
    legal_moves: "e2e3 e2e4 g1f3",
    result: null,
    termination: null,
    ...overrides,
  };
}

function square(name: string): HTMLElement {
  const element = document.querySelector<HTMLElement>(`[data-square="${name}"]`);
  if (!element) throw new Error(`no square ${name}`);
  return element;
}

beforeEach(() => {
  FakeSocket.instances = [];
  vi.stubGlobal("WebSocket", FakeSocket);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

async function openGame() {
  saveSeat(MATCH_ID, SEAT);
  mockApi({ "/session": { user: null } });
  renderRoute(`/play/${MATCH_ID}`);
  await waitFor(() => expect(FakeSocket.instances).toHaveLength(1));
  const socket = FakeSocket.latest();
  act(() => socket.open());
  return socket;
}

describe("play setup", () => {
  it("starts a game against a bot and keeps the seat", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: null },
      "/bots": { items: BOTS },
      "/disciplines": { items: [] },
      "/play": () =>
        Response.json(
          { match_id: MATCH_ID, seat: SEAT, color: "white", socket_path: "/api/v1/play/socket" },
          { status: 201 },
        ),
    });
    const { router } = renderRoute("/play");

    await user.selectOptions(await screen.findByRole("combobox", { name: "Bot" }), BOTS[1]!.id);
    await user.selectOptions(screen.getByRole("combobox", { name: "Your color" }), "white");
    await user.click(screen.getByRole("button", { name: "Start game" }));

    await waitFor(() => expect(router.state.location.pathname).toBe(`/play/${MATCH_ID}`));
    const call = api.calls.find((made) => made.url.pathname === "/api/v1/play");
    expect(call?.body).toEqual({
      bot_id: BOTS[1]!.id,
      color: "white",
      initial_time_ms: 300_000,
      increment_ms: 3000,
    });
    expect(localStorage.getItem(`sbm.play.${MATCH_ID}`)).toBe(SEAT);
  });

  it("names a full server", async () => {
    const user = userEvent.setup();
    mockApi({
      "/session": { user: null },
      "/bots": { items: BOTS },
      "/disciplines": { items: [] },
      "/play": () => Response.json({ code: "no_capacity", message: "full" }, { status: 503 }),
    });
    renderRoute("/play");

    await user.click(await screen.findByRole("button", { name: "Start game" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("All places for games are taken");
  });
});

describe("game page", () => {
  it("joins the seat and plays a move by clicking", async () => {
    const user = userEvent.setup();
    const socket = await openGame();
    expect(socket.sentMessages()).toEqual([{ type: "join", v: 1, match_id: MATCH_ID, seat: SEAT }]);

    act(() => socket.receive({ type: "joined", v: 1, match_id: MATCH_ID }));
    expect(screen.getByText(/Waiting for the bot/)).toBeVisible();
    act(() => socket.receive(state()));
    expect(screen.getByText("Your move.")).toBeVisible();

    await user.click(square("e2"));
    await user.click(square("e4"));

    expect(socket.sentMessages().at(-1)).toEqual({ type: "move", v: 1, move: "e2e4" });
  });

  it("shows the bot's move, then the result", async () => {
    const socket = await openGame();
    act(() =>
      socket.receive(
        state({
          moves: "e2e4",
          san: "e4",
          running: "black",
          legal_moves: "",
          clock: { white: 297_000, black: 300_000 },
        }),
      ),
    );
    expect(screen.getByText(/The bot is thinking/)).toBeVisible();
    expect(screen.getByText("e4")).toBeVisible();
    expect(screen.getByTestId("clock-white")).toHaveTextContent("4:57");

    act(() =>
      socket.receive(
        state({
          moves: "e2e4",
          san: "e4",
          running: null,
          legal_moves: "",
          result: "0-1",
          termination: "resignation",
        }),
      ),
    );
    expect(screen.getByText(/Game over: 0-1/)).toBeVisible();
    expect(screen.queryByRole("button", { name: "Resign" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "New game" })).toBeVisible();
  });

  it("asks which piece a pawn becomes", async () => {
    const user = userEvent.setup();
    const socket = await openGame();
    act(() =>
      socket.receive(
        state({
          fen: "8/4P3/8/8/8/8/k7/4K3 w - - 0 1",
          legal_moves: "e7e8q e7e8r e7e8b e7e8n e1d1",
        }),
      ),
    );

    await user.click(square("e7"));
    await user.click(square("e8"));
    await user.click(screen.getByRole("button", { name: "Knight" }));

    expect(socket.sentMessages().at(-1)).toEqual({ type: "move", v: 1, move: "e7e8n" });
  });

  it("resigns after asking", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const socket = await openGame();
    act(() => socket.receive(state()));

    await user.click(screen.getByRole("button", { name: "Resign" }));

    expect(socket.sentMessages().at(-1)).toEqual({ type: "resign", v: 1 });
  });

  it("joins again after a dropped connection", async () => {
    const socket = await openGame();
    act(() => socket.receive(state()));

    act(() => socket.drop());

    await waitFor(() => expect(FakeSocket.instances).toHaveLength(2), { timeout: 2000 });
    const again = FakeSocket.latest();
    act(() => again.open());
    expect(again.sentMessages()).toEqual([{ type: "join", v: 1, match_id: MATCH_ID, seat: SEAT }]);
  });

  it("says when the seat is refused", async () => {
    const socket = await openGame();
    act(() => socket.receive({ type: "refused", v: 1, code: "no_game", message: "gone" }));
    expect(screen.getByText(/cannot be joined/)).toBeVisible();
  });

  it("shows a move the server refused", async () => {
    const socket = await openGame();
    act(() => socket.receive(state()));
    act(() => socket.receive({ type: "error", v: 1, code: "illegal_move", message: "no" }));
    expect(screen.getByRole("alert")).toHaveTextContent("That move is not possible.");
  });

  it("needs the seat of this browser", async () => {
    mockApi({ "/session": { user: null } });
    renderRoute(`/play/${MATCH_ID}`);
    expect(await screen.findByRole("alert")).toHaveTextContent("another browser");
    expect(FakeSocket.instances).toHaveLength(0);
  });
});

describe("players and the admin limits", () => {
  it("shows players no own bots", async () => {
    mockApi({ "/session": { user: PLAYER }, "/bots": { items: BOTS } });
    renderRoute("/account/bots");
    expect(await screen.findByRole("alert")).toHaveTextContent("not allowed");
    expect(screen.queryByRole("link", { name: "My bots" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Play" })).toHaveAttribute("href", "/play");
  });

  it("lets admins change the limits of games", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: ADMIN },
      "/admin/play-settings": (_url: URL, call: ApiCall) =>
        call.method === "PUT"
          ? call.body
          : { max_games: 2, games_per_client: 1, games_per_day: 50 },
    });
    renderRoute("/admin/play");

    const total = await screen.findByRole("spinbutton", { name: "Games at once in total" });
    await user.clear(total);
    await user.type(total, "3");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Saved.")).toBeVisible();
    const call = api.calls.find((made) => made.method === "PUT");
    expect(call?.body).toEqual({ max_games: 3, games_per_client: 1, games_per_day: 50 });
  });
});

describe("api tokens", () => {
  it("lets coders make a token, shown once, and revoke it", async () => {
    const user = userEvent.setup();
    let items: unknown[] = [];
    const created = {
      id: "665f00000000000000000e01",
      name: "laptop",
      created_at: "2026-05-01T10:00:00.000Z",
      last_used_at: null,
      token: `sbm_${"A".repeat(43)}`,
    };
    const api = mockApi({
      "/session": { user: CODER },
      "/account/tokens": (_url: URL, call: ApiCall) => {
        if (call.method === "POST") {
          items = [
            {
              id: created.id,
              name: created.name,
              created_at: created.created_at,
              last_used_at: null,
            },
          ];
          return Response.json(created, { status: 201 });
        }
        return { items };
      },
      [`/account/tokens/${created.id}`]: () => {
        items = [];
        return new Response(null, { status: 204 });
      },
    });
    renderRoute("/account");

    await user.type(await screen.findByRole("textbox", { name: "Name" }), "laptop");
    await user.click(screen.getByRole("button", { name: "Create token" }));

    expect(await screen.findByRole("textbox", { name: "Token" })).toHaveValue(created.token);
    expect(await screen.findByRole("cell", { name: "laptop" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Revoke" }));
    expect(await screen.findByText("No tokens yet.")).toBeVisible();
    expect(api.calls.some((call) => call.method === "DELETE")).toBe(true);
  });

  it("shows players no tokens", async () => {
    mockApi({ "/session": { user: PLAYER } });
    renderRoute("/account");
    expect(await screen.findByRole("heading", { name: "Account" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "API tokens" })).not.toBeInTheDocument();
  });
});
