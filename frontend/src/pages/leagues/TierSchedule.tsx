import { useTranslation } from "react-i18next";

import { fetchSeasonSchedule } from "../../api/leagues";
import { ApiContent } from "../../components/ApiContent";
import { ScheduleRounds } from "../../components/ScheduleRounds";
import { seasonRoundAnchor } from "../../format/anchors";
import { POLL_LIST_MS } from "../../hooks/polling";
import { useApi } from "../../hooks/useApi";

/** The rounds of one tier with the state of each game (E138). */
export function TierSchedule({
  seasonId,
  tier,
  running,
}: {
  seasonId: string;
  tier: number;
  running: boolean;
}) {
  const { t } = useTranslation();
  const schedule = useApi(
    (signal) => fetchSeasonSchedule(seasonId, tier, signal),
    `schedule:${seasonId}:${tier}`,
    running ? POLL_LIST_MS : undefined,
  );
  return (
    <>
      <h3>{t("seasons.schedule")}</h3>
      <ApiContent state={schedule}>
        {(data) => (
          <ScheduleRounds
            rounds={data.rounds}
            empty={t("seasons.noSchedule")}
            anchor={(round) => seasonRoundAnchor(tier, round)}
          />
        )}
      </ApiContent>
    </>
  );
}
