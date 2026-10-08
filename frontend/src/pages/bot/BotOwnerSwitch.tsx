import { useTranslation } from "react-i18next";

import { updateOwnBot } from "../../api/bots";
import type { BotDetail } from "../../api/types";
import { FormError } from "../../components/FormError";
import { useSubmit } from "../../hooks/useSubmit";

/** The owner retires a verified bot and brings it back; an admin block stays (E96). */
export function BotOwnerSwitch({ bot, onChange }: { bot: BotDetail; onChange: () => void }) {
  const { t } = useTranslation();
  const { pending, error, submit } = useSubmit();
  if (bot.status !== "verified" && bot.status !== "retired") return null;
  const next = bot.status === "verified" ? "retired" : "verified";

  function onClick() {
    void submit(async () => {
      await updateOwnBot(bot.id, { status: next });
      onChange();
    });
  }

  return (
    <>
      <p className="inline-actions">
        <button type="button" onClick={onClick} disabled={pending}>
          {next === "retired" ? t("bot.retire") : t("bot.reactivate")}
        </button>
        <span className="hint">
          {next === "retired" ? t("bot.retireHint") : t("bot.retiredHint")}
        </span>
      </p>
      <FormError error={error} />
    </>
  );
}
