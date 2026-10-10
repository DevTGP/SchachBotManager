import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { Bot, Opponent, Series } from "../api/types";
import {
  ADMIN,
  BOTS,
  botDetail,
  CODER,
  CODER_LIMITS,
  match,
  ownMatches,
  queue,
  SHARP_ID,
  side,
  storedDiscipline,
  summary,
} from "../test/fixtures";
import { type ApiCall, mockApi, renderRoute } from "../test/render";

const [RANDOM, MATERIAL] = BOTS as [Bot, Bot];
const SERIES_ID = "665f00000000000000000201";
const OLDER_ID = "665f0000000000000000000e";
const FEN = "4k3/8/8/8/8/8/8/4K2R w K - 0 1";

const SHARP: Bot = {
  ...RANDOM,
  id: SHARP_ID,
  name: "Sharp",
  builtin: false,
  status: "verified",
};

describe("matches page filters", () => {
  it("narrows the games to an opponent, a discipline and the own ones", async () => {
    const user = userEvent.setup();
    const blitz = storedDiscipline();
    const api = mockApi({
      "/session": { user: CODER },
      "/matches": { items: [summary()], total: 1 },
      "/bots": { items: BOTS },
      "/disciplines": { items: [blitz] },
    });
    const { router } = renderRoute(`/matches?bot=${RANDOM.id}`);

    const opponent = await screen.findByRole("combobox", { name: "Opponent" });
    await within(opponent).findByRole("option", { name: "Material" });
    // The bot itself is no opponent.
    expect(within(opponent).queryByRole("option", { name: "Random" })).toBeNull();
    await user.selectOptions(opponent, "Material");
    await user.selectOptions(await screen.findByRole("combobox", { name: "Discipline" }), "Blitz");
    await user.click(screen.getByRole("checkbox", { name: "Set by me" }));

    expect(Object.fromEntries(new URLSearchParams(router.state.location.search))).toEqual({
      bot: RANDOM.id,
      opponent: MATERIAL.id,
      discipline: blitz.id,
      mine: "true",
    });
    await waitFor(() => {
      const last = api.requests.filter((url) => url.pathname === "/api/v1/matches").at(-1);
      expect(Object.fromEntries(last?.searchParams ?? [])).toEqual({
        bot_id: RANDOM.id,
        opponent_id: MATERIAL.id,
        discipline_id: blitz.id,
        mine: "true",
        limit: "25",
        offset: "0",
      });
    });

    await user.selectOptions(screen.getByRole("combobox", { name: "Bot" }), "All bots");
    expect(router.state.location.search).toBe(`?discipline=${blitz.id}&mine=true`);
    expect(screen.queryByRole("combobox", { name: "Opponent" })).toBeNull();
  });

  it("offers the own games only to coders and admins", async () => {
    mockApi({
      "/session": { user: null },
      "/matches": { items: [summary()], total: 1 },
      "/bots": { items: BOTS },
    });
    renderRoute("/matches?mine=true");

    await screen.findByText("0–1");
    expect(screen.queryByRole("checkbox", { name: "Set by me" })).toBeNull();
  });
});

describe("series", () => {
  function series(overrides: Partial<Series> = {}): Series {
    const [first, second] = [
      summary({ id: "665f00000000000000000101", series: { id: SERIES_ID, index: 1, games: 2 } }),
      summary({
        id: "665f00000000000000000102",
        white: side("Material", MATERIAL.id),
        black: side("Random", RANDOM.id),
        result: "1/2-1/2",
        series: { id: SERIES_ID, index: 2, games: 2 },
      }),
    ];
    return {
      id: SERIES_ID,
      games: 2,
      a: { bot_id: RANDOM.id, name: "Random", version: "1.0.0", points: 0.5 },
      b: { bot_id: MATERIAL.id, name: "Material", version: "1.0.0", points: 1.5 },
      counted: 2,
      matches: [first!, second!],
      ...overrides,
    };
  }

  it("shows the score and the games", async () => {
    mockApi({ [`/series/${SERIES_ID}`]: series() });
    renderRoute(`/series/${SERIES_ID}`);

    expect(await screen.findByRole("heading", { name: "Series" })).toBeVisible();
    expect(screen.getByText("½ – 1½")).toBeVisible();
    expect(screen.getByRole("link", { name: "Random 1.0.0" })).toHaveAttribute(
      "href",
      `/bots/${RANDOM.id}`,
    );
    expect(screen.getByText("2 of 2 games finished")).toBeVisible();
    expect(screen.getAllByRole("link", { name: /–/ })).toHaveLength(2);
  });

  it("links a game to its series", async () => {
    mockApi({
      "/matches/665f00000000000000000001": match({
        series: { id: SERIES_ID, index: 2, games: 3 },
      }),
    });
    renderRoute("/matches/665f00000000000000000001");

    expect(await screen.findByText(/Game 2 of 3 in a series/)).toBeVisible();
    expect(screen.getByRole("link", { name: "View series" })).toHaveAttribute(
      "href",
      `/series/${SERIES_ID}`,
    );
  });
});

