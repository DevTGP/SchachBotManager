/**
 * The seat of a game, kept in this browser so a reload joins the same game again (E113).
 * Storage may be unavailable, e.g. in a private window; the game then lasts as long as the page.
 *
 * Games from /play keep theirs as "play"; league and tournament games as "ready", since their
 * seat comes before the game starts (E183).
 */

export type SeatKind = "play" | "ready";

function key(matchId: string, kind: SeatKind): string {
  return `sbm.${kind}.${matchId}`;
}

export function saveSeat(matchId: string, seat: string, kind: SeatKind = "play"): void {
  try {
    localStorage.setItem(key(matchId, kind), seat);
  } catch {
    // Without storage a reload cannot rejoin; playing works all the same.
  }
}

export function loadSeat(matchId: string, kind: SeatKind = "play"): string | undefined {
  try {
    return localStorage.getItem(key(matchId, kind)) ?? undefined;
  } catch {
    return undefined;
  }
}

export function forgetSeat(matchId: string, kind: SeatKind = "play"): void {
  try {
    localStorage.removeItem(key(matchId, kind));
  } catch {
    // Nothing to forget without storage.
  }
}
