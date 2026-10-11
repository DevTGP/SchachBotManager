import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { BOTS, queue, storedDiscipline, summary } from "../test/fixtures";
import { mockApi, renderRoute } from "../test/render";

describe("start page", () => {
  it("explains the idea without asking the API", async () => {
    const api = mockApi({});
    renderRoute("/");
    expect(
      await screen.findByRole("heading", { level: 1, name: "Chess bots in competition" }),
    ).toBeVisible();
    expect(screen.getByRole("heading", { name: "Four steps to the first game" })).toBeVisible();
    expect(screen.getByText(/class MyBot\(sbm.Bot\)/)).toBeVisible();
    expect(api.requests.filter((url) => url.pathname.startsWith("/api/v1/matches"))).toEqual([]);
  });
});

describe("matches page", () => {
  it("keeps filter and page in the URL", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/matches": { items: [summary()], total: 60 },
      "/bots": { items: BOTS },
    });
    const { router } = renderRoute("/matches?offset=25");

    expect(await screen.findByText("26–50 of 60")).toBeVisible();
    await screen.findByRole("option", { name: "Material" });
    await user.selectOptions(screen.getByRole("combobox", { name: "Bot" }), "Material");
    expect(router.state.location.search).toBe("?bot=665f0000000000000000000b");

    const status = screen.getByRole("group", { name: "Status" });
    await user.click(within(status).getByRole("button", { name: "Finished" }));
    expect(within(status).getByRole("button", { name: "Finished" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await user.click(await screen.findByRole("button", { name: "Next" }));
    expect(router.state.location.search).toBe(
      "?bot=665f0000000000000000000b&status=finished&offset=25",
    );
    const last = api.requests.filter((url) => url.pathname === "/api/v1/matches").at(-1);
    expect(Object.fromEntries(last?.searchParams ?? [])).toEqual({
      status: "finished",
      bot_id: "665f0000000000000000000b",
      limit: "25",
      offset: "25",
    });
  });

  it("filters games with players", async () => {
    const user = userEvent.setup();
    const guest = {
      kind: "human" as const,
      bot_id: null,
      name: "Guest",
      version: null,
      sdk: null,
      lang: null,
      rating: null,
    };
    const api = mockApi({
      "/matches": { items: [summary({ type: "human", white: guest })], total: 1 },
      "/bots": { items: BOTS },
    });
    const { router } = renderRoute("/matches");

    const row = (await screen.findByText("Guest")).closest("tr")!;
    expect(row.textContent).toMatch(/^Guest–Material/);
    expect(within(row).getByRole("link", { name: "Open" })).toHaveAttribute(
      "href",
      "/matches/665f00000000000000000001",
    );
    const kind = screen.getByRole("group", { name: "Kind" });
    expect(within(kind).getByRole("button", { name: "All" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await user.click(within(kind).getByRole("button", { name: "With players" }));
    expect(router.state.location.search).toBe("?kind=players");
    const last = api.requests.filter((url) => url.pathname === "/api/v1/matches").at(-1);
    expect(last?.searchParams.get("kind")).toBe("players");
  });
});

describe("bots page", () => {
  it("lists the bots with a link to their matches", async () => {
    mockApi({ "/bots": { items: BOTS } });
    renderRoute("/bots");
    const row = (await screen.findByRole("cell", { name: "Material" })).closest("tr");
    expect(row).not.toBeNull();
    expect(within(row!).getByText("Reference bot")).toBeVisible();
    expect(within(row!).getByText("1.0.0")).toBeVisible();
    expect(screen.getByRole("columnheader", { name: "Creator" })).toBeVisible();
    expect(screen.getByRole("columnheader", { name: "Version" })).toBeVisible();
    expect(within(row!).getByRole("link", { name: "0" })).toHaveAttribute(
      "href",
      "/matches?bot=665f0000000000000000000b",
    );
  });
});

describe("ratings page", () => {
  const [random, material] = BOTS;
  const sharp = { ...random!, id: "665f0000000000000000001a", name: "Sharp", builtin: false };
  const ranking = {
    "/disciplines": { items: [storedDiscipline()] },
    "/ratings": {
      items: [
        { ...material!, rating: { value: 2550, games: 3 } },
        { ...sharp, version: "1.2.0", owner: "bob", rating: { value: 2510, games: 1 } },
        { ...random!, rating: { value: 2450, games: 3 } },
      ],
    },
    "/ratings/players": { items: [{ username: "anna", rating: { value: 2500, games: 2 } }] },
  };

  it("ranks bots and players by rating", async () => {
    mockApi(ranking);
    renderRoute("/ratings");
    const rows = (await screen.findAllByRole("row")).slice(1);
    expect(rows.map((row) => row.textContent)).toEqual([
      "1Material1.0.0Reference botPython25503",
      "2Sharp1.2.0bobPython25101",
      "3anna––Player25002",
      "4Random1.0.0Reference botPython24503",
    ]);
    expect(within(rows[0]!).getByRole("link", { name: "Material" })).toHaveAttribute(
      "href",
      "/bots/665f0000000000000000000b",
    );
    expect(within(rows[2]!).queryByRole("link")).toBeNull();
  });

  it("filters bots or players through the URL", async () => {
    const user = userEvent.setup();
    const api = mockApi(ranking);
    const { router } = renderRoute("/ratings?show=players");
    expect(await screen.findByText("anna")).toBeVisible();
    expect(screen.queryByText("Material")).toBeNull();
    const paths = api.requests.map((url) => url.pathname);
    expect(paths).toContain("/api/v1/ratings/players");
    expect(paths).not.toContain("/api/v1/ratings");

    await user.click(
      within(screen.getByRole("group", { name: "Show" })).getByRole("button", {
        name: "Bots only",
      }),
    );
    expect(await screen.findByText("Material")).toBeVisible();
    expect(screen.queryByText("anna")).toBeNull();
    expect(router.state.location.search).toBe("?show=bots");
  });

  it("ranks by the overall rating or within one discipline", async () => {
    const user = userEvent.setup();
    const api = mockApi(ranking);
    const { router } = renderRoute("/ratings");
    expect(await screen.findByText(/weighted by the number of games/)).toBeVisible();
    const discipline = await screen.findByRole("group", { name: "Discipline" });
    expect(within(discipline).getByRole("button", { name: "Overall" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    await user.click(await within(discipline).findByRole("button", { name: "Blitz" }));
    expect(router.state.location.search).toBe(`?discipline=${storedDiscipline().id}`);
    await waitFor(() => {
      const last = api.requests.filter((url) => url.pathname === "/api/v1/ratings").at(-1);
      expect(last?.searchParams.get("discipline_id")).toBe(storedDiscipline().id);
    });
    const players = api.requests.filter((url) => url.pathname === "/api/v1/ratings/players");
    expect(players.at(-1)?.searchParams.get("discipline_id")).toBe(storedDiscipline().id);
    expect(screen.queryByText(/weighted by the number of games/)).toBeNull();
  });

  it("explains an empty ranking", async () => {
    mockApi({
      "/disciplines": { items: [] },
      "/ratings": { items: [] },
      "/ratings/players": { items: [] },
    });
    renderRoute("/ratings");
    expect(await screen.findByText(/No rated game yet\./)).toBeVisible();
    const empty = screen.getByText(/No rated game yet\./);
    expect(within(empty).getByRole("link", { name: "Play" })).toHaveAttribute("href", "/play");
  });
});

describe("queue page", () => {
  it("shows running and waiting matches with estimates", async () => {
    const entry = {
      match: summary({ status: "queued", result: null, termination: null }),
      position: 1,
      priority: 100,
      estimated_start: "2026-05-01T12:10:00.000Z",
      estimated_end: "2026-05-01T12:20:00.000Z",
    };
    mockApi({ "/queue": queue({ paused: true, waiting: [entry], waiting_total: 3 }) });
    renderRoute("/queue");

    expect(await screen.findByRole("status")).toHaveTextContent("The queue is paused");
    expect(screen.getByText("No game is running right now.")).toBeVisible();
    const row = screen.getByRole("link", { name: "Open" }).closest("tr")!;
    expect(row.textContent).toMatch(/^1Material–Random3\smin\s\+\s2\ss/);
    expect(screen.getByText("2 more games are waiting.")).toBeVisible();
  });
});

describe("layout", () => {
  it("switches the language and remembers it", async () => {
    const user = userEvent.setup();
    mockApi({ "/bots": { items: [] } });
    renderRoute("/bots");
    expect(await screen.findByText("No bots yet.")).toBeVisible();

    await user.click(screen.getByRole("button", { name: "DE" }));
    expect(await screen.findByText("Noch keine Bots.")).toBeVisible();
    expect(screen.getByRole("link", { name: "Partien" })).toBeVisible();
    expect(window.localStorage.getItem("sbm.language")).toBe("de");
    expect(document.documentElement.lang).toBe("de");
  });

  it("answers unknown paths", async () => {
    mockApi({});
    renderRoute("/nowhere");
    expect(await screen.findByRole("heading", { name: "Page not found" })).toBeVisible();
    const explore = screen.getByRole("navigation", { name: "Go on to" });
    expect(within(explore).getByRole("link", { name: "Ranking" })).toHaveAttribute(
      "href",
      "/ratings",
    );
  });
});