describe("own waiting games", () => {
  it("withdraws a waiting game", async () => {
    const user = userEvent.setup();
    let waiting = [summary({ status: "queued", white: side("Sharp", SHARP_ID), result: null })];
    const api = mockApi({
      "/session": { user: CODER },
      "/account/bots": { items: [SHARP] },
      "/account/limits": CODER_LIMITS,
      "/bots": { items: [...BOTS, SHARP] },
      "/matches": (url: URL, call: ApiCall) => ownMatches(null, waiting)(url, call),
      "/matches/665f00000000000000000001/withdraw": () => {
        waiting = [];
        return new Response(null, { status: 204 });
      },
    });
    renderRoute("/account/bots");

    const section = (await screen.findByRole("heading", { name: "Waiting games" })).closest(
      "section",
    )!;
    expect(await within(section).findByRole("link", { name: /Sharp 1\.0\.0/ })).toBeVisible();
    await user.click(within(section).getByRole("button", { name: "Withdraw" }));

    expect(await within(section).findByText("None of your games is waiting.")).toBeVisible();
    const post = api.calls.find((call) => call.method === "POST");
    expect(post?.url.pathname).toBe("/api/v1/matches/665f00000000000000000001/withdraw");
    expect(post?.headers.get("X-SBM-CSRF")).toBe("1");
    const list = api.requests.find((url) => url.pathname === "/api/v1/matches");
    expect(list?.searchParams.get("mine")).toBe("true");
    expect(list?.searchParams.get("status")).toBe("queued");
  });

  it("queues games from a start position, unrated", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: CODER },
      "/account/bots": { items: [SHARP] },
      "/account/limits": CODER_LIMITS,
      "/bots": { items: [...BOTS, SHARP] },
      "/matches": ownMatches({ match_ids: ["665f00000000000000000101"], series_id: null }),
    });
    renderRoute("/account/bots");

    await user.type(
      await screen.findByRole("textbox", { name: "Start position (FEN, optional)" }),
      FEN,
    );
    await user.click(screen.getByRole("checkbox", { name: "Rated" }));
    await user.click(screen.getByRole("button", { name: "Add to queue" }));

    expect(await screen.findByRole("status")).toHaveTextContent("1 game queued.");
    expect(screen.queryByRole("link", { name: "View series" })).toBeNull();
    const post = api.calls.find((call) => call.method === "POST");
    expect(post?.body).toMatchObject({ start_fen: FEN, rated: false });
  });
});

