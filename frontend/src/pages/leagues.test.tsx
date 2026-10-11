import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { Bot } from "../api/types";
import {
  ADMIN,
  BOTS,
  CODER,
  PLAYER,
  SHARP_ID,
  botDetail,
  match,
  storedDiscipline,
  user as account,
} from "../test/fixtures";
import { LEAGUE_ID, SEASON_ID, league, leagueDetail, registration, season } from "../test/leagues";
import { mockApi, renderRoute } from "../test/render";

const SHARP: Bot = { ...BOTS[0]!, id: SHARP_ID, name: "Sharp", builtin: false };

describe("league pages", () => {
  it("lists the leagues with their latest season", async () => {
    mockApi({ "/session": { user: null }, "/leagues": { items: [league()] } });
    renderRoute("/leagues");

    const row = (await screen.findByRole("link", { name: "Bundesliga" })).closest("tr")!;
    expect(row).toHaveTextContent("Season 1: Planned");
    expect(within(row).getByText("Blitz")).toBeVisible();
  });

  it("shows a league and lets a coder register a verified bot", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: CODER },
      [`/leagues/${LEAGUE_ID}`]: leagueDetail(),
      "/account/bots": { items: [SHARP, { ...SHARP, id: "x2", status: "rejected" }] },
      [`/leagues/${LEAGUE_ID}/registrations`]: registration(),
    });
    renderRoute(`/leagues/${LEAGUE_ID}`);

    expect(await screen.findByRole("heading", { name: "Bundesliga" })).toBeVisible();
    expect(screen.getByText("The next season waits for an admin to start it.")).toBeVisible();
    expect(screen.getByText("none, an admin starts each one")).toBeVisible();
    expect(screen.getByText("Wins, Head-to-head, Lot")).toBeVisible();
    expect(screen.getByText("1 / ½ / 0")).toBeVisible();
    const registered = screen.getByRole("link", { name: "Random" }).closest("tr")!;
    expect(registered).toHaveTextContent("from the next season");

    const choice = await screen.findByRole("combobox", { name: "Bot" });
    expect(within(choice).getAllByRole("option")).toHaveLength(1);
    await user.click(screen.getByRole("button", { name: "Register" }));

    await screen.findByRole("heading", { name: "Bundesliga" });
    const post = api.calls.find((call) => call.method === "POST");
    expect(post?.url.pathname).toBe(`/api/v1/leagues/${LEAGUE_ID}/registrations`);
    expect(post?.body).toEqual({ bot_id: SHARP_ID });
  });

  it("lets an admin register any verified bot, reference bots included", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: ADMIN },
      [`/leagues/${LEAGUE_ID}`]: leagueDetail(),
      "/bots": { items: [...BOTS, SHARP] },
      [`/leagues/${LEAGUE_ID}/registrations`]: registration(),
    });
    renderRoute(`/leagues/${LEAGUE_ID}`);

    const choice = await screen.findByRole("combobox", { name: "Bot" });
    expect(
      within(choice)
        .getAllByRole("option")
        .map((option) => option.textContent),
    ).toEqual(["Material", "Sharp"]);
    await user.click(screen.getByRole("button", { name: "Register" }));

    await waitFor(() => expect(api.calls.some((call) => call.method === "POST")).toBe(true));
    const post = api.calls.find((call) => call.method === "POST");
    expect(post?.body).toEqual({ bot_id: BOTS[1]!.id });
    expect(api.calls.some((call) => call.url.pathname === "/api/v1/account/bots")).toBe(false);
  });

  it("names a bot registered already", async () => {
    const user = userEvent.setup();
    mockApi({
      "/session": { user: CODER },
      [`/leagues/${LEAGUE_ID}`]: leagueDetail(),
      "/account/bots": { items: [SHARP] },
      [`/leagues/${LEAGUE_ID}/registrations`]: Response.json(
        { code: "already_registered", message: "registered", field: "bot_id" },
        { status: 409 },
      ),
    });
    renderRoute(`/leagues/${LEAGUE_ID}`);

    await user.click(await screen.findByRole("button", { name: "Register" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The bot or account is registered here already.",
    );
  });

  it("shows the tables of a season with outcomes and forfeits", async () => {
    mockApi({ "/session": { user: null }, [`/seasons/${SEASON_ID}`]: season() });
    renderRoute(`/seasons/${SEASON_ID}`);

    expect(await screen.findByRole("heading", { name: "Bundesliga – season 1" })).toBeVisible();
    expect(screen.getByText("Blitz (3 min + 2 s)")).toBeVisible();
    const winner = screen.getByRole("link", { name: "Material" }).closest("tr")!;
    expect(within(winner).getByText("2 (1 by forfeit)")).toBeVisible();
    expect(within(winner).getByText("Stays")).toBeVisible();
    const withdrawn = screen.getByRole("link", { name: "Random" }).closest("tr")!;
    expect(within(withdrawn).getByText("–")).toBeVisible();
    expect(within(withdrawn).getByText("Withdrawn")).toBeVisible();
    expect(screen.getByRole("link", { name: "Games of the tier" })).toHaveAttribute(
      "href",
      `/matches?season=${SEASON_ID}&tier=1`,
    );
  });

  it("filters the games by season and tier", async () => {
    const api = mockApi({
      "/session": { user: null },
      "/matches": { items: [], total: 0 },
      "/bots": { items: BOTS },
      "/disciplines": { items: [] },
    });
    renderRoute(`/matches?season=${SEASON_ID}&tier=2`);

    expect(await screen.findByText("Only the games of tier 2 of one season.")).toBeVisible();
    const list = api.requests.find((url) => url.pathname === "/api/v1/matches")!;
    expect(list.searchParams.get("season_id")).toBe(SEASON_ID);
    expect(list.searchParams.get("tier")).toBe("2");
  });

  it("shows where a league game stands", async () => {
    const place = {
      league_id: LEAGUE_ID,
      league_name: "Bundesliga",
      season_id: SEASON_ID,
      season_number: 3,
      tier: 2,
      round: 4,
      board: 1,
    };
    mockApi({ "/session": { user: null }, "/matches/m1": match({ id: "m1", league: place }) });
    renderRoute("/matches/m1");

    expect(await screen.findByRole("link", { name: "Season 3" })).toHaveAttribute(
      "href",
      `/seasons/${SEASON_ID}`,
    );
    expect(screen.getByText(/tier 2, round 4, board 1/)).toBeVisible();
  });
});

