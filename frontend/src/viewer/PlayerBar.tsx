import { useTranslation } from "react-i18next";

import type { Side } from "../api/types";
import type { Color } from "../chess/fen";
import { formatClock } from "../format/clock";

/** Name, material lead and remaining time of one side; the side to move is highlighted. */
export function PlayerBar({
  side,
  color,
  clockMs,
  lead,
  toMove,
}: {
  side: Side;
  color: Color;
  clockMs: number;
  lead: number;
  toMove: boolean;
}) {
  const { t } = useTranslation();
  const label = t(color === "w" ? "viewer.white" : "viewer.black");
  return (
    <div className={`player-bar${toMove ? " to-move" : ""}`} data-testid={`player-${color}`}>
      <span className={`piece-dot ${color}`} aria-label={label} title={label} />
      <span className="player-name">{side.name}</span>
      {lead > 0 && (
        <span className="material" title={t("viewer.material")}>
          +{lead}
        </span>
      )}
      <span className="clock" role="timer">
        {formatClock(clockMs)}
      </span>
    </div>
  );
}
