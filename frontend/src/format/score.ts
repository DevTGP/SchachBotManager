import type { MoveInfo } from "../api/types";
import type { Color } from "../chess/fen";

/**
 * The reported score from White's point of view: +0.35, -1.20, #3 or #-3. Bots report it from
 * their own side, so Black's scores change sign.
 */
export function formatScore(info: MoveInfo, mover: Color): string | undefined {
  const sign = mover === "w" ? 1 : -1;
  if (info.score_mate !== undefined) return `#${sign * info.score_mate}`;
  if (info.score_cp === undefined) return undefined;
  const pawns = (sign * info.score_cp) / 100;
  return `${pawns > 0 ? "+" : ""}${pawns.toFixed(2)}`;
}
