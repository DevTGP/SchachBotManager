import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { Bot, StoredDiscipline } from "../api/types";
import {
  ADMIN,
  BOTS,
  CODER,
  CODER_LIMITS,
  ownMatches,
  queue,
  storedDiscipline,
} from "../test/fixtures";
import { type ApiCall, mockApi, renderRoute } from "../test/render";

const BLITZ = storedDiscipline();
const OLD = storedDiscipline({ id: "665f0000000000000000d002", name: "Old", archived: true });
const SHARP: Bot = { ...BOTS[0]!, id: "665f0000000000000000001a", name: "Sharp", builtin: false };

describe("admin disciplines", () => {
  it("creates a discipline and archives it", async () => {
    const user = userEvent.setup();
    let items: StoredDiscipline[] = [];
    const api = mockApi({
      "/session": { user: ADMIN },
      "/disciplines": () => ({ items }),
      "/admin/disciplines": (_url: URL, call: ApiCall) => {
        items = [storedDiscipline({ name: (call.body as { name: string }).name })];
        return items[0];
      },
      [`/admin/disciplines/${BLITZ.id}`]: (_url: URL, call: ApiCall) => {
        items = [{ ...items[0]!, ...(call.body as Partial<StoredDiscipline>) }];
        return items[0];
      },
    });
    renderRoute("/admin/disciplines");

    expect(await screen.findByText("No disciplines yet.")).toBeVisible();
    await user.type(screen.getByRole("textbox", { name: "Name" }), "Blitz");
    await user.clear(screen.getByRole("spinbutton", { name: "Tolerance (ms)" }));
    await user.type(screen.getByRole("spinbutton", { name: "Tolerance (ms)" }), "50");
    await user.click(screen.getByRole("button", { name: "Create discipline" }));

    const row = (await screen.findByRole("cell", { name: "Blitz" })).closest("tr")!;
    expect(api.calls.find((call) => call.method === "POST")?.body).toEqual({
      name: "Blitz",
      initial_time_ms: 180_000,
      increment_ms: 2_000,
      startup_ms: 10_000,
      tolerance_ms: 50,
      max_moves: 500,
    });
    expect(screen.getByRole("textbox", { name: "Name" })).toHaveValue("");
    expect(within(row).getByText("3+2")).toBeVisible();

    await user.click(within(row).getByRole("button", { name: "Archive" }));
    expect(await within(row).findByText("Archived")).toBeVisible();
    expect(api.calls.find((call) => call.method === "PATCH")?.body).toEqual({ archived: true });
  });

  it("changes a discipline", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: ADMIN },
      "/disciplines": { items: [BLITZ] },
      [`/admin/disciplines/${BLITZ.id}`]: { ...BLITZ, max_moves: 300 },
    });
    renderRoute("/admin/disciplines");

    await user.click(await screen.findByRole("button", { name: "Edit" }));
    expect(screen.getByRole("heading", { name: "Edit discipline Blitz" })).toBeVisible();
    expect(screen.getByRole("spinbutton", { name: "Startup (s)" })).toHaveValue(10);
    await user.clear(screen.getByRole("spinbutton", { name: "Move limit" }));
    await user.type(screen.getByRole("spinbutton", { name: "Move limit" }), "300");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByRole("heading", { name: "New discipline" })).toBeVisible();
    expect(api.calls.find((call) => call.method === "PATCH")?.body).toMatchObject({
      name: "Blitz",
      max_moves: 300,
    });
  });

  it("names a taken name", async () => {
    const user = userEvent.setup();
    mockApi({
      "/session": { user: ADMIN },
      "/disciplines": { items: [BLITZ] },
      "/admin/disciplines": Response.json(
        { code: "name_taken", message: "taken", field: "name" },
        { status: 409 },
      ),
    });
    renderRoute("/admin/disciplines");

    await user.type(await screen.findByRole("textbox", { name: "Name" }), "blitz");
    await user.click(screen.getByRole("button", { name: "Create discipline" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Another discipline already has this name.",
    );
  });
});

describe("games under a discipline", () => {
  it("lets admins choose a discipline in use instead of free times", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: ADMIN },
      "/bots": { items: BOTS },
      "/queue": queue(),
      "/disciplines": { items: [BLITZ, OLD] },
      "/admin/matches": { match_ids: ["m1"], series_id: null },
    });
    renderRoute("/admin");

    const choice = await screen.findByRole("combobox", { name: "Discipline" });
    await within(choice).findByRole("option", { name: "Blitz (3+2)" });
    expect(within(choice).queryByRole("option", { name: /Old/ })).toBeNull();
    await user.selectOptions(choice, "Blitz (3+2)");
    expect(screen.queryByRole("spinbutton", { name: "Time (s)" })).toBeNull();
    await user.click(screen.getByRole("button", { name: "Add to queue" }));

    await screen.findByText("1 game queued.");
    expect(api.calls.find((call) => call.method === "POST")?.body).toEqual({
      white_bot_id: BOTS[0]!.id,
      black_bot_id: BOTS[1]!.id,
      discipline_id: BLITZ.id,
      games: 1,
      alternate: false,
      priority: 100,
      rated: true,
    });
  });

  it("lets coders choose one beyond the free limits", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: CODER },
      "/account/bots": { items: [SHARP] },
      "/account/limits": CODER_LIMITS,
      "/bots": { items: [...BOTS, SHARP] },
      "/disciplines": { items: [BLITZ] },
      "/matches": ownMatches({ match_ids: ["m1", "m2"], series_id: "s1" }),
    });
    renderRoute("/account/bots");

    const choice = await screen.findByRole("combobox", { name: "Discipline" });
    await user.selectOptions(choice, await within(choice).findByRole("option", { name: /Blitz/ }));
    await user.click(screen.getByRole("button", { name: "Add to queue" }));

    await screen.findByText(/2 games queued/);
    expect(api.calls.find((call) => call.method === "POST")?.body).toEqual({
      white_bot_id: SHARP.id,
      black_bot_id: BOTS[0]!.id,
      discipline_id: BLITZ.id,
      games: 2,
      alternate: true,
      rated: true,
    });
  });
});
