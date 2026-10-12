import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { CurrentUser, LeagueDetail, TournamentDetail } from "../api/types";
import { ADMIN, CODER } from "../test/fixtures";
import { LEAGUE_ID, SEASON_ID, leagueDetail, schedule, season } from "../test/leagues";
import { type ApiResponses, mockApi, renderRoute } from "../test/render";
import { EDITION_ID, TOURNAMENT_ID, plannedEdition, tournamentDetail } from "../test/tournaments";

const NOW = new Date().toISOString();
const PLANNED_SEASON = season({
  status: "planned",
  starts_after: null,
  started_at: null,
  finished_at: null,
  settings: null,
  discipline: null,
  tiers: [],
});

/** The league before and after the start: the planned season is due at once (E171). */
function leagueResponses(): ApiResponses {
  let started = false;
  const detail = (): LeagueDetail =>
    started
      ? leagueDetail({ season: { ...leagueDetail().season!, starts_after: NOW } })
      : leagueDetail();
  return {
    [`/leagues/${LEAGUE_ID}`]: detail,
    [`/seasons/${SEASON_ID}`]: () => ({ ...PLANNED_SEASON, starts_after: started ? NOW : null }),
    [`/admin/leagues/${LEAGUE_ID}/start`]: () => {
      started = true;
      return detail();
    },
  };
}

function tournamentResponses(): ApiResponses {
  let started = false;
  const detail = (): TournamentDetail =>
    started
      ? tournamentDetail({ edition: { ...tournamentDetail().edition!, starts_after: NOW } })
      : tournamentDetail();
  return {
    [`/tournaments/${TOURNAMENT_ID}`]: detail,
    [`/editions/${EDITION_ID}`]: () => ({
      ...plannedEdition(),
      starts_after: started ? NOW : null,
    }),
    [`/admin/tournaments/${TOURNAMENT_ID}/start`]: () => {
      started = true;
      return detail();
    },
  };
}

function session(user: CurrentUser | null) {
  return { "/session": { user } };
}

describe("start now on the competition pages", () => {
  it.each([
    ["league", `/leagues/${LEAGUE_ID}`, leagueResponses, `/admin/leagues/${LEAGUE_ID}/start`],
    ["season", `/seasons/${SEASON_ID}`, leagueResponses, `/admin/leagues/${LEAGUE_ID}/start`],
    [
      "tournament",
      `/tournaments/${TOURNAMENT_ID}`,
      tournamentResponses,
      `/admin/tournaments/${TOURNAMENT_ID}/start`,
    ],
    [
      "edition",
      `/editions/${EDITION_ID}`,
      tournamentResponses,
      `/admin/tournaments/${TOURNAMENT_ID}/start`,
    ],
  ])("lets an admin start from the %s page", async (_page, path, responses, start) => {
    const user = userEvent.setup();
    const api = mockApi({ ...session(ADMIN), ...responses() });
    renderRoute(path);

    expect(await screen.findByText(/waits for an admin to start it/)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Start now" }));

    await waitFor(() => expect(screen.queryByRole("button", { name: "Start now" })).toBeNull());
    expect(await screen.findByText(/at the earliest/)).toBeVisible();
    const posts = api.calls.filter((call) => call.method === "POST");
    expect(posts.map((call) => call.url.pathname)).toEqual([`/api/v1${start}`]);
  });

  it.each([
    ["nobody", null],
    ["a coder", CODER],
  ])("offers no start to %s", async (_who, current) => {
    mockApi({ ...session(current), ...leagueResponses(), ...tournamentResponses() });
    const seasonPage = renderRoute(`/seasons/${SEASON_ID}`);
    expect(await screen.findByText(/waits for an admin to start it/)).toBeVisible();
    expect(screen.queryByRole("button", { name: "Start now" })).toBeNull();
    seasonPage.unmount();

    renderRoute(`/tournaments/${TOURNAMENT_ID}`);
    expect(await screen.findByText(/waits for an admin to start it/)).toBeVisible();
    expect(screen.queryByRole("button", { name: "Start now" })).toBeNull();
  });

  it("offers no start for a season that is not the planned one", async () => {
    mockApi({
      ...session(ADMIN),
      [`/seasons/${SEASON_ID}`]: season(),
      [`/seasons/${SEASON_ID}/schedule`]: schedule(),
      [`/leagues/${LEAGUE_ID}`]: leagueDetail(),
    });
    renderRoute(`/seasons/${SEASON_ID}`);

    expect(await screen.findByText(/^Finished/)).toBeVisible();
    expect(screen.queryByRole("button", { name: "Start now" })).toBeNull();
  });
});
