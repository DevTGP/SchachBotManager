import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { Bot } from "../api/types";
import { BOTS, CODER, CODER_LIMITS, ownMatches } from "../test/fixtures";
import { type ApiCall, mockApi, renderRoute } from "../test/render";

function own(id: string, name: string, version: string, status: Bot["status"]): Bot {
  return {
    id,
    name,
    version,
    language: "python",
    status,
    builtin: false,
    description: "",
    rating: { value: 2500, games: 0 },
    created_at: "2026-05-01T10:00:00.000Z",
  };
}

const SHARP_NEW = own("665f0000000000000000001a", "Sharp", "1.1.0", "verified");
const SHARP_OLD = own("665f0000000000000000001b", "Sharp", "1.0.0", "retired");
const BLUNT = own("665f0000000000000000001c", "Blunt", "0.1.0", "rejected");
const FOREIGN = own("665f0000000000000000001d", "Foreign", "2.0.0", "verified");

describe("my bots page", () => {
  it("groups the versions by name", async () => {
    mockApi({
      "/session": { user: CODER },
      "/account/bots": { items: [SHARP_NEW, BLUNT, SHARP_OLD] },
      "/bots": { items: [...BOTS, SHARP_NEW, FOREIGN] },
    });
    renderRoute("/account/bots");

    const sharp = await screen.findByRole("rowheader", { name: "Sharp" });
    expect(sharp).toHaveAttribute("rowspan", "2");
    const group = sharp.closest("tbody")!;
    expect(within(group).getByRole("link", { name: "Sharp 1.1.0" })).toHaveAttribute(
      "href",
      `/bots/${SHARP_NEW.id}`,
    );
    expect(within(group).getByText("Withdrawn")).toBeVisible();
    expect(screen.getByRole("rowheader", { name: "Blunt" })).toHaveAttribute("rowspan", "1");
    expect(screen.getByRole("link", { name: "Upload bot" })).toHaveAttribute("href", "/bots/new");
    expect(screen.getByRole("link", { name: "My bots" })).toHaveAttribute("aria-current", "page");
  });

  it("schedules games of an own bot against any verified bot", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: CODER },
      "/account/bots": { items: [SHARP_NEW, SHARP_OLD] },
      "/account/limits": CODER_LIMITS,
      "/bots": { items: [...BOTS, SHARP_NEW, FOREIGN] },
      "/matches": ownMatches({
        match_ids: ["665f00000000000000000101", "665f00000000000000000102"],
        series_id: "665f00000000000000000201",
      }),
    });
    renderRoute("/account/bots");

    const ownBot = await screen.findByRole("combobox", { name: "Your bot" });
    // Only the verified version can play.
    expect(
      within(ownBot)
        .getAllByRole("option")
        .map((option) => option.textContent),
    ).toEqual(["Sharp 1.1.0"]);
    expect(screen.getByRole("combobox", { name: "Opponent" })).toHaveValue(BOTS[0]!.id);
    await user.selectOptions(screen.getByRole("combobox", { name: "Opponent" }), "Foreign 2.0.0");
    await user.selectOptions(screen.getByRole("combobox", { name: "Your bot plays" }), "Black");
    expect(screen.getByRole("spinbutton", { name: "Time (s)" })).toHaveAttribute("max", "300");
    await user.click(screen.getByRole("button", { name: "Add to queue" }));

    expect(await screen.findByRole("status")).toHaveTextContent("2 games queued.");
    const post = api.calls.find((call: ApiCall) => call.method === "POST");
    expect(post?.url.pathname).toBe("/api/v1/matches");
    expect(post?.body).toEqual({
      white_bot_id: FOREIGN.id,
      black_bot_id: SHARP_NEW.id,
      initial_time_ms: 60_000,
      increment_ms: 1_000,
      games: 2,
      alternate: true,
      rated: true,
    });
  });

  it("explains a refused request with the coder limits", async () => {
    const user = userEvent.setup();
    mockApi({
      "/session": { user: CODER },
      "/account/bots": { items: [SHARP_NEW] },
      "/account/limits": { ...CODER_LIMITS, max_initial_ms: 600_000, games_per_day: 50 },
      "/bots": { items: BOTS },
      "/matches": ownMatches(
        Response.json(
          { code: "invalid_parameter", message: "too long", field: "initial_time_ms" },
          { status: 400 },
        ),
      ),
    });
    renderRoute("/account/bots");

    await user.click(await screen.findByRole("button", { name: "Add to queue" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The time must be between 1 and 600 seconds.",
    );
    expect(screen.getByRole("spinbutton", { name: "Time (s)" })).toHaveAttribute("max", "600");
    expect(screen.getByText(/at most 600 seconds plus 5 seconds/)).toHaveTextContent(
      "At most 10 games at once and 50 games a day.",
    );
  });

  it("needs a verified own bot for games", async () => {
    mockApi({
      "/session": { user: CODER },
      "/account/bots": { items: [BLUNT] },
      "/account/limits": CODER_LIMITS,
      "/bots": { items: BOTS },
    });
    renderRoute("/account/bots");

    expect(
      await screen.findByText(
        "Once one of your bots is verified, you can schedule games for it here.",
      ),
    ).toBeVisible();
    expect(screen.queryByRole("button", { name: "Add to queue" })).toBeNull();
  });

  it("is only for accounts", async () => {
    mockApi({ "/session": { user: null } });
    const { router } = renderRoute("/account/bots");
    await screen.findByRole("button", { name: "Log in" });
    expect(router.state.location.pathname).toBe("/login");
  });
});
