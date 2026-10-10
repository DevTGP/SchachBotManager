import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { AuditEntry, Invite, User } from "../api/types";
import { ADMIN, BOTS, CODER, queue, user as account } from "../test/fixtures";
import { type ApiCall, mockApi, renderRoute } from "../test/render";

const NO_CONTENT = () => new Response(null, { status: 204 });
const SITE = "https://sbm.example";

describe("admin access", () => {
  it("refuses coders", async () => {
    mockApi({ "/session": { user: CODER } });
    renderRoute("/admin/users");
    expect(await screen.findByRole("alert")).toHaveTextContent("You are not allowed to do this.");
  });
});

describe("admin games", () => {
  it("pauses and resumes the queue", async () => {
    const user = userEvent.setup();
    let paused = false;
    mockApi({
      "/session": { user: ADMIN },
      "/bots": { items: BOTS },
      "/queue": () => queue({ paused }),
      "/admin/queue": (_url: URL, call: ApiCall) => {
        paused = (call.body as { paused: boolean }).paused;
        return { paused };
      },
    });
    renderRoute("/admin");
    expect(await screen.findByText("The queue is running.")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Pause" }));
    expect(await screen.findByText("The queue is paused.")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Resume" }));
    expect(await screen.findByText("The queue is running.")).toBeVisible();
  });

  it("schedules games between two bots", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: ADMIN },
      "/bots": { items: BOTS },
      "/queue": queue(),
      "/admin/matches": { match_ids: ["m1", "m2", "m3"] },
    });
    renderRoute("/admin");
    const games = await screen.findByRole("spinbutton", { name: "Games" });
    await user.clear(games);
    await user.type(games, "3");
    await user.clear(screen.getByRole("spinbutton", { name: "Increment (s)" }));
    await user.type(screen.getByRole("spinbutton", { name: "Increment (s)" }), "0.5");
    await user.click(screen.getByRole("checkbox", { name: "Alternate colours" }));
    await user.click(screen.getByRole("button", { name: "Add to queue" }));

    expect(await screen.findByText("3 games queued.")).toBeVisible();
    const post = api.calls.find((call) => call.url.pathname === "/api/v1/admin/matches");
    expect(post?.body).toEqual({
      white_bot_id: BOTS[0]!.id,
      black_bot_id: BOTS[1]!.id,
      initial_time_ms: 180_000,
      increment_ms: 500,
      games: 3,
      alternate: true,
      priority: 100,
      max_moves: 500,
    });
  });

  it("names the invalid field", async () => {
    const user = userEvent.setup();
    mockApi({
      "/session": { user: ADMIN },
      "/bots": { items: BOTS },
      "/queue": queue(),
      "/admin/matches": Response.json(
        { code: "invalid_parameter", message: "bad FEN", field: "start_fen" },
        { status: 400 },
      ),
    });
    renderRoute("/admin");
    await user.type(await screen.findByLabelText("Start position (FEN, optional)"), "nonsense");
    await user.click(screen.getByRole("button", { name: "Add to queue" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("The position is invalid.");
  });
});

describe("admin users", () => {
  it("deactivates an account and creates a reset link", async () => {
    const user = userEvent.setup();
    let bob: User = account(CODER);
    const api = mockApi({
      "/session": { user: ADMIN },
      "/admin/users": () => ({ items: [account(ADMIN), bob] }),
      [`/admin/users/${CODER.id}`]: (_url: URL, call: ApiCall) => {
        bob = { ...bob, ...(call.body as Partial<User>) };
        return bob;
      },
      [`/admin/users/${CODER.id}/password-reset`]: {
        url: `${SITE}/reset-password#reset-token`,
        expires_at: "2026-05-02T12:00:00.000Z",
      },
    });
    renderRoute("/admin/users");

    const own = (await screen.findByRole("cell", { name: /^admin/ })).closest("tr")!;
    expect(within(own).getByRole("button", { name: "Deactivate" })).toBeDisabled();
    expect(within(own).getByRole("combobox")).toBeDisabled();

    const row = screen.getByRole("cell", { name: "bob" }).closest("tr")!;
    await user.click(within(row).getByRole("button", { name: "Deactivate" }));
    expect(await within(row).findByText("Deactivated")).toBeVisible();
    expect(api.calls.find((call) => call.method === "PATCH")?.body).toEqual({ active: false });

    await user.click(within(row).getByRole("button", { name: "Activate" }));
    await within(row).findByText("Active");
    await user.click(within(row).getByRole("button", { name: "Password link" }));
    expect(await screen.findByRole("textbox", { name: "Link" })).toHaveValue(
      `${SITE}/reset-password#reset-token`,
    );
    expect(screen.getByText("Link for a new password of bob")).toBeVisible();
  });

  it("changes a role", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: ADMIN },
      "/admin/users": { items: [account(ADMIN), account(CODER)] },
      [`/admin/users/${CODER.id}`]: account(CODER, { role: "admin" }),
    });
    renderRoute("/admin/users");
    await user.selectOptions(await screen.findByRole("combobox", { name: "Role of bob" }), "Admin");
    await screen.findAllByRole("combobox");
    expect(api.calls.find((call) => call.method === "PATCH")?.body).toEqual({ role: "admin" });
  });
});

