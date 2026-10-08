import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { BOTS, queue, summary } from "../test/fixtures";
import { mockApi, renderRoute } from "../test/render";

describe("start page", () => {
  it("lists running and finished matches", async () => {
    mockApi({
      "/matches": (url: URL) =>
        url.searchParams.get("status") === "running"
          ? { items: [], total: 0 }
          : { items: [summary()], total: 1 },
    });
    renderRoute("/");
    expect(await screen.findByText("No game is running right now.")).toBeVisible();
    const link = await screen.findByRole("link", { name: "Random 1.0.0 – Material 1.0.0" });
    expect(link).toHaveAttribute("href", "/matches/665f00000000000000000001");
    expect(screen.getByText("0–1")).toBeVisible();
    expect(screen.getByText("3+2")).toBeVisible();
  });

  it("explains an unreachable API", async () => {
    mockApi({
      "/matches": () => Response.json({ code: "unavailable", message: "db" }, { status: 503 }),
    });
    renderRoute("/");
    expect((await screen.findAllByRole("alert"))[0]).toHaveTextContent(
      "The service is unavailable right now.",
    );
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

    await user.selectOptions(screen.getByRole("combobox", { name: "Status" }), "Finished");
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
});

describe("bots page", () => {
  it("lists the bots with a link to their matches", async () => {
    mockApi({ "/bots": { items: BOTS } });
    renderRoute("/bots");
    const row = (await screen.findByRole("cell", { name: "Material" })).closest("tr");
    expect(row).not.toBeNull();
    expect(within(row!).getByText("Reference bot")).toBeVisible();
    expect(within(row!).getByText("2500")).toBeVisible();
    expect(within(row!).getByRole("link", { name: "Games" })).toHaveAttribute(
      "href",
      "/matches?bot=665f0000000000000000000b",
    );
  });
});

describe("ratings page", () => {
  it("ranks the bots by rating", async () => {
    const [random, material] = BOTS;
    mockApi({
      "/ratings": {
        items: [
          { ...material!, rating: { value: 2550, games: 3 } },
          { ...random!, rating: { value: 2450, games: 3 } },
        ],
      },
    });
    renderRoute("/ratings");
    const rows = (await screen.findAllByRole("row")).slice(1);
    expect(rows.map((row) => row.textContent)).toEqual([
      "1MaterialPython25503",
      "2RandomPython24503",
    ]);
    expect(within(rows[0]!).getByRole("link", { name: "Material" })).toHaveAttribute(
      "href",
      "/bots/665f0000000000000000000b",
    );
  });

  it("explains an empty ranking", async () => {
    mockApi({ "/ratings": { items: [] } });
    renderRoute("/ratings");
    expect(await screen.findByText("No rated game yet.")).toBeVisible();
  });
});

describe("queue page", () => {
  it("shows running and waiting matches with estimates", async () => {
    const entry = {
      match: summary({ status: "queued", result: null, termination: null }),
      position: 1,
      estimated_start: "2026-05-01T12:10:00.000Z",
      estimated_end: "2026-05-01T12:20:00.000Z",
    };
    mockApi({ "/queue": queue({ paused: true, waiting: [entry], waiting_total: 3 }) });
    renderRoute("/queue");

    expect(await screen.findByRole("status")).toHaveTextContent("The queue is paused");
    expect(screen.getByText("No game is running right now.")).toBeVisible();
    expect(screen.getByRole("link", { name: "Random 1.0.0 – Material 1.0.0" })).toBeVisible();
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
  });
});
