import { useTranslation } from "react-i18next";

import type { EditionSummary, SeasonSummary } from "../../api/types";
import { useSubmit } from "../../hooks/useSubmit";
import { useSession } from "../../session/sessionContext";
import { FormError } from "../FormError";
import { startable } from "./startable";

/**
 * "Start now" for an admin on the page of a league, tournament, season or edition (E191), as on
 * the admin pages (E171): the planned season or edition is due at once and starts as soon as
 * enough participants are registered.
 */
export function StartNow({
  competition,
  start,
  onStarted,
}: {
  competition: {
    archived: boolean;
    season?: SeasonSummary | null;
    edition?: EditionSummary | null;
  };
  start: () => Promise<unknown>;
  onStarted: () => void;
}) {
  const { t } = useTranslation();
  const { user } = useSession();
  const { pending, error, submit } = useSubmit();
  if (user?.role !== "admin") return null;
  const show = startable(competition);
  if (!show && !error) return null;
  return (
    <div className="start-now">
      {show && (
        <button
          type="button"
          className="primary"
          disabled={pending}
          onClick={() =>
            void submit(async () => {
              await start();
              onStarted();
            })
          }
        >
          {t("leagues.startNow")}
        </button>
      )}
      <FormError error={error} />
    </div>
  );
}