describe("start position from a PGN", () => {
  function setup(answer: unknown) {
    return mockApi({
      "/session": { user: ADMIN },
      "/bots": { items: BOTS },
      "/queue": queue(),
      "/positions/from-pgn": answer,
    });
  }

  it("fills in the FEN after some half-moves", async () => {
    const user = userEvent.setup();
    const api = setup({ fen: FEN });
    renderRoute("/admin");

    await user.click(await screen.findByText("From PGN"));
    await user.type(screen.getByRole("textbox", { name: "PGN" }), "1. e4 e5 *");
    const game = screen.getByRole("spinbutton", { name: "Game no." });
    await user.clear(game);
    await user.type(game, "2");
    await user.type(screen.getByRole("spinbutton", { name: "Half-moves" }), "1");
    await user.click(screen.getByRole("button", { name: "Insert FEN" }));

    await waitFor(() =>
      expect(screen.getByRole("textbox", { name: "Start position (FEN, optional)" })).toHaveValue(
        FEN,
      ),
    );
    const post = api.calls.find((call) => call.url.pathname === "/api/v1/positions/from-pgn");
    expect(post?.body).toEqual({ pgn: "1. e4 e5 *", game: 2, plies: 1 });
  });

  it("names what is wrong with the PGN", async () => {
    const user = userEvent.setup();
    setup(
      Response.json(
        { code: "invalid_parameter", message: "short", field: "plies" },
        { status: 400 },
      ),
    );
    renderRoute("/admin");

    await user.click(await screen.findByText("From PGN"));
    await user.type(screen.getByRole("textbox", { name: "PGN" }), "1. e4 *");
    await user.click(screen.getByRole("button", { name: "Insert FEN" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("The game has fewer half-moves.");
  });
});

describe("quick start", () => {
  const older: Bot = { ...SHARP, id: OLDER_ID, version: "0.9.0" };

  it("presets the admin form from the address", async () => {
    mockApi({
      "/session": { user: ADMIN },
      "/bots": { items: BOTS },
      "/queue": queue(),
    });
    renderRoute(`/admin?white=${MATERIAL.id}&black=${RANDOM.id}`);

    await screen.findByRole("option", { name: "Material", selected: true });
    expect(screen.getByRole("combobox", { name: "White" })).toHaveValue(MATERIAL.id);
    expect(screen.getByRole("combobox", { name: "Black" })).toHaveValue(RANDOM.id);
  });

  it("presets the own form from the address", async () => {
    mockApi({
      "/session": { user: CODER },
      "/account/bots": { items: [SHARP, older] },
      "/account/limits": CODER_LIMITS,
      "/bots": { items: [...BOTS, SHARP, older] },
      "/matches": ownMatches(null),
    });
    renderRoute(`/account/bots?own=${OLDER_ID}&opponent=${SHARP_ID}`);

    expect(await screen.findByRole("combobox", { name: "Your bot" })).toHaveValue(OLDER_ID);
    expect(screen.getByRole("combobox", { name: "Opponent" })).toHaveValue(SHARP_ID);
  });

  it("leads the owner from a version to the own form", async () => {
    mockApi({
      "/session": { user: CODER },
      [`/bots/${SHARP_ID}`]: botDetail({ status: "verified", versions: [SHARP, older] }),
    });
    renderRoute(`/bots/${SHARP_ID}`);

    const expected = `/account/bots?own=${SHARP_ID}&opponent=${OLDER_ID}`;
    expect(
      await screen.findByRole("link", { name: "Play against the predecessor" }),
    ).toHaveAttribute("href", expected);
    const main = screen.getByRole("main");
    expect(within(main).getByRole("link", { name: "Play" })).toHaveAttribute("href", expected);
  });

  it("leads admins to the admin form", async () => {
    mockApi({
      "/session": { user: ADMIN },
      [`/bots/${SHARP_ID}`]: botDetail({ status: "verified", versions: [SHARP, older] }),
    });
    renderRoute(`/bots/${SHARP_ID}`);

    const versions = await screen.findByRole("link", { name: "0.9.0" });
    expect(within(versions.closest("tr")!).getByRole("link", { name: "Play" })).toHaveAttribute(
      "href",
      `/admin?white=${SHARP_ID}&black=${OLDER_ID}`,
    );
  });

  it("offers nothing to guests", async () => {
    mockApi({
      "/session": { user: null },
      [`/bots/${SHARP_ID}`]: botDetail({
        status: "verified",
        details: null,
        versions: [SHARP, older],
      }),
    });
    renderRoute(`/bots/${SHARP_ID}`);

    await screen.findByRole("link", { name: "0.9.0" });
    expect(within(screen.getByRole("main")).queryByRole("link", { name: /Play/ })).toBeNull();
  });
});

describe("record", () => {
  it("lists the results against each opponent", async () => {
    const opponent: Opponent = {
      bot_id: MATERIAL.id,
      name: "Material",
      version: "1.0.0",
      games: 5,
      wins: 1,
      draws: 3,
      losses: 1,
    };
    mockApi({
      "/session": { user: null },
      [`/bots/${SHARP_ID}`]: botDetail({ status: "verified", details: null }),
      [`/bots/${SHARP_ID}/opponents`]: { items: [opponent] },
    });
    renderRoute(`/bots/${SHARP_ID}`);

    const row = (await screen.findByRole("link", { name: "Material 1.0.0" })).closest("tr")!;
    expect(within(row).getByRole("link", { name: "5" })).toHaveAttribute(
      "href",
      `/matches?bot=${SHARP_ID}&opponent=${MATERIAL.id}`,
    );
    expect(within(row).getByText("3")).toBeVisible();
  });

  it("explains an empty record", async () => {
    mockApi({
      "/session": { user: null },
      [`/bots/${SHARP_ID}`]: botDetail({ status: "verified", details: null }),
      [`/bots/${SHARP_ID}/opponents`]: { items: [] },
    });
    renderRoute(`/bots/${SHARP_ID}`);

    expect(await screen.findByText("No finished games against other bots yet.")).toBeVisible();
  });
});
