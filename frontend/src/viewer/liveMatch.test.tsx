import { act, screen, waitFor } from "@testing-library/react";
import type { ChessboardOptions } from "react-chessboard";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Match } from "../api/types";
import { FakeEventSource } from "../test/fakeEventSource";
import { match, OPENING } from "../test/fixtures";
import { mockApi, renderRoute } from "../test/render";

vi.mock("react-chessboard", () => ({
  Chessboard: ({ options }: { options: ChessboardOptions }) => (
    <div data-testid="board" data-position={String(options.position)} />
  ),
}));

const ID = "665f00000000000000000001";
const RUNNING: Partial<Match> = {
  status: "running",
  result: null,
  termination: null,
  finished_at: null,
};

function currentMove() {
  return screen.getByRole("button", { current: "step" });
}

/** A running match with the first two moves; `current` changes what the API answers. */
async function openRunningMatch() {
  const state = { current: match({ ...RUNNING, moves: OPENING.slice(0, 2) }) };
  const api = mockApi({ [`/matches/${ID}`]: () => state.current });
  renderRoute(`/matches/${ID}`);
  await screen.findByRole("button", { name: "Following live" });
  await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1));
  return { api, state, source: FakeEventSource.latest() };
}

describe("a running match in the viewer (E142)", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    FakeEventSource.instances = [];
    vi.stubGlobal("EventSource", FakeEventSource);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("takes the moves from the event stream instead of asking the API", async () => {
    const { api, source } = await openRunningMatch();
    expect(source.url).toBe(`/api/v1/matches/${ID}/live?after=2`);

    act(() => source.open());
    const asked = api.requests.length;
    act(() => source.emit("move", OPENING[2]));

    expect(currentMove()).toHaveTextContent("Nf3");
    await act(() => vi.advanceTimersByTimeAsync(6_000));
    expect(api.requests.length).toBe(asked);
  });

  it("ignores moves it has and loads the match again at the end", async () => {
    const { api, state, source } = await openRunningMatch();
    act(() => source.open());
    act(() => source.emit("move", OPENING[1]));
    act(() => source.emit("move", OPENING[2]));
    expect(screen.getAllByRole("button", { name: /e5/ })).toHaveLength(1);

    state.current = match();
    const asked = api.requests.length;
    act(() => source.emit("end", {}));

    expect(source.closed).toBe(true);
    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "Following live" })).toBeNull(),
    );
    expect(api.requests.length).toBe(asked + 1);
  });

  it("asks the API again while the stream is broken", async () => {
    const { api, state, source } = await openRunningMatch();
    act(() => source.open());
    act(() => source.fail());

    state.current = match({ ...RUNNING, moves: OPENING });
    const asked = api.requests.length;
    await act(() => vi.advanceTimersByTimeAsync(2_000));

    expect(api.requests.length).toBeGreaterThan(asked);
    expect(currentMove()).toHaveTextContent("Nf3");
  });

  it("gives up the stream when moves are missing", async () => {
    const { api, source } = await openRunningMatch();
    act(() => source.open());
    const asked = api.requests.length;
    act(() => source.emit("move", { ...OPENING[2], ply: 4 }));

    expect(source.closed).toBe(true);
    expect(currentMove()).toHaveTextContent("e5");
    await act(() => vi.advanceTimersByTimeAsync(2_000));
    expect(api.requests.length).toBeGreaterThan(asked);
  });

  it("does not open a stream for a finished match", async () => {
    mockApi({ [`/matches/${ID}`]: match() });
    renderRoute(`/matches/${ID}`);
    await screen.findByRole("heading", { name: "Random 1.0.0 – Material 1.0.0" });
    await act(() => vi.advanceTimersByTimeAsync(100));
    expect(FakeEventSource.instances).toHaveLength(0);
  });
});
