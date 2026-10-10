import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { Bot, BotDetail, BotDetails, VerificationReport } from "../api/types";
import { ADMIN, BOTS, CODER, botDetail, queue, SHARP_ID } from "../test/fixtures";
import { mockApi, renderRoute } from "../test/render";

/** The bot with some of its details changed. */
function withDetails(status: Bot["status"], change: Partial<BotDetails>): BotDetail {
  const bot = botDetail({ status });
  return bot.details ? { ...bot, details: { ...bot.details, ...change } } : bot;
}

describe("rechecks on the bot page", () => {
  it("lets admins check a bot again and shows that the recheck waits", async () => {
    const user = userEvent.setup();
    let pending = false;
    const api = mockApi({
      "/session": { user: ADMIN },
      [`/bots/${SHARP_ID}`]: () => withDetails("verified", { recheck_pending: pending }),
      [`/admin/bots/${SHARP_ID}/recheck`]: () => {
        pending = true;
        return withDetails("verified", { recheck_pending: true });
      },
    });
    renderRoute(`/bots/${SHARP_ID}`);

    await user.click(await screen.findByRole("button", { name: "Check again" }));

    expect(await screen.findByText(/A recheck is waiting or running/)).toBeVisible();
    expect(screen.queryByRole("button", { name: "Check again" })).toBeNull();
    const post = api.calls.find((call) => call.method === "POST");
    expect(post?.url.pathname).toBe(`/api/v1/admin/bots/${SHARP_ID}/recheck`);
  });

  it("shows the owner the rechecks with their stages", async () => {
    const user = userEvent.setup();
    const recheck: VerificationReport = {
      result: "passed",
      ruleset: "python-2",
      runtime: {},
      started_at: "2026-06-01T09:59:00.000Z",
      finished_at: "2026-06-01T10:00:00.000Z",
      stages: [{ stage: "analysis", status: "passed", duration_ms: 900, problem: null }],
    };
    mockApi({
      "/session": { user: CODER },
      [`/bots/${SHARP_ID}`]: withDetails("rejected", { rechecks: [recheck] }),
    });
    renderRoute(`/bots/${SHARP_ID}`);

    const section = await screen.findByRole("heading", { name: "Rechecks" });
    const summary = screen.getByText(/Rules python-2/);
    await user.click(summary);

    expect(section).toBeVisible();
    expect(screen.getByText(/Static analysis: Passed/)).toBeVisible();
    expect(screen.queryByRole("button", { name: "Check again" })).toBeNull();
  });

  it("offers no recheck for reference bots", async () => {
    mockApi({
      "/session": { user: ADMIN },
      [`/bots/${SHARP_ID}`]: botDetail({ status: "verified", builtin: true }),
    });
    renderRoute(`/bots/${SHARP_ID}`);
    expect(await screen.findByRole("button", { name: "Disable" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Check again" })).toBeNull();
  });
});

describe("override on the bot page", () => {
  it("lets admins verify a rejected bot anyway after asking", async () => {
    const user = userEvent.setup();
    let status: Bot["status"] = "rejected";
    const at = "2026-06-02T10:00:00.000Z";
    const api = mockApi({
      "/session": { user: ADMIN },
      [`/bots/${SHARP_ID}`]: () =>
        withDetails(status, { overridden_at: status === "verified" ? at : null }),
      [`/admin/bots/${SHARP_ID}/override`]: () => {
        status = "verified";
        return withDetails(status, { overridden_at: at });
      },
    });
    renderRoute(`/bots/${SHARP_ID}`);

    await user.click(await screen.findByRole("button", { name: "Verify anyway" }));
    expect(screen.getByText(/may play although the verification rejected it/)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Yes, verify anyway" }));

    expect(await screen.findByText("Verified anyway")).toBeVisible();
    expect(screen.getByText("Static analysis: 1 finding")).toBeVisible();
    expect(screen.queryByRole("button", { name: "Verify anyway" })).toBeNull();
    const post = api.calls.find((call) => call.method === "POST");
    expect(post?.url.pathname).toBe(`/api/v1/admin/bots/${SHARP_ID}/override`);
  });
});

describe("rechecks of a language", () => {
  it("queues the bots of the chosen language", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: ADMIN },
      "/bots": { items: BOTS },
      "/queue": queue(),
      "/admin/bots/recheck": { queued: 3 },
    });
    renderRoute("/admin");

    const section = (await screen.findByRole("heading", { name: "Check bots again" }))
      .parentElement;
    if (!section) throw new Error("no section");
    await user.selectOptions(within(section).getByRole("combobox", { name: "Language" }), "cpp");
    await user.click(within(section).getByRole("button", { name: "Check again" }));

    expect(await screen.findByText("3 rechecks queued.")).toBeVisible();
    const post = api.calls.find((call) => call.url.pathname === "/api/v1/admin/bots/recheck");
    expect(post?.body).toEqual({ language: "cpp" });
  });
});
