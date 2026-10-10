import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ADMIN, adminSettings } from "../test/fixtures";
import { type ApiCall, mockApi, renderRoute } from "../test/render";

function section(name: string) {
  return screen.getByRole("heading", { name }).closest("section")!;
}

describe("admin settings", () => {
  it("saves a group with times typed in seconds", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: ADMIN },
      "/admin/settings": adminSettings(),
      "/admin/settings/coders": (_url: URL, call: ApiCall) =>
        adminSettings({ coders: call.body as ReturnType<typeof adminSettings>["coders"] }),
    });
    renderRoute("/admin/settings");

    expect(await screen.findByRole("link", { name: "Settings" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    await screen.findByRole("heading", { name: "Limits for coders" });
    const coders = section("Limits for coders");
    const time = within(coders).getByRole("spinbutton", { name: "Free time at most (s)" });
    expect(time).toHaveValue(300);
    await user.clear(time);
    await user.type(time, "600");
    await user.click(within(coders).getByRole("button", { name: "Save" }));

    expect(await within(coders).findByText("Saved.")).toBeVisible();
    const put = api.calls.find((call) => call.method === "PUT");
    expect(put?.url.pathname).toBe("/api/v1/admin/settings/coders");
    expect(put?.body).toEqual({
      games_per_day: 20,
      uploads_per_day: 20,
      games_per_request: 10,
      max_initial_ms: 600_000,
      max_increment_ms: 5_000,
      priority: 50,
    });
  });

  it("shows a running recount after a new rating rule", async () => {
    const user = userEvent.setup();
    mockApi({
      "/session": { user: ADMIN },
      "/admin/settings": adminSettings(),
      "/admin/settings/rating": adminSettings({ rating_recount_pending: true }),
    });
    renderRoute("/admin/settings");

    await screen.findByRole("heading", { name: "Rating" });
    const start = within(section("Rating")).getByRole("spinbutton", { name: "Start value" });
    await user.clear(start);
    await user.type(start, "1500");
    await user.click(within(section("Rating")).getByRole("button", { name: "Save" }));

    expect(await screen.findByText("The ratings are being counted again.")).toBeVisible();
  });

  it("explains values that do not fit together", async () => {
    const user = userEvent.setup();
    mockApi({
      "/session": { user: ADMIN },
      "/admin/settings": adminSettings(),
      "/admin/settings/accounts": Response.json(
        {
          code: "invalid_parameter",
          message: "invite_days must not exceed invite_max_days",
          field: "invite_days",
        },
        { status: 400 },
      ),
    });
    renderRoute("/admin/settings");

    await screen.findByRole("heading", { name: "Invitations and accounts" });
    const accounts = section("Invitations and accounts");
    await user.click(within(accounts).getByRole("button", { name: "Save" }));

    expect(await within(accounts).findByRole("alert")).toHaveTextContent(
      "The default validity must not exceed the longest.",
    );
  });
});
