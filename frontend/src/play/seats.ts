/**
 * The seat of a game, kept in this browser so a reload joins the same game again (E113).
 * Storage may be unavailable, e.g. in a private window; the game then lasts as long as the page.
 */

const PREFIX = "sbm.play.";

export function saveSeat(matchId: string, seat: string): void {
  try {
    localStorage.setItem(PREFIX + matchId, seat);
  } catch {
    // Without storage a reload cannot rejoin; playing works all the same.
  }
}

export function loadSeat(matchId: string): string | undefined {
  try {
    return localStorage.getItem(PREFIX + matchId) ?? undefined;
  } catch {
    return undefined;
  }
}

export function forgetSeat(matchId: string): void {
  try {
    localStorage.removeItem(PREFIX + matchId);
  } catch {
    // Nothing to forget without storage.
  }
}
