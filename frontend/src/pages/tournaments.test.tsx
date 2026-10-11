import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { Bot } from "../api/types";
import { ADMIN, BOTS, CODER, SHARP_ID, botDetail, match, storedDiscipline } from "../test/fixtures";
import { schedule } from "../test/leagues";
import { mockApi, renderRoute } from "../test/render";
import {
  EDITION_ID,
  TOURNAMENT_ID,
  botEdition,
  knockoutEdition,
  swissEdition,
  tournament,
  tournamentDetail,
  tournamentRegistration,
} from "../test/tournaments";

const SHARP: Bot = { ...BOTS[0]!, id: SHARP_ID, name: "Sharp", builtin: false };

describe("tournament pages", () => {
  it("lists the tournaments with format and latest edition", async () => {
    mockApi({ "/session": { user: null }, "/tournaments": { items: [tournament()] } });
    renderRoute("/tournaments");

    const row = (await screen.findByRole("link", { name: "Herbstcup" })).closest("tr")!;
    expect(row).toHaveTextContent("Round robin");
    expect(row).toHaveTextContent("Edition 1: Planned");
  });

  it("shows a tournament and lets a coder register a verified bot", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: CODER },
      [`/tournaments/${TOURNAMENT_ID}`]: tournamentDetail(),
      "/account/bots": { items: [SHARP, { ...SHARP, id: "x2", status: "rejected" }] },
      [`/tournaments/${TOURNAMENT_ID}/registrations`]: tournamentRegistration(),
    });
    renderRoute(`/tournaments/${TOURNAMENT_ID}`);

    expect(await screen.findByRole("heading", { name: "Herbstcup" })).toBeVisible();
    expect(screen.getByText("The next edition waits for an admin to start it.")).toBeVisible();
    expect(screen.getByText("Wins, Head-to-head, Sonneborn-Berger, Lot")).toBeVisible();
    expect(screen.getByText("By rating in the discipline, ties by lot")).toBeVisible();
    const registered = screen.getByRole("link", { name: "Random" }).closest("tr")!;
    expect(registered).toHaveTextContent("from the next edition");

    const choice = await screen.findByRole("combobox", { name: "Bot" });
    expect(within(choice).getAllByRole("option")).toHaveLength(1);
    await user.click(screen.getByRole("button", { name: "Register" }));

    await waitFor(() => expect(api.calls.some((call) => call.method === "POST")).toBe(true));
    const post = api.calls.find((call) => call.method === "POST")!;
    expect(post.url.pathname).toBe(`/api/v1/tournaments/${TOURNAMENT_ID}/registrations`);
    expect(post.body).toEqual({ bot_id: SHARP_ID });
  });

  it("lets an admin register a reference bot", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: ADMIN },
      [`/tournaments/${TOURNAMENT_ID}`]: tournamentDetail(),
      "/bots": { items: BOTS },
      [`/tournaments/${TOURNAMENT_ID}/registrations`]: tournamentRegistration(),
    });
    renderRoute(`/tournaments/${TOURNAMENT_ID}`);

    const choice = await screen.findByRole("combobox", { name: "Bot" });
    expect(
      within(choice)
        .getAllByRole("option")
        .map((option) => option.textContent),
    ).toEqual(["Material"]);
    await user.click(screen.getByRole("button", { name: "Register" }));

    await waitFor(() => expect(api.calls.some((call) => call.method === "POST")).toBe(true));
    expect(api.calls.find((call) => call.method === "POST")!.body).toEqual({
      bot_id: BOTS[1]!.id,
    });
  });

  it("names the knockout rules and the calendar of a tournament", async () => {
    mockApi({
      "/session": { user: null },
      [`/tournaments/${TOURNAMENT_ID}`]: tournamentDetail({
        format: "knockout",
        tiebreak_discipline_name: "Bullet",
        recurrence: { first_start: "2026-11-01T17:00:00.000Z", interval_hours: 168 },
        edition: { ...tournament().edition!, starts_after: "2026-11-01T17:00:00.000Z" },
      }),
    });
    renderRoute(`/tournaments/${TOURNAMENT_ID}`);

    expect(await screen.findByText("Bullet")).toBeVisible();
    expect(screen.getByText("Colour by lot, a draw is enough for black")).toBeVisible();
    expect(screen.queryByText(/Sonneborn-Berger/)).toBeNull();
    expect(
      screen.getByText(/The next edition starts .* once 2 bots are registered\./),
    ).toBeVisible();
  });

  it("shows the table and rounds of a Swiss edition", async () => {
    const api = mockApi({
      "/session": { user: null },
      [`/editions/${EDITION_ID}`]: swissEdition(),
      [`/editions/${EDITION_ID}/rounds`]: { rounds: schedule().rounds },
    });
    renderRoute(`/editions/${EDITION_ID}`);

    expect(await screen.findByRole("heading", { name: "Herbstcup – edition 1" })).toBeVisible();
    expect(screen.getByText("Blitz (3 min + 2 s)")).toBeVisible();
    const table = screen.getByRole("heading", { name: "Table" }).closest("section")!;
    const columns = within(table)
      .getAllByRole("columnheader")
      .map((cell) => cell.textContent);
    expect(columns).toContain("Byes");
    expect(columns).toContain("Buchholz");
    const sharp = within(table).getByRole("link", { name: "Sharp" }).closest("tr")!;
    expect(within(sharp).getAllByRole("cell")[7]).toHaveTextContent("1");
    const random = within(table).getByRole("link", { name: "Random" }).closest("tr")!;
    expect(random).toHaveTextContent("Withdrawn");
    expect(screen.getByRole("link", { name: "Games of the edition" })).toHaveAttribute(
      "href",
      `/matches?edition=${EDITION_ID}`,
    );
    expect(await screen.findByText("Round 2")).toBeVisible();
    expect(api.requests.some((url) => url.pathname.endsWith("/rounds"))).toBe(true);
  });

  it("shows the bracket and places of a knockout edition", async () => {
    const api = mockApi({
      "/session": { user: null },
      [`/editions/${EDITION_ID}`]: knockoutEdition(),
    });
    renderRoute(`/editions/${EDITION_ID}`);

    expect(await screen.findByText("Final")).toBeVisible();
    expect(screen.getByText(/^Bullet/)).toBeVisible();
    const bracket = screen.getByRole("heading", { name: "Bracket" }).closest("section")!;
    const duel = within(bracket).getByText("by tiebreak").closest("tr")!;
    expect(duel).toHaveTextContent("½–½ (1–0)");
    expect(within(duel).getByTitle("Winner of the duel")).toHaveTextContent("Material");
    expect(within(bracket).getByText("Tiebreak 1")).toBeVisible();
    const places = screen.getByRole("heading", { name: "Places" }).closest("section")!;
    const first = within(places).getByRole("link", { name: "Material" }).closest("tr")!;
    expect(first).toHaveTextContent("1");
    expect(api.requests.some((url) => url.pathname.endsWith("/rounds"))).toBe(false);
  });

  it("filters the games by edition", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: null },
      "/matches": { items: [], total: 0 },
      "/bots": { items: BOTS },
      "/disciplines": { items: [] },
    });
    renderRoute(`/matches?edition=${EDITION_ID}`);

    expect(await screen.findByText("Only the games of one tournament edition.")).toBeVisible();
    const first = api.requests.find((url) => url.pathname === "/api/v1/matches")!;
    expect(first.searchParams.get("edition_id")).toBe(EDITION_ID);

    await user.click(screen.getByRole("button", { name: "Show all games" }));
    await waitFor(() =>
      expect(screen.queryByText("Only the games of one tournament edition.")).toBeNull(),
    );
    const last = api.requests.filter((url) => url.pathname === "/api/v1/matches").at(-1)!;
    expect(last.searchParams.has("edition_id")).toBe(false);
  });

  it("shows where a tournament game stands", async () => {
    const place = {
      tournament_id: TOURNAMENT_ID,
      tournament_name: "Herbstcup",
      edition_id: EDITION_ID,
      edition_number: 2,
      format: "knockout" as const,
      round: 3,
      board: 1,
      phase: "tiebreak" as const,
      game: 2,
    };
    mockApi({ "/session": { user: null }, "/matches/m1": match({ id: "m1", tournament: place }) });
    renderRoute("/matches/m1");

    expect(await screen.findByRole("link", { name: "Edition 2" })).toHaveAttribute(
      "href",
      `/editions/${EDITION_ID}`,
    );
    expect(screen.getByRole("link", { name: "Herbstcup" })).toBeVisible();
    expect(screen.getByText(/round 3, duel 1, Tiebreak 2/)).toBeVisible();
  });
});