describe("leagues of a bot", () => {
  it("lets the owner leave a league and join another", async () => {
    const user = userEvent.setup();
    const other = league({ id: "665f0000000000000000e002", name: "Kreisliga" });
    let entries = [
      registration({
        bot: { kind: "bot", bot_id: SHARP_ID, user_id: null, name: "Sharp", version: "1.0.0" },
      }),
    ];
    const api = mockApi({
      "/session": { user: CODER },
      [`/bots/${SHARP_ID}`]: botDetail({ status: "verified" }),
      [`/bots/${SHARP_ID}/opponents`]: { items: [] },
      [`/bots/${SHARP_ID}/leagues`]: () => ({ items: entries }),
      "/leagues": { items: [league(), other] },
      [`/leagues/${LEAGUE_ID}/registrations/${SHARP_ID}`]: () => {
        entries = [];
        return new Response(null, { status: 204 });
      },
      [`/leagues/${LEAGUE_ID}/registrations`]: registration(),
    });
    renderRoute(`/bots/${SHARP_ID}`);

    const choice = await screen.findByRole("combobox", { name: "League" });
    expect(
      within(choice)
        .getAllByRole("option")
        .map((option) => option.textContent),
    ).toEqual(["Kreisliga"]);
    await user.click(screen.getByRole("button", { name: "Deregister" }));
    expect(await screen.findByText("The bot is not registered in any league.")).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Register" }));
    await waitFor(() => expect(api.calls.filter((call) => call.method === "POST")).toHaveLength(1));
    const methods = api.calls
      .filter((call) => call.method !== "GET")
      .map((call) => `${call.method} ${call.url.pathname}`);
    expect(methods).toEqual([
      `DELETE /api/v1/leagues/${LEAGUE_ID}/registrations/${SHARP_ID}`,
      `POST /api/v1/leagues/${LEAGUE_ID}/registrations`,
    ]);
  });
});

