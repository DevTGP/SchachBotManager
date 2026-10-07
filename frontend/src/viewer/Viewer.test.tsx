import { act, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ChessboardOptions } from "react-chessboard";
import { describe, expect, it, vi } from "vitest";

import { match, OPENING } from "../test/fixtures";
import { mockApi, renderRoute } from "../test/render";

// The real board measures its squares, which jsdom cannot; the stub shows what it was given.
vi.mock("react-chessboard", () => ({
  Chessboard: ({ options }: { options: ChessboardOptions }) => (
    <div
      data-testid="board"
      data-position={String(options.position)}
      data-orientation={options.boardOrientation}
      data-highlighted={Object.keys(options.squareStyles ?? {}).join(" ")}
    />
  ),
}));

const ID = "665f00000000000000000001";

function plyOf(router: { state: { location: { search: string } } }) {
  return new URLSearchParams(router.state.location.search).get("ply");
}

function currentMove() {
  return screen.getByRole("button", { current: "step" });
}

describe("viewer", () => {
  it("shows a finished match at its last move", async () => {
    mockApi({ [`/matches/${ID}`]: match() });
    renderRoute(`/matches/${ID}`);

    expect(await screen.findByRole("heading", { name: "Random – Material" })).toBeVisible();
    expect(currentMove()).toHaveTextContent("Nf3");
    expect(screen.getByText("Resignation")).toBeVisible();
    expect(within(screen.getByTestId("player-w")).getByRole("timer")).toHaveTextContent("2:56");
    expect(within(screen.getByTestId("player-b")).getByRole("timer")).toHaveTextContent("2:58");
    expect(screen.getByRole("link", { name: "Download PGN" })).toHaveAttribute(
      "href",
      `/api/v1/matches/${ID}/pgn`,
    );
    expect(screen.queryByRole("button", { name: /follow live/i })).toBeNull();
  });

  it("opens the move from the link and steps with buttons, list and keys", async () => {
    const user = userEvent.setup();
    mockApi({ [`/matches/${ID}`]: match() });
    const { router } = renderRoute(`/matches/${ID}?ply=1`);

    expect(await screen.findByRole("button", { current: "step" })).toHaveTextContent("e4");
    const board = screen.getByTestId("board");
    expect(board).toHaveAttribute("data-position", OPENING[0]?.fen);
    expect(board).toHaveAttribute("data-highlighted", "e2 e4");
    expect(screen.getByText("+0.35")).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Flip board" }));
    expect(screen.getByTestId("board")).toHaveAttribute("data-orientation", "black");
    expect(screen.getByText("e2e4 e7e5")).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Next move" }));
    expect(currentMove()).toHaveTextContent("e5");
    expect(plyOf(router)).toBe("2");
    // Black's score of +0.20 is -0.20 for White.
    expect(screen.getByText("-0.20")).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Starting position" }));
    expect(plyOf(router)).toBe("0");
    expect(screen.queryByText("Bot info")).toBeNull();

    await user.keyboard("{End}");
    expect(currentMove()).toHaveTextContent("Nf3");
    await user.keyboard("{ArrowLeft}");
    expect(currentMove()).toHaveTextContent("e5");
    await user.click(screen.getByRole("button", { name: /e4/ }));
    expect(plyOf(router)).toBe("1");
  });

  it("plays the moves one after another and stops at the end", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    mockApi({ [`/matches/${ID}`]: match() });
    const { router } = renderRoute(`/matches/${ID}?ply=0`);
    await screen.findByRole("heading", { name: "Random – Material" });

    await user.selectOptions(screen.getByRole("combobox", { name: "Speed" }), "2");
    await user.click(screen.getByRole("button", { name: "Play" }));
    expect(screen.getByRole("button", { name: "Pause" })).toBeVisible();

    // Factor 2: one move every half second.
    for (const ply of ["1", "2", "3"]) {
      await act(() => vi.advanceTimersByTimeAsync(500));
      expect(plyOf(router)).toBe(ply);
    }
    await act(() => vi.advanceTimersByTimeAsync(500));
    expect(plyOf(router)).toBe("3");
    expect(screen.getByRole("button", { name: "Play" })).toBeVisible();
  });

  it("follows a running match and lets the viewer browse freely", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    let moves = OPENING.slice(0, 2);
    const api = mockApi({
      [`/matches/${ID}`]: () =>
        match({ status: "running", result: null, termination: null, finished_at: null, moves }),
    });
    const { router } = renderRoute(`/matches/${ID}`);

    expect(await screen.findByRole("button", { name: "Following live" })).toBeDisabled();
    expect(currentMove()).toHaveTextContent("e5");
    // White is to move and its clock is highlighted.
    expect(screen.getByTestId("player-w")).toHaveClass("to-move");

    moves = OPENING;
    await act(() => vi.advanceTimersByTimeAsync(2_000));
    expect(currentMove()).toHaveTextContent("Nf3");
    expect(api.requests.length).toBeGreaterThanOrEqual(2);

    await user.click(screen.getByRole("button", { name: "Previous move" }));
    expect(plyOf(router)).toBe("2");
    await user.click(screen.getByRole("button", { name: "Follow live" }));
    expect(plyOf(router)).toBeNull();
    expect(currentMove()).toHaveTextContent("Nf3");
  });

  it("names a missing match", async () => {
    mockApi({});
    renderRoute(`/matches/${ID}`);
    expect(await screen.findByRole("alert")).toHaveTextContent("Not found.");
  });
});