describe("tournaments of a bot", () => {
  it("lets the owner leave a tournament and join another and lists its editions", async () => {
    const user = userEvent.setup();
    const other = tournament({ id: "665f00000000000000001002", name: "Wintercup" });
    let entries = [
      tournamentRegistration({
        bot: { bot_id: SHARP_ID, name: "Sharp", version: "1.0.0" },
        playing: true,
      }),
    ];
    const api = mockApi({
      "/session": { user: CODER },
      [`/bots/${SHARP_ID}`]: botDetail({ status: "verified" }),
      [`/bots/${SHARP_ID}/opponents`]: { items: [] },
      [`/bots/${SHARP_ID}/tournaments`]: () => ({ items: entries }),
      [`/bots/${SHARP_ID}/editions`]: { items: [botEdition()] },
      "/tournaments": { items: [tournament(), other] },
      [`/tournaments/${TOURNAMENT_ID}/registrations/${SHARP_ID}`]: () => {
        entries = [];
        return new Response(null, { status: 204 });
      },
      [`/tournaments/${TOURNAMENT_ID}/registrations`]: tournamentRegistration(),
    });
    renderRoute(`/bots/${SHARP_ID}`);

    const editions = (await screen.findByRole("heading", { name: "Tournament editions" })).closest(
      "section",
    )!;
    const row = (await within(editions).findByRole("link", { name: "Edition 1" })).closest("tr")!;
    expect(row).toHaveTextContent("Knockout");
    expect(row).toHaveTextContent("2 of 8");

    const choice = await screen.findByRole("combobox", { name: "Tournament" });
    expect(
      within(choice)
        .getAllByRole("option")
        .map((option) => option.textContent),
    ).toEqual(["Wintercup"]);
    expect(screen.getByText(/in the running edition/)).toBeVisible();
    const section = choice.closest("section")!;
    await user.click(within(section).getByRole("button", { name: "Deregister" }));
    expect(await screen.findByText("The bot is not registered in any tournament.")).toBeVisible();

    const form = screen.getByRole("combobox", { name: "Tournament" }).closest("form")!;
    await user.click(within(form).getByRole("button", { name: "Register" }));
    await waitFor(() =>
      expect(
        api.calls.filter(
          (call) => call.method === "POST" && call.url.pathname.includes("/tournaments/"),
        ),
      ).toHaveLength(1),
    );
    const methods = api.calls
      .filter((call) => call.method !== "GET" && call.url.pathname.includes("/tournaments/"))
      .map((call) => `${call.method} ${call.url.pathname}`);
    expect(methods).toEqual([
      `DELETE /api/v1/tournaments/${TOURNAMENT_ID}/registrations/${SHARP_ID}`,
      `POST /api/v1/tournaments/${TOURNAMENT_ID}/registrations`,
    ]);
  });
});

