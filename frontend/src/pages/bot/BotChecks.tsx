import { useState } from "react";
import { useTranslation } from "react-i18next";

import { overrideBot, recheckBot } from "../../api/admin";
import type { BotDetail } from "../../api/types";
import { FormError } from "../../components/FormError";
import { useSubmit } from "../../hooks/useSubmit";
import { useSession } from "../../session/sessionContext";

const RECHECKABLE: BotDetail["status"][] = ["verified", "rejected", "disabled", "retired"];

/**
 * Admins check an uploaded bot again with the current rules, which only adds a report, and
 * verify a rejected bot anyway after a second click (E153).
 */
export function BotChecks({ bot, onChange }: { bot: BotDetail; onChange: () => void }) {
  const { t } = useTranslation();
  const { user } = useSession();
  const [asking, setAsking] = useState(false);
  const { pending, error, submit } = useSubmit();
  if (user?.role !== "admin" || bot.builtin || !RECHECKABLE.includes(bot.status)) return null;

  function run(action: (id: string) => Promise<BotDetail>) {
    void submit(async () => {
      await action(bot.id);
      setAsking(false);
      onChange();
    });
  }

  return (
    <>
      <p className="inline-actions">
        {!bot.details?.recheck_pending && (
          <button type="button" onClick={() => run(recheckBot)} disabled={pending}>
            {t("bot.recheck")}
          </button>
        )}
        {bot.status === "rejected" && !asking && (
          <button type="button" onClick={() => setAsking(true)} disabled={pending}>
            {t("bot.override")}
          </button>
        )}
      </p>
      {asking && (
        <>
          <p className="hint">{t("bot.overrideWarning")}</p>
          <p>
            <button type="button" onClick={() => run(overrideBot)} disabled={pending}>
              {t("bot.overrideConfirm")}
            </button>{" "}
            <button type="button" onClick={() => setAsking(false)} disabled={pending}>
              {t("bot.cancel")}
            </button>
          </p>
        </>
      )}
      <FormError error={error} />
    </>
  );
}