describe("admin invites", () => {
  it("creates, shows and revokes invites", async () => {
    const user = userEvent.setup();
    const invite: Invite = {
      id: "665f0000000000000000c001",
      role: "admin",
      created_by: "admin",
      created_at: "2026-05-01T12:00:00.000Z",
      expires_at: "2026-05-04T12:00:00.000Z",
    };
    let invites: Invite[] = [{ ...invite, id: "665f0000000000000000c000", created_by: null }];
    const api = mockApi({
      "/session": { user: ADMIN },
      "/admin/invites": (_url: URL, call: ApiCall) => {
        if (call.method === "GET") return { items: invites };
        invites = [invite, ...invites];
        return Response.json({ invite, url: `${SITE}/invite#invite-token` }, { status: 201 });
      },
      [`/admin/invites/${invite.id}`]: () => {
        invites = invites.filter((item) => item.id !== invite.id);
        return NO_CONTENT();
      },
    });
    renderRoute("/admin/invites");

    expect(await screen.findByRole("cell", { name: "Command line" })).toBeVisible();
    await user.selectOptions(screen.getByRole("combobox", { name: "Role" }), "Admin");
    await user.clear(screen.getByRole("spinbutton", { name: "Valid (days)" }));
    await user.type(screen.getByRole("spinbutton", { name: "Valid (days)" }), "3");
    await user.click(screen.getByRole("button", { name: "Create invitation" }));

    expect(await screen.findByRole("textbox", { name: "Link" })).toHaveValue(
      `${SITE}/invite#invite-token`,
    );
    expect(screen.getByText("Invitation link (Admin)")).toBeVisible();
    const post = api.calls.find((call) => call.method === "POST");
    expect(post?.body).toEqual({ role: "admin", valid_days: 3 });

    const row = (await screen.findByRole("cell", { name: "admin" })).closest("tr")!;
    await user.click(within(row).getByRole("button", { name: "Revoke" }));
    await expect.poll(() => screen.queryByRole("cell", { name: "admin" })).toBeNull();
    expect(api.calls.at(-2)?.method).toBe("DELETE");
  });
});

describe("admin audit log", () => {
  it("lists entries and filters by action and target", async () => {
    const user = userEvent.setup();
    const entry: AuditEntry = {
      id: "665f0000000000000000d001",
      at: "2026-05-01T12:00:00.000Z",
      actor: "admin",
      action: "bot.update",
      target: "665f0000000000000000b001",
      details: { status: "disabled", games: 2 },
    };
    const api = mockApi({
      "/session": { user: ADMIN },
      "/admin/audit": {
        items: [entry],
        total: 1,
        actions: ["bot.update", "invite.create"],
        actors: ["admin", "cli"],
      },
    });
    renderRoute("/admin/audit");

    expect(await screen.findByText("status=disabled, games=2")).toBeVisible();
    await user.selectOptions(screen.getByRole("combobox", { name: "Action" }), "bot.update");
    await expect.poll(() => api.requests.at(-1)?.searchParams.get("action")).toBe("bot.update");
    await user.click(screen.getByRole("button", { name: entry.target! }));
    await expect.poll(() => api.requests.at(-1)?.searchParams.get("target")).toBe(entry.target);
    expect(api.requests.at(-1)?.searchParams.get("action")).toBe("bot.update");

    await user.click(screen.getByRole("button", { name: `Remove target ${entry.target}` }));
    await expect.poll(() => api.requests.at(-1)?.searchParams.get("target")).toBeNull();
  });
});
