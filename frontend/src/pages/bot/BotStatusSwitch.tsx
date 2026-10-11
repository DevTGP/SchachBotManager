import { useTranslation } from "react-i18next";

import { setBotStatus } from "../../api/admin";
import type { BotDetail } from "../../api/types";
import { ConfirmButton } from "../../components/ConfirmButton";
import { FormError } from "../../components/FormError";
import { useSubmit } from "../../hooks/useSubmit";
import { useSession } from "../../session/sessionContext";

/**
 * Admins disable a verified or retired bot and enable a disabled one, which makes it verified
 * (E93, E96); nobody else sees the switch.
 */
export function BotStatusSwitch({ bot, onChange }: { bot: BotDetail; onChange: () => void }) {
  const { t } = useTranslation();
  const { user } = useSession();
  const { pending, error, submit } = useSubmit();
  if (user?.role !== "admin") return null;
  if (bot.status !== "verified" && bot.status !== "retired" && bot.status !== "disabled") {
    return null;
  }
  const next = bot.status === "disabled" ? "verified" : "disabled";

  function onClick() {
    void submit(async () => {
      await setBotStatus(bot.id, next);
      onChange();
    });
  }

  return (
    <>
      <p>
        {next === "disabled" ? (
          <ConfirmButton
            label={t("bot.disable")}
            confirmLabel={t("bot.disableConfirm")}
            onConfirm={onClick}
            disabled={pending}
          />
        ) : (
          <button type="button" onClick={onClick} disabled={pending}>
            {t("bot.enable")}
          </button>
        )}
      </p>
      <FormError error={error} />
    </>
  );
}
