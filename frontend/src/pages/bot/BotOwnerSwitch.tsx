import { useTranslation } from "react-i18next";

import { updateOwnBot } from "../../api/bots";
import type { BotDetail } from "../../api/types";
import { ConfirmButton } from "../../components/ConfirmButton";
import { FormError } from "../../components/FormError";
import { useSubmit } from "../../hooks/useSubmit";

/**
 * The owner retires a verified bot and brings it back; an admin block stays (E96). A button in
 * the bar of actions (U10).
 */
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
      {next === "retired" ? (
        <ConfirmButton
          label={t("bot.retire")}
          confirmLabel={t("bot.retireConfirm")}
          onConfirm={onClick}
          disabled={pending}
          title={t("bot.retireHint")}
        />
      ) : (
        <button type="button" onClick={onClick} disabled={pending}>
          {t("bot.reactivate")}
        </button>
      )}
      <FormError error={error} />
    </>
  );
}