describe("leagues of a reference bot", () => {
  it("lets an admin register it in a league", async () => {
    const user = userEvent.setup();
    const material = BOTS[1]!;
    const api = mockApi({
      "/session": { user: ADMIN },
      [`/bots/${material.id}`]: botDetail({ ...material, details: null }),
      [`/bots/${material.id}/opponents`]: { items: [] },
      [`/bots/${material.id}/leagues`]: { items: [] },
      "/leagues": { items: [league()] },
      [`/leagues/${LEAGUE_ID}/registrations`]: registration(),
    });
    renderRoute(`/bots/${material.id}`);

    const choice = await screen.findByRole("combobox", { name: "League" });
    const form = choice.closest("form")!;
    await user.click(within(form).getByRole("button", { name: "Register" }));
    await waitFor(() => expect(api.calls.some((call) => call.method === "POST")).toBe(true));
    expect(api.calls.find((call) => call.method === "POST")!.body).toEqual({
      bot_id: material.id,
    });
  });
});

describe("accounts in leagues", () => {
  const PAT = {
    kind: "human" as const,
    bot_id: null,
    user_id: PLAYER.id,
    name: "pat",
    version: null,
  };

  it("lets a player join a league with the account", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: PLAYER },
      [`/leagues/${LEAGUE_ID}`]: leagueDetail(),
      [`/leagues/${LEAGUE_ID}/registrations`]: registration({ bot: PAT }),
    });
    renderRoute(`/leagues/${LEAGUE_ID}`);

    expect(await screen.findByRole("heading", { name: "Play yourself" })).toBeVisible();
    expect(screen.getByText(/at most 48 hours after its release/)).toBeVisible();
    expect(screen.queryByRole("combobox", { name: "Bot" })).toBeNull();
    await user.click(screen.getByRole("button", { name: "Join" }));

    await waitFor(() => expect(api.calls.some((call) => call.method === "POST")).toBe(true));
    const post = api.calls.find((call) => call.method === "POST");
    expect(post?.url.pathname).toBe(`/api/v1/leagues/${LEAGUE_ID}/registrations`);
    expect(post?.body).toEqual({ user_id: PLAYER.id });
  });

  it("lets an account leave and hides joining while it is registered", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: PLAYER },
      [`/leagues/${LEAGUE_ID}`]: leagueDetail({
        registrations: [registration(), registration({ bot: PAT })],
      }),
      [`/leagues/${LEAGUE_ID}/registrations/${PLAYER.id}`]: new Response(null, { status: 204 }),
    });
    renderRoute(`/leagues/${LEAGUE_ID}`);

    const button = await screen.findByRole("button", { name: "Deregister" });
    expect(button.closest("tr")).toHaveTextContent("pat");
    expect(screen.getAllByRole("button", { name: "Deregister" })).toHaveLength(1);
    expect(screen.queryByRole("button", { name: "Join" })).toBeNull();
    await user.click(button);

    await waitFor(() => expect(api.calls.some((call) => call.method === "DELETE")).toBe(true));
    const deleted = api.calls.find((call) => call.method === "DELETE");
    expect(deleted?.url.pathname).toBe(`/api/v1/leagues/${LEAGUE_ID}/registrations/${PLAYER.id}`);
  });

  it("lets an admin register an active account that is not in the league", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: ADMIN },
      [`/leagues/${LEAGUE_ID}`]: leagueDetail({
        registrations: [registration({ bot: { ...PAT, user_id: CODER.id, name: "bob" } })],
      }),
      "/bots": { items: BOTS },
      "/admin/users": {
        items: [
          account(ADMIN),
          account(CODER),
          account(PLAYER),
          account(
            { ...PLAYER, id: "665f0000000000000000a004", username: "gone" },
            { active: false },
          ),
        ],
      },
      [`/leagues/${LEAGUE_ID}/registrations`]: registration({ bot: PAT }),
    });
    renderRoute(`/leagues/${LEAGUE_ID}`);

    const choice = await screen.findByRole("combobox", { name: "Account" });
    expect(
      within(choice)
        .getAllByRole("option")
        .map((option) => option.textContent),
    ).toEqual(["admin", "pat"]);
    await user.selectOptions(choice, "pat");
    const form = choice.closest("form")!;
    await user.click(within(form).getByRole("button", { name: "Register" }));

    await waitFor(() => expect(api.calls.some((call) => call.method === "POST")).toBe(true));
    const post = api.calls.find((call) => call.method === "POST");
    expect(post?.body).toEqual({ user_id: PLAYER.id });
  });
});

