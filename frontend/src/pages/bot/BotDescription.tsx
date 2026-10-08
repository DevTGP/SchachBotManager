import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { updateOwnBot } from "../../api/bots";
import type { BotDetail } from "../../api/types";
import { FormError } from "../../components/FormError";
import { useSubmit } from "../../hooks/useSubmit";

/** The most characters of a description (E95). */
export const DESCRIPTION_LENGTH = 500;

/** The public description as plain text; the owner edits it in place (E95). */
export function BotDescription({
  bot,
  isOwner,
  onChange,
}: {
  bot: BotDetail;
  isOwner: boolean;
  onChange: () => void;
}) {
  const { t } = useTranslation();
  const { pending, error, submit } = useSubmit();
  const [draft, setDraft] = useState<string | undefined>(undefined);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void submit(async () => {
      await updateOwnBot(bot.id, { description: draft ?? "" });
      setDraft(undefined);
      onChange();
    });
  }

  if (draft !== undefined) {
    return (
      <form className="form" onSubmit={onSubmit}>
        <label>
          {t("bot.description")}
          <textarea
            rows={5}
            maxLength={DESCRIPTION_LENGTH}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
          />
          <span className="hint">{t("bot.descriptionHint", { max: DESCRIPTION_LENGTH })}</span>
        </label>
        <FormError error={error} />
        <div className="inline-actions">
          <button type="submit" className="primary" disabled={pending}>
            {t("bot.save")}
          </button>
          <button type="button" onClick={() => setDraft(undefined)} disabled={pending}>
            {t("bot.cancel")}
          </button>
        </div>
      </form>
    );
  }
  return (
    <>
      {bot.description && <p className="description">{bot.description}</p>}
      {isOwner && (
        <p>
          <button type="button" onClick={() => setDraft(bot.description)}>
            {t("bot.editDescription")}
          </button>
        </p>
      )}
    </>
  );
}
