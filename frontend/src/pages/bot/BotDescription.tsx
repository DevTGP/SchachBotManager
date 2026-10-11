import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { updateOwnBot } from "../../api/bots";
import type { BotDetail } from "../../api/types";
import { FormError } from "../../components/FormError";
import { useSubmit } from "../../hooks/useSubmit";

/** The most characters of a description (E95). */
export const DESCRIPTION_LENGTH = 500;

/**
 * The public description as plain text; while editing, the owner's form in its place (E95). The
 * button to edit sits in the bar of actions (U10).
 */
export function BotDescription({
  bot,
  editing,
  onDone,
  onChange,
}: {
  bot: BotDetail;
  editing: boolean;
  onDone: () => void;
  onChange: () => void;
}) {
  if (editing) return <DescriptionForm bot={bot} onDone={onDone} onChange={onChange} />;
  return bot.description ? <p className="description">{bot.description}</p> : null;
}

function DescriptionForm({
  bot,
  onDone,
  onChange,
}: {
  bot: BotDetail;
  onDone: () => void;
  onChange: () => void;
}) {
  const { t } = useTranslation();
  const { pending, error, submit } = useSubmit();
  const [draft, setDraft] = useState(bot.description);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void submit(async () => {
      await updateOwnBot(bot.id, { description: draft });
      onDone();
      onChange();
    });
  }

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
        <button type="button" onClick={onDone} disabled={pending}>
          {t("bot.cancel")}
        </button>
      </div>
    </form>
  );
}