describe("admin leagues", () => {
  it("creates a league with the defaults and starts its first season", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: ADMIN },
      "/leagues": { items: [league()] },
      "/disciplines": { items: [storedDiscipline()] },
      "/admin/leagues": league(),
      [`/admin/leagues/${LEAGUE_ID}/start`]: league(),
      [`/admin/leagues/${LEAGUE_ID}`]: league({ archived: true }),
    });
    renderRoute("/admin/leagues");

    await user.type(await screen.findByRole("textbox", { name: "Name" }), "Kreisliga");
    await user.click(screen.getByRole("button", { name: "Create league" }));
    await user.click(screen.getByRole("button", { name: "Start now" }));
    await user.click(screen.getByRole("button", { name: "Archive" }));

    const changes = api.calls.filter((call) => call.method !== "GET");
    expect(changes.map((call) => call.url.pathname)).toEqual([
      "/api/v1/admin/leagues",
      `/api/v1/admin/leagues/${LEAGUE_ID}/start`,
      `/api/v1/admin/leagues/${LEAGUE_ID}`,
    ]);
    expect(changes[0]!.body).toEqual({
      name: "Kreisliga",
      discipline_id: storedDiscipline().id,
      tiers: 1,
      tier_size: 10,
      games_per_pairing: 2,
      promotions: 2,
      points: { win: 1, draw: 0.5, loss: 0 },
      tiebreaks: ["wins", "head_to_head", "sonneborn_berger"],
      min_participants: 2,
      priority: 50,
      ready_hours: 48,
      recurrence: null,
    });
    expect(changes[2]!.body).toEqual({ archived: true });
  });

  it("changes a league without setting its discipline again", async () => {
    const user = userEvent.setup();
    const running = league({
      season: { ...league().season!, status: "running", starts_after: "2026-05-01T10:00:00Z" },
    });
    const api = mockApi({
      "/session": { user: ADMIN },
      "/leagues": { items: [running] },
      "/disciplines": { items: [storedDiscipline({ archived: true })] },
      [`/admin/leagues/${LEAGUE_ID}`]: running,
    });
    renderRoute("/admin/leagues");

    await user.click(await screen.findByRole("button", { name: "Edit" }));
    expect(screen.queryByRole("button", { name: "Start now" })).toBeNull();
    const size = screen.getByRole("spinbutton", { name: "Bots per tier" });
    await user.clear(size);
    await user.type(size, "6");
    await user.selectOptions(screen.getByRole("combobox", { name: "Criterion 3" }), "fewer_moves");
    await user.click(screen.getByRole("checkbox", { name: "Start by calendar" }));
    const start = screen.getByLabelText("First start");
    await user.clear(start);
    await user.type(start, "2026-11-01T18:00");
    const every = screen.getByRole("spinbutton", { name: "Every" });
    await user.clear(every);
    await user.type(every, "2");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByRole("heading", { name: "New league" })).toBeVisible();
    const patch = api.calls.find((call) => call.method === "PATCH")!.body as Record<
      string,
      unknown
    >;
    expect(patch).not.toHaveProperty("discipline_id");
    expect(patch).toMatchObject({
      tier_size: 6,
      tiebreaks: ["wins", "head_to_head", "fewer_moves"],
      recurrence: { first_start: new Date("2026-11-01T18:00").toISOString(), interval_hours: 48 },
    });
  });

  it("names the rule of a refused setting", async () => {
    const user = userEvent.setup();
    mockApi({
      "/session": { user: ADMIN },
      "/leagues": { items: [] },
      "/disciplines": { items: [storedDiscipline()] },
      "/admin/leagues": Response.json(
        { code: "invalid_parameter", message: "too many", field: "promotions" },
        { status: 400 },
      ),
    });
    renderRoute("/admin/leagues");

    await user.type(await screen.findByRole("textbox", { name: "Name" }), "Kreisliga");
    await user.click(screen.getByRole("button", { name: "Create league" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "At most half a tier may be promoted or relegated.",
    );
  });
});
