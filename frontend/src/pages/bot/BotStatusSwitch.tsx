import { useTranslation } from "react-i18next";

import { setBotStatus } from "../../api/admin";
import type { BotDetail } from "../../api/types";
import { FormError } from "../../components/FormError";
import { useSubmit } from "../../hooks/useSubmit";
import { useSession } from "../../session/sessionContext";

/** Admins disable a verified bot or enable it again (E93); nobody else sees the switch. */
export function BotStatusSwitch({ bot, onChange }: { bot: BotDetail; onChange: () => void }) {
  const { t } = useTranslation();
  const { user } = useSession();
  const { pending, error, submit } = useSubmit();
  if (user?.role !== "admin") return null;
  if (bot.status !== "verified" && bot.status !== "disabled") return null;
  const next = bot.status === "verified" ? "disabled" : "verified";

  function onClick() {
    void submit(async () => {
      await setBotStatus(bot.id, next);
      onChange();
    });
  }

  return (
    <>
      <p>
        <button type="button" onClick={onClick} disabled={pending}>
          {next === "disabled" ? t("bot.disable") : t("bot.enable")}
        </button>
      </p>
      <FormError error={error} />
    </>
  );
}
