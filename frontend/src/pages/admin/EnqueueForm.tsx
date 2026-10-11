import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { enqueueMatches } from "../../api/admin";
import type { Bot, EnqueuedMatches, StoredDiscipline } from "../../api/types";
import { BotPicker } from "../../components/BotPicker";
import { FormError } from "../../components/FormError";
import { MatchFields } from "../../components/matchFields/MatchFields";
import { QueuedNotice } from "../../components/QueuedNotice";
import { useSubmit } from "../../hooks/useSubmit";
import { DEFAULT_FORM, type MatchForm, matchOrder } from "./matchOrder";

/**
 * Puts games between two bots into the queue, under a discipline or free times (E85, E100);
 * white and black may come preset, e.g. from the bot page (E160). Either side may be "Random":
 * the server draws a new bot for every game (E162).
 */
export function EnqueueForm({
  bots,
  disciplines,
  white,
  black,
}: {
  bots: Bot[];
  disciplines: StoredDiscipline[];
  white?: string;
  black?: string;
}) {
  const { t } = useTranslation();
  const { pending, error, submit } = useSubmit();
  const [queued, setQueued] = useState<EnqueuedMatches | undefined>(undefined);
  const [form, setForm] = useState<MatchForm>(() => {
    const known = (id: string | undefined) => bots.find((bot) => bot.id === id)?.id;
    return {
      ...DEFAULT_FORM,
      white: known(white) ?? bots[0]?.id ?? "",
      black: known(black) ?? bots[1]?.id ?? bots[0]?.id ?? "",
    };
  });

  function set(patch: Partial<MatchForm>) {
    setForm((current) => ({ ...current, ...patch }));
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setQueued(undefined);
    void submit(async () => {
      setQueued(await enqueueMatches(matchOrder(form)));
    });
  }

  return (
    <form className="form" onSubmit={onSubmit}>
      <div className="form-row">
        <BotPicker
          label={t("viewer.white")}
          bots={bots}
          value={form.white}
          random
          onChange={(white) => set({ white })}
        />
        <BotPicker
          label={t("viewer.black")}
          bots={bots}
          value={form.black}
          random
          onChange={(black) => set({ black })}
        />
      </div>
      <MatchFields variant="admin" disciplines={disciplines} form={form} onChange={set} />
      <FormError error={error} />
      {queued && <QueuedNotice queued={queued} />}
      <button type="submit" className="primary" disabled={pending || bots.length === 0}>
        {t("admin.enqueue")}
      </button>
    </form>
  );
}
