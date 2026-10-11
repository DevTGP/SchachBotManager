import { useTranslation } from "react-i18next";

import type { LeagueBot } from "../../api/types";
import { useSubmit } from "../../hooks/useSubmit";
import { useSession } from "../../session/sessionContext";
import { FormError } from "../FormError";

/**
 * Any logged-in account joins a league or tournament itself; its games wait for it to say it is
 * ready, up to ready_hours after their release (E182, E183).
 */
export function SelfRegistration({
  registered,
  readyHours,
  register,
  onChange,
}: {
  registered: LeagueBot[];
  readyHours: number;
  register: (userId: string) => Promise<unknown>;
  onChange: () => void;
}) {
  const { t } = useTranslation();
  const { user } = useSession();
  const { pending, error, submit } = useSubmit();
  if (user == null || registered.some((entry) => entry.user_id === user.id)) return null;
  const userId = user.id;

  function join() {
    void submit(async () => {
      await register(userId);
      onChange();
    });
  }

  return (
    <section>
      <h2>{t("registration.self")}</h2>
      <p className="hint">{t("registration.selfHint", { hours: readyHours })}</p>
      <FormError error={error} />
      <div className="inline-actions">
        <button type="button" className="primary" disabled={pending} onClick={join}>
          {t("registration.join")}
        </button>
      </div>
    </section>
  );
}
