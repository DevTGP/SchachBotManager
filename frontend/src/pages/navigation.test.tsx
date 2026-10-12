import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { LeaguePlace, TournamentPlace } from "../api/types";
import { BOTS, match, queue, summary } from "../test/fixtures";
import { LEAGUE_ID, SEASON_ID, league, leagueDetail, schedule, season } from "../test/leagues";
import { mockApi, renderRoute } from "../test/render";
import { EDITION_ID, TOURNAMENT_ID, tournament, tournamentDetail } from "../test/tournaments";

const LEAGUE_PLACE: LeaguePlace = {
  league_id: LEAGUE_ID,
  league_name: "Bundesliga",
  season_id: SEASON_ID,
  season_number: 3,
  tier: 2,
  round: 4,
  board: 1,
};
const TOURNAMENT_PLACE: TournamentPlace = {
  tournament_id: TOURNAMENT_ID,
  tournament_name: "Herbstcup",
  edition_id: EDITION_ID,
  edition_number: 2,
  format: "swiss",
  round: 3,
  board: 1,
  phase: null,
  game: null,
};
const OTHER_SEASON = "665f0000000000000000f002";
const NEXT_SEASON = "665f0000000000000000f003";

describe("links to the current season and edition", () => {
  it("links the season in the league list", async () => {
    mockApi({ "/session": { user: null }, "/leagues": { items: [league()] } });
    renderRoute("/leagues");

    expect(await screen.findByRole("link", { name: "Season 1: Planned" })).toHaveAttribute(
      "href",
      `/seasons/${SEASON_ID}`,
    );
  });

  it("names the current season under the title of a league", async () => {
    mockApi({ "/session": { user: null }, [`/leagues/${LEAGUE_ID}`]: leagueDetail() });
    renderRoute(`/leagues/${LEAGUE_ID}`);

    const current = (await screen.findByText("Current season:")).closest("p")!;
    expect(within(current).getByRole("link", { name: "Season 1: Planned" })).toHaveAttribute(
      "href",
      `/seasons/${SEASON_ID}`,
    );
  });

  it("links the edition in the tournament list and on the tournament page", async () => {
    mockApi({
      "/session": { user: null },
      "/tournaments": { items: [tournament()] },
      [`/tournaments/${TOURNAMENT_ID}`]: tournamentDetail(),
    });
    renderRoute("/tournaments");

    expect(await screen.findByRole("link", { name: "Edition 1: Planned" })).toHaveAttribute(
      "href",
      `/editions/${EDITION_ID}`,
    );

    renderRoute(`/tournaments/${TOURNAMENT_ID}`);
    const current = (await screen.findByText("Current edition:")).closest("p")!;
    expect(within(current).getByRole("link")).toHaveAttribute("href", `/editions/${EDITION_ID}`);
  });
});

describe("moving within a season", () => {
  it("jumps to the tiers and to the seasons before and after", async () => {
    const [tier] = season().tiers;
    const seasons = [
      { ...league().season!, id: OTHER_SEASON, number: 1 },
      { ...league().season!, id: SEASON_ID, number: 2 },
      { ...league().season!, id: NEXT_SEASON, number: 3 },
    ];
    mockApi({
      "/session": { user: null },
      [`/seasons/${SEASON_ID}`]: season({ number: 2, tiers: [tier!, { ...tier!, tier: 2 }] }),
      [`/seasons/${SEASON_ID}/schedule`]: schedule(),
      [`/leagues/${LEAGUE_ID}`]: leagueDetail({ seasons }),
    });
    renderRoute(`/seasons/${SEASON_ID}`);

    expect(await screen.findByRole("link", { name: "← Season 1" })).toHaveAttribute(
      "href",
      `/seasons/${OTHER_SEASON}`,
    );
    expect(screen.getByRole("link", { name: "Season 3 →" })).toHaveAttribute(
      "href",
      `/seasons/${NEXT_SEASON}`,
    );
    const jumps = screen.getByRole("navigation", { name: "Tiers" });
    expect(
      within(jumps)
        .getAllByRole("link")
        .map((link) => link.getAttribute("href")),
    ).toEqual(["#tier-1", "#tier-2"]);
    expect(document.getElementById("tier-2")).not.toBeNull();
  });

  it("leaves out the jumps for a single tier and the neighbours of a lone season", async () => {
    mockApi({
      "/session": { user: null },
      [`/seasons/${SEASON_ID}`]: season(),
      [`/seasons/${SEASON_ID}/schedule`]: schedule(),
      [`/leagues/${LEAGUE_ID}`]: leagueDetail(),
    });
    renderRoute(`/seasons/${SEASON_ID}`);

    await screen.findAllByText("Round 1");
    expect(screen.queryByRole("navigation", { name: "Tiers" })).toBeNull();
    expect(screen.queryByRole("link", { name: /Season \d →/ })).toBeNull();
  });

  it("opens the round a link names", async () => {
    mockApi({
      "/session": { user: null },
      [`/seasons/${SEASON_ID}`]: season({ status: "running", finished_at: null }),
      [`/seasons/${SEASON_ID}/schedule`]: schedule(),
    });
    renderRoute(`/seasons/${SEASON_ID}#tier-1-round-1`);

    const first = (await screen.findByText("Round 1")).closest("details")!;
    expect(first).toHaveAttribute("id", "tier-1-round-1");
    expect(first).toHaveAttribute("open");
  });
});

