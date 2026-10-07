import { useTranslation } from "react-i18next";

import { SPEEDS, type Speed } from "./playback";
import type { Playback } from "./usePlayback";
import type { ViewerPly } from "./useViewerPly";

export function Controls({
  position,
  total,
  live,
  playback,
  onFlip,
}: {
  position: ViewerPly;
  total: number;
  live: boolean;
  playback: Playback;
  onFlip: () => void;
}) {
  const { t } = useTranslation();
  const { ply, goTo, following, follow } = position;
  return (
    <div className="controls">
      <div className="control-buttons">
        <IconButton
          label={t("viewer.first")}
          symbol="⏮"
          disabled={ply === 0}
          onClick={() => goTo(0)}
        />
        <IconButton
          label={t("viewer.previous")}
          symbol="◀"
          disabled={ply === 0}
          onClick={() => goTo(ply - 1)}
        />
        <IconButton
          label={playback.playing ? t("viewer.pause") : t("viewer.play")}
          symbol={playback.playing ? "⏸" : "▶"}
          disabled={total === 0}
          onClick={playback.toggle}
        />
        <IconButton
          label={t("viewer.next")}
          symbol="▶"
          className="step"
          disabled={ply >= total}
          onClick={() => goTo(ply + 1)}
        />
        <IconButton
          label={t("viewer.last")}
          symbol="⏭"
          disabled={ply >= total}
          onClick={() => goTo(total)}
        />
        <IconButton label={t("viewer.flip")} symbol="⇅" onClick={onFlip} />
      </div>
      <div className="control-options">
        <label>
          {t("viewer.speed")}
          <select
            value={String(playback.speed)}
            onChange={(event) => playback.setSpeed(parseSpeed(event.target.value))}
          >
            {SPEEDS.map((speed) => (
              <option key={speed} value={String(speed)}>
                {speed === "real" ? t("viewer.realTime") : `${speed}×`}
              </option>
            ))}
          </select>
        </label>
        {live && (
          <button type="button" aria-pressed={following} onClick={follow} disabled={following}>
            {following ? t("viewer.following") : t("viewer.follow")}
          </button>
        )}
      </div>
    </div>
  );
}

function IconButton({
  label,
  symbol,
  className,
  disabled,
  onClick,
}: {
  label: string;
  symbol: string;
  className?: string;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={`icon${className ? ` ${className}` : ""}`}
      aria-label={label}
      title={label}
      disabled={disabled}
      onClick={onClick}
    >
      <span aria-hidden="true">{symbol}</span>
    </button>
  );
}

function parseSpeed(value: string): Speed {
  return SPEEDS.find((speed) => String(speed) === value) ?? 1;
}
