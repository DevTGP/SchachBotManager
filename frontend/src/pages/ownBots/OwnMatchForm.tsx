import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { enqueueOwnMatches } from "../../api/bots";
import type { Bot, CoderLimits, EnqueuedMatches, StoredDiscipline } from "../../api/types";
import { BotPicker } from "../../components/BotPicker";
import { FormError } from "../../components/FormError";
import { ColorSelect } from "../../components/matchFields/ColorSelect";
import { MatchFields } from "../../components/matchFields/MatchFields";
import { QueuedNotice } from "../../components/QueuedNotice";
import { useSubmit } from "../../hooks/useSubmit";
import { ownLimits } from "./ownLimits";
import { DEFAULT_OWN_FORM, type OwnMatchForm, ownMatchOrder } from "./ownMatchOrder";

/**
 * Games of an own verified bot against any verified bot, with the coder limits (E98, E100,
 * E154); both bots may come preset, e.g. from the bot page (E160). The opponent may be "Random":
 * the server draws a new one for every game (E162).
 */
export function OwnMatchForm({
  own,
  opponents,
  disciplines,
  limits,
  preset,
  onQueued,
}: {
  own: Bot[];
  opponents: Bot[];
  disciplines: StoredDiscipline[];
  limits: CoderLimits;
  preset?: { own?: string; opponent?: string };
  onQueued?: () => void;
}) {
  const { t } = useTranslation();
  const values = ownLimits(limits);
  const { pending, error, submit } = useSubmit();
  const [queued, setQueued] = useState<EnqueuedMatches | undefined>(undefined);
  const [form, setForm] = useState<OwnMatchForm>(() => ({
    ...DEFAULT_OWN_FORM,
    own: own.find((bot) => bot.id === preset?.own)?.id ?? own[0]?.id ?? "",
    opponent:
      opponents.find((bot) => bot.id === preset?.opponent)?.id ??
      opponents.find((bot) => bot.builtin)?.id ??
      opponents[0]?.id ??
      "",
  }));

  if (own.length === 0) return <p className="muted">{t("ownBots.noVerified")}</p>;

  function set(patch: Partial<OwnMatchForm>) {
    setForm((current) => ({ ...current, ...patch }));
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setQueued(undefined);
    void submit(async () => {
      setQueued(await enqueueOwnMatches(ownMatchOrder(form)));
      onQueued?.();
    });
  }

  return (
    <form className="form" onSubmit={onSubmit}>
      <div className="form-row">
        <BotPicker
          label={t("ownBots.ownBot")}
          bots={own}
          value={form.own}
          onChange={(value) => set({ own: value })}
        />
        <BotPicker
          label={t("ownBots.opponent")}
          bots={opponents}
          value={form.opponent}
          random
          onChange={(opponent) => set({ opponent })}
        />
        <ColorSelect
          label={t("ownBots.ownColor")}
          value={form.ownColor}
          onChange={(ownColor) => set({ ownColor })}
        />
      </div>
      <MatchFields
        variant="coder"
        disciplines={disciplines}
        form={form}
        limits={{
          initial: values.initialSeconds,
          incrementSeconds: values.incrementSeconds,
          games: values.games,
        }}
        onChange={set}
      />
      <p className="hint">{t("ownBots.limits", values)}</p>
      <FormError error={error} rules="ownMatchError" values={values} />
      {queued && <QueuedNotice queued={queued} />}
      <button type="submit" className="primary" disabled={pending || opponents.length === 0}>
        {t("admin.enqueue")}
      </button>
    </form>
  );
}