describe("the competition of a game", () => {
  it("shows season and round above the board", async () => {
    mockApi({
      "/session": { user: null },
      "/matches/m1": match({ id: "m1", league: LEAGUE_PLACE }),
    });
    renderRoute("/matches/m1");

    const place = await screen.findByRole("link", { name: "tier 2, round 4, board 1" });
    expect(place).toHaveAttribute("href", `/seasons/${SEASON_ID}#tier-2-round-4`);
    const board = document.querySelector(".viewer")!;
    expect(place.compareDocumentPosition(board) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("links a tournament game to its round", async () => {
    mockApi({
      "/session": { user: null },
      "/matches/m1": match({ id: "m1", tournament: TOURNAMENT_PLACE }),
    });
    renderRoute("/matches/m1");

    expect(await screen.findByRole("link", { name: /round 3, board 1/ })).toHaveAttribute(
      "href",
      `/editions/${EDITION_ID}#round-3`,
    );
  });

  it("names season, edition and series in the list of games", async () => {
    mockApi({
      "/matches": {
        items: [
          summary({ id: "a", league: LEAGUE_PLACE }),
          summary({ id: "b", tournament: TOURNAMENT_PLACE }),
          summary({ id: "c", series: { id: "s1", index: 2, games: 4 } }),
        ],
        total: 3,
      },
      "/bots": { items: BOTS },
    });
    renderRoute("/matches");

    expect(await screen.findByRole("columnheader", { name: "Competition" })).toBeVisible();
    expect(screen.getByRole("link", { name: "Bundesliga, Season 3" })).toHaveAttribute(
      "href",
      `/seasons/${SEASON_ID}#tier-2-round-4`,
    );
    expect(screen.getByRole("link", { name: "Herbstcup, Edition 2" })).toHaveAttribute(
      "href",
      `/editions/${EDITION_ID}#round-3`,
    );
    expect(screen.getByRole("link", { name: "Game 2 of 4 in a series" })).toHaveAttribute(
      "href",
      "/series/s1",
    );
  });

  it("names the competition in the queue", async () => {
    const entry = {
      match: summary({ status: "queued", result: null, termination: null, league: LEAGUE_PLACE }),
      position: 1,
      priority: 50,
      estimated_start: "2026-05-01T12:10:00.000Z",
      estimated_end: "2026-05-01T12:20:00.000Z",
    };
    mockApi({ "/queue": queue({ waiting: [entry], waiting_total: 1 }) });
    renderRoute("/queue");

    expect(await screen.findByRole("link", { name: "Bundesliga, Season 3" })).toHaveAttribute(
      "href",
      `/seasons/${SEASON_ID}#tier-2-round-4`,
    );
  });
});

describe("back from filtered games", () => {
  it("leads back to the tier of the season", async () => {
    mockApi({
      "/session": { user: null },
      "/matches": { items: [], total: 0 },
      "/bots": { items: BOTS },
    });
    renderRoute(`/matches?season=${SEASON_ID}&tier=2`);

    expect(await screen.findByRole("link", { name: "To the season" })).toHaveAttribute(
      "href",
      `/seasons/${SEASON_ID}#tier-2`,
    );
  });

  it("leads back to the edition", async () => {
    mockApi({
      "/session": { user: null },
      "/matches": { items: [], total: 0 },
      "/bots": { items: BOTS },
    });
    renderRoute(`/matches?edition=${EDITION_ID}`);

    expect(await screen.findByRole("link", { name: "To the edition" })).toHaveAttribute(
      "href",
      `/editions/${EDITION_ID}`,
    );
  });
});
