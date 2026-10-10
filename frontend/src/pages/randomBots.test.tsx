import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { Bot } from "../api/types";
import { ADMIN, BOTS, CODER, CODER_LIMITS, ownMatches, queue } from "../test/fixtures";
import { type ApiCall, mockApi, renderRoute } from "../test/render";

const SHARP: Bot = {
  ...BOTS[0]!,
  id: "665f0000000000000000001a",
  name: "Sharp",
  builtin: false,
  owner: "coder",
};

function posted(calls: ApiCall[], path: string): unknown {
  return calls.find((call) => call.method === "POST" && call.url.pathname === path)?.body;
}

describe("random bots", () => {
  it("lets admins draw both sides for every game", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: ADMIN },
      "/bots": { items: BOTS },
      "/queue": queue(),
      "/admin/matches": {
        match_ids: Array.from({ length: 10 }, (_, i) => `m${i}`),
        series_id: null,
      },
    });
    renderRoute("/admin");

    const white = await screen.findByRole("combobox", { name: "White" });
    await user.selectOptions(white, "Random");
    await user.selectOptions(screen.getByRole("combobox", { name: "Black" }), "Random");
    const games = screen.getByRole("spinbutton", { name: "Games" });
    await user.clear(games);
    await user.type(games, "10");
    await user.click(screen.getByRole("button", { name: "Add to queue" }));

    expect(await screen.findByText("10 games queued.")).toBeVisible();
    expect(screen.queryByRole("link", { name: "View series" })).toBeNull();
    expect(posted(api.calls, "/api/v1/admin/matches")).toMatchObject({
      white_bot_id: "random",
      black_bot_id: "random",
      games: 10,
    });
  });

  it("lets coders draw the opponent", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: CODER },
      "/account/bots": { items: [SHARP] },
      "/account/limits": CODER_LIMITS,
      "/bots": { items: [...BOTS, SHARP] },
      "/matches": ownMatches({ match_ids: ["m1", "m2"], series_id: null }),
    });
    renderRoute("/account/bots");

    await user.selectOptions(await screen.findByRole("combobox", { name: "Opponent" }), "Random");
    await user.click(screen.getByRole("button", { name: "Add to queue" }));

    expect(await screen.findByRole("status")).toHaveTextContent("2 games queued.");
    expect(posted(api.calls, "/api/v1/matches")).toMatchObject({
      white_bot_id: SHARP.id,
      black_bot_id: "random",
    });
  });

  it("lets people play against a random bot", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: null },
      "/bots": { items: BOTS },
      "/disciplines": { items: [] },
      "/play": () =>
        Response.json(
          { match_id: "m1", seat: "s", color: "white", socket_path: "/api/v1/play/socket" },
          { status: 201 },
        ),
    });
    const { router } = renderRoute("/play");

    await user.selectOptions(await screen.findByRole("combobox", { name: "Bot" }), "Random");
    await user.click(screen.getByRole("button", { name: "Start game" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/play/m1"));
    expect(posted(api.calls, "/api/v1/play")).toMatchObject({ bot_id: "random" });
  });
});
