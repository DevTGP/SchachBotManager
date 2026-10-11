import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { BotRecord, DisciplineRatingHistory } from "../api/types";
import { SHARP_ID, botDetail } from "../test/fixtures";
import { LEAGUE_ID, SEASON_ID, botSeason, schedule, season } from "../test/leagues";
import { mockApi, renderRoute } from "../test/render";

function history(name: string, afters: number[]): DisciplineRatingHistory {
  let before = 1500;
  return {
    discipline_id: `d-${name}`,
    name,
    games: afters.map((after, index) => {
      const point = {
        match_id: `${name}-${index}`,
        finished_at: "2026-05-01T10:00:00.000Z",
        before,
        after,
      };
      before = after;
      return point;
    }),
  };
}

const RECORD: BotRecord = {
  total: { games: 5, wins: 3, draws: 1, losses: 1 },
  disciplines: [
    { discipline_id: "d-Blitz", name: "Blitz", games: 4, wins: 3, draws: 1, losses: 0 },
    { discipline_id: null, name: null, games: 1, wins: 0, draws: 0, losses: 1 },
  ],
};

/** The API of the page of Sharp with the history given. */
function botApi(extra: Record<string, unknown> = {}) {
  return mockApi({
    "/session": { user: null },
    [`/bots/${SHARP_ID}`]: botDetail({ status: "verified" }),
    [`/bots/${SHARP_ID}/opponents`]: { items: [] },
    [`/bots/${SHARP_ID}/leagues`]: { items: [] },
    [`/bots/${SHARP_ID}/seasons`]: { items: [] },
    [`/bots/${SHARP_ID}/rating-history`]: { items: [] },
    [`/bots/${SHARP_ID}/record`]: {
      total: { games: 0, wins: 0, draws: 0, losses: 0 },
      disciplines: [],
    },
    ...extra,
  });
}

describe("schedule of a season", () => {
  it("shows the rounds of a tier with results, forfeits and byes", async () => {
    const api = mockApi({
      "/session": { user: null },
      [`/seasons/${SEASON_ID}`]: season({ status: "running", finished_at: null }),
      [`/seasons/${SEASON_ID}/schedule`]: schedule(),
    });
    renderRoute(`/seasons/${SEASON_ID}`);

    expect(await screen.findByRole("heading", { name: "Schedule" })).toBeVisible();
    const request = api.requests.find((url) => url.pathname.endsWith("/schedule"))!;
    expect(request.searchParams.get("tier")).toBe("1");

    const first = (await screen.findByText("Round 1")).closest("details")!;
    expect(first).not.toHaveAttribute("open");
    expect(within(first).getByText("· 1 of 1 finished")).toBeInTheDocument();
    expect(within(first).getByRole("link", { name: "0–1 by forfeit" })).toHaveAttribute(
      "href",
      "/matches/m1",
    );

    const second = screen.getByText("Round 2").closest("details")!;
    expect(second).toHaveAttribute("open");
    expect(within(second).getByRole("link", { name: "Waiting" })).toHaveAttribute(
      "href",
      "/matches/m2",
    );
    expect(within(second).getByText("Bye: Sharp 1.0.0")).toBeVisible();
  });

  it("says when a tier has no games", async () => {
    mockApi({
      "/session": { user: null },
      [`/seasons/${SEASON_ID}`]: season(),
      [`/seasons/${SEASON_ID}/schedule`]: { tier: 1, rounds: [] },
    });
    renderRoute(`/seasons/${SEASON_ID}`);

    expect(await screen.findByText("No games in this tier.")).toBeVisible();
  });
});

describe("history of a bot", () => {
  it("lists the league seasons of the version with its place", async () => {
    botApi({
      [`/bots/${SHARP_ID}/seasons`]: {
        items: [
          botSeason({
            season_id: "s2",
            number: 2,
            status: "running",
            finished_at: null,
            rank: 1,
            games: 2,
            points: 2,
            outcome: null,
          }),
          botSeason(),
        ],
      },
    });
    renderRoute(`/bots/${SHARP_ID}`);

    const running = (await screen.findByRole("link", { name: "Season 2" })).closest("tr")!;
    expect(running).toHaveTextContent("1 of 4");
    expect(within(running).getByText("Running")).toBeVisible();
    const finished = screen.getByRole("link", { name: "Season 1" }).closest("tr")!;
    expect(finished).toHaveTextContent("2 of 4");
    expect(within(finished).getByText("3½")).toBeVisible();
    expect(within(finished).getByText("Stays")).toBeVisible();
    expect(within(finished).getByRole("link", { name: "Bundesliga" })).toHaveAttribute(
      "href",
      `/leagues/${LEAGUE_ID}`,
    );
  });

  it("says when the version has played nothing yet", async () => {
    botApi();
    renderRoute(`/bots/${SHARP_ID}`);

    expect(
      await screen.findByText("This version has not played in a league season yet."),
    ).toBeVisible();
    expect(screen.getByText("No rated game yet.")).toBeVisible();
    expect(screen.getByText("No finished games yet.")).toBeVisible();
  });

  it("counts the results per discipline and in total", async () => {
    botApi({ [`/bots/${SHARP_ID}/record`]: RECORD });
    renderRoute(`/bots/${SHARP_ID}`);

    const blitz = (await screen.findByRole("rowheader", { name: "Blitz" })).closest("tr")!;
    expect(
      within(blitz)
        .getAllByRole("cell")
        .map((cell) => cell.textContent),
    ).toEqual(["4", "3", "1", "0"]);
    expect(screen.getByRole("rowheader", { name: "Free time control" })).toBeVisible();
    const total = screen.getByRole("rowheader", { name: "Total" }).closest("tr")!;
    expect(
      within(total)
        .getAllByRole("cell")
        .map((cell) => cell.textContent),
    ).toEqual(["5", "3", "1", "1"]);
  });

  it("draws the rating curve of the chosen discipline", async () => {
    const user = userEvent.setup();
    botApi({
      [`/bots/${SHARP_ID}/rating-history`]: {
        items: [history("Blitz", [1510, 1530, 1520]), history("Rapid", [1490])],
      },
    });
    renderRoute(`/bots/${SHARP_ID}`);

    expect(await screen.findByRole("img", { name: "Rating in Blitz over 3 games" })).toBeVisible();
    expect(screen.getByText("Now 1520 after 3 games; highest 1530, lowest 1500.")).toBeVisible();
    expect(screen.getByText("After game 2: 1530")).toBeInTheDocument();

    await user.selectOptions(screen.getByRole("combobox", { name: "Discipline" }), "Rapid");
    expect(screen.getByRole("img", { name: "Rating in Rapid over 1 games" })).toBeVisible();
    expect(screen.getByText("Start: 1500")).toBeInTheDocument();
  });
});
