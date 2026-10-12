import { useTranslation } from "react-i18next";

import { fetchEditionRounds } from "../../api/tournaments";
import { ApiContent } from "../../components/ApiContent";
import { ScheduleRounds } from "../../components/ScheduleRounds";
import { editionRoundAnchor } from "../../format/anchors";
import { POLL_LIST_MS } from "../../hooks/polling";
import { useApi } from "../../hooks/useApi";

/** The rounds of a round robin or Swiss edition, refreshed while it runs (E180). */
export function EditionRoundsSection({
  editionId,
  running,
}: {
  editionId: string;
  running: boolean;
}) {
  const { t } = useTranslation();
  const rounds = useApi(
    (signal) => fetchEditionRounds(editionId, signal),
    `edition-rounds:${editionId}`,
    running ? POLL_LIST_MS : undefined,
  );
  return (
    <section>
      <h2>{t("editions.rounds")}</h2>
      <ApiContent state={rounds}>
        {(data) => (
          <ScheduleRounds
            rounds={data.rounds}
            empty={t("editions.noRounds")}
            anchor={editionRoundAnchor}
          />
        )}
      </ApiContent>
    </section>
  );
}
