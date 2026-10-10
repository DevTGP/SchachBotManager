import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";

import { repeatMatch } from "../../api/admin";
import type { Match } from "../../api/types";
import { FormError } from "../../components/FormError";
import { useSubmit } from "../../hooks/useSubmit";
import { useSession } from "../../session/sessionContext";

/**
 * Admins queue an ended single game again, with the bots and discipline as they are now (E152);
 * the page then shows the new game.
 */
export function MatchRepeat({ match }: { match: Match }) {
  const { t } = useTranslation();
  const { user } = useSession();
  const navigate = useNavigate();
  const { pending, error, submit } = useSubmit();
  const ended = match.status === "finished" || match.status === "aborted";
  if (user?.role !== "admin" || match.type !== "single" || !ended) return null;

  function onRepeat() {
    void submit(async () => {
      const id = await repeatMatch(match.id);
      void navigate(`/matches/${id}`);
    });
  }

  return (
    <>
      <p>
        <button type="button" disabled={pending} onClick={onRepeat}>
          {t("admin.repeatMatch")}
        </button>
      </p>
      <FormError error={error} />
    </>
  );
}