describe("admin tournaments", () => {
  it("creates a knockout tournament, starts its edition and archives it", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: ADMIN },
      "/tournaments": { items: [tournament()] },
      "/disciplines": { items: [storedDiscipline()] },
      "/admin/tournaments": tournament(),
      [`/admin/tournaments/${TOURNAMENT_ID}/start`]: tournament(),
      [`/admin/tournaments/${TOURNAMENT_ID}`]: tournament({ archived: true }),
    });
    renderRoute("/admin/tournaments");

    await user.type(await screen.findByRole("textbox", { name: "Name" }), "Wintercup");
    await user.selectOptions(screen.getByRole("combobox", { name: "Format" }), "knockout");
    expect(screen.getByRole("spinbutton", { name: "Games per duel" })).toBeVisible();
    expect(screen.queryByRole("combobox", { name: "Criterion 1" })).toBeNull();
    await user.click(screen.getByRole("button", { name: "Create tournament" }));
    await user.click(await screen.findByRole("button", { name: "Start now" }));
    await user.click(screen.getByRole("button", { name: "Archive" }));

    await waitFor(() => expect(api.calls.filter((call) => call.method !== "GET")).toHaveLength(3));
    const changes = api.calls.filter((call) => call.method !== "GET");
    expect(changes.map((call) => call.url.pathname)).toEqual([
      "/api/v1/admin/tournaments",
      `/api/v1/admin/tournaments/${TOURNAMENT_ID}/start`,
      `/api/v1/admin/tournaments/${TOURNAMENT_ID}`,
    ]);
    expect(changes[0]!.body).toEqual({
      name: "Wintercup",
      discipline_id: storedDiscipline().id,
      format: "knockout",
      games_per_pairing: 2,
      rounds: 5,
      tiebreaks: [],
      tiebreak_discipline_id: null,
      tiebreak_pairs: 1,
      min_participants: 2,
      priority: 40,
      recurrence: null,
    });
    expect(changes[2]!.body).toEqual({ archived: true });
  });

  it("changes a tournament without its format or discipline", async () => {
    const user = userEvent.setup();
    const running = tournament({
      format: "swiss",
      tiebreaks: ["buchholz", "sonneborn_berger", "wins"],
      edition: { ...tournament().edition!, status: "running" },
    });
    const api = mockApi({
      "/session": { user: ADMIN },
      "/tournaments": { items: [running] },
      "/disciplines": { items: [storedDiscipline({ archived: true })] },
      [`/admin/tournaments/${TOURNAMENT_ID}`]: running,
    });
    renderRoute("/admin/tournaments");

    await user.click(await screen.findByRole("button", { name: "Edit" }));
    expect(screen.queryByRole("button", { name: "Start now" })).toBeNull();
    expect(screen.getByRole("combobox", { name: "Format" })).toBeDisabled();
    const rounds = screen.getByRole("spinbutton", { name: "Rounds" });
    await user.clear(rounds);
    await user.type(rounds, "7");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByRole("heading", { name: "New tournament" })).toBeVisible();
    const patch = api.calls.find((call) => call.method === "PATCH")!.body as Record<
      string,
      unknown
    >;
    expect(patch).not.toHaveProperty("format");
    expect(patch).not.toHaveProperty("discipline_id");
    expect(patch).toMatchObject({ rounds: 7, tiebreaks: ["buchholz", "sonneborn_berger", "wins"] });
  });

  it("names a taken tournament name", async () => {
    const user = userEvent.setup();
    mockApi({
      "/session": { user: ADMIN },
      "/tournaments": { items: [] },
      "/disciplines": { items: [storedDiscipline()] },
      "/admin/tournaments": Response.json(
        { code: "name_taken", message: "taken", field: "name" },
        { status: 409 },
      ),
    });
    renderRoute("/admin/tournaments");

    await user.type(await screen.findByRole("textbox", { name: "Name" }), "Herbstcup");
    await user.click(screen.getByRole("button", { name: "Create tournament" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Another tournament already has this name.",
    );
  });
});
