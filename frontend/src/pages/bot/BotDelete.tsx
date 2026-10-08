import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";

import { deleteBot } from "../../api/admin";
import type { BotDetail } from "../../api/types";
import { FormError } from "../../components/FormError";
import { useSubmit } from "../../hooks/useSubmit";
import { useSession } from "../../session/sessionContext";

/**
 * Admins delete this version for good with its matches (E105), after a second click. Then the
 * page moves on to another version of the name, or to the list of bots if none is left.
 */
export function BotDelete({ bot }: { bot: BotDetail }) {
  const { t } = useTranslation();
  const { user } = useSession();
  const navigate = useNavigate();
  const [asking, setAsking] = useState(false);
  const { pending, error, submit } = useSubmit();
  if (user?.role !== "admin" || bot.builtin) return null;
  if (bot.status === "uploaded" || bot.status === "analyzing" || bot.status === "testing") {
    return null;
  }

  function onDelete() {
    void submit(async () => {
      await deleteBot(bot.id);
      const other = bot.versions.find((version) => version.id !== bot.id);
      void navigate(other ? `/bots/${other.id}` : "/bots", { replace: true });
    });
  }

  return (
    <>
      {asking ? (
        <>
          <p className="hint">{t("bot.deleteWarning")}</p>
          <p>
            <button type="button" onClick={onDelete} disabled={pending}>
              {t("bot.deleteConfirm")}
            </button>{" "}
            <button type="button" onClick={() => setAsking(false)} disabled={pending}>
              {t("bot.deleteCancel")}
            </button>
          </p>
        </>
      ) : (
        <p>
          <button type="button" onClick={() => setAsking(true)}>
            {t("bot.delete")}
          </button>
        </p>
      )}
      <FormError error={error} />
    </>
  );
}
