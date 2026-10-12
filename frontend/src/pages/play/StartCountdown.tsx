import { useState } from "react";
import { useTranslation } from "react-i18next";

import { formatCountdown } from "../../format/countdown";
import { useNow } from "../../hooks/useNow";

/**
 * How long a ready game probably still waits for the runner (E187): a countdown, and a bar from
 * the moment this page first saw an estimate. A later estimate makes the bar longer.
 */
export function StartCountdown({ at }: { at: string }) {
  const { t } = useTranslation();
  const now = useNow();
  const [since] = useState(() => Date.now());
  const target = Date.parse(at);
  const left = target - now;
  const total = Math.max(target - since, 1);
  return (
    <div className="start-countdown">
      <p>
        {left > 0
          ? t("competitionGame.startsIn", { left: formatCountdown(left) })
          : t("competitionGame.startsSoon")}
      </p>
      <progress
        aria-label={t("competitionGame.startProgress")}
        max={total}
        value={Math.min(Math.max(now - since, 0), total)}
      />
      <p className="hint">{t("competitionGame.startHint")}</p>
    </div>
  );
}
