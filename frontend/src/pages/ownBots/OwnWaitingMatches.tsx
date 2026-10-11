import { useTranslation } from "react-i18next";

import { withdrawOwnMatch } from "../../api/bots";
import type { MatchSummary } from "../../api/types";
import { ConfirmButton } from "../../components/ConfirmButton";
import { FormError } from "../../components/FormError";
import { QueueTable } from "../../components/QueueTable";
import { useSubmit } from "../../hooks/useSubmit";

/**
 * The account's games that still wait, in the coder view of the queue table (E167); each can be
 * taken back until it starts, after a second click (E157).
 */
export function OwnWaitingMatches({
  matches,
  onChange,
}: {
  matches: MatchSummary[];
  onChange: () => void;
}) {
  const { t } = useTranslation();
  const { pending, error, submit } = useSubmit();

  function withdraw(matchId: string) {
    void submit(async () => {
      await withdrawOwnMatch(matchId);
      onChange();
    });
  }

  return (
    <>
      <QueueTable
        rows={matches.map((match) => ({ match }))}
        view="own"
        empty={t("ownBots.noWaiting")}
        actions={({ match }) => (
          <ConfirmButton
            small
            label={t("ownBots.withdraw")}
            confirmLabel={t("ownBots.withdrawConfirm")}
            onConfirm={() => withdraw(match.id)}
            disabled={pending}
          />
        )}
      />
      <FormError error={error} />
    </>
  );
}
