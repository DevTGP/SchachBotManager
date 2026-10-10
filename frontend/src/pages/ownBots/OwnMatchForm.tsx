import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { enqueueOwnMatches } from "../../api/bots";
import type { Bot, CoderLimits, EnqueuedMatches, StoredDiscipline } from "../../api/types";
import { DisciplineSelect } from "../../components/DisciplineSelect";
import { FormError } from "../../components/FormError";
import { NumberField } from "../../components/NumberField";
import { QueuedNotice } from "../../components/QueuedNotice";
import { RatedField } from "../../components/RatedField";
import { StartPositionField } from "../../components/StartPositionField";
import { botLabel } from "../../format/botLabel";
import { useSubmit } from "../../hooks/useSubmit";
import { ownLimits } from "./ownLimits";
import { DEFAULT_OWN_FORM, type OwnMatchForm, ownMatchOrder } from "./ownMatchOrder";

/**
 * Games of an own verified bot against any verified bot, with the coder limits (E98, E100,
 * E154); both bots may come preset, e.g. from the bot page (E160).
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

  function set<K extends keyof OwnMatchForm>(field: K, value: OwnMatchForm[K]) {
    setForm((current) => ({ ...current, [field]: value }));
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
        <label>
          {t("ownBots.ownBot")}
          <select value={form.own} onChange={(event) => set("own", event.target.value)}>
            {own.map((bot) => (
              <option key={bot.id} value={bot.id}>
                {botLabel(bot)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("ownBots.opponent")}
          <select value={form.opponent} onChange={(event) => set("opponent", event.target.value)}>
            {opponents.map((bot) => (
              <option key={bot.id} value={bot.id}>
                {botLabel(bot)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("ownBots.ownColor")}
          <select
            value={form.ownColor}
            onChange={(event) => set("ownColor", event.target.value as OwnMatchForm["ownColor"])}
          >
            <option value="white">{t("viewer.white")}</option>
            <option value="black">{t("viewer.black")}</option>
          </select>
        </label>
      </div>
      <div className="form-row">
        <DisciplineSelect
          disciplines={disciplines}
          value={form.discipline}
          onChange={(value) => set("discipline", value)}
        />
        {!form.discipline && (
          <>
            <NumberField
              label={t("admin.initialSeconds")}
              value={form.initialSeconds}
              step="any"
              min={1}
              max={values.initialSeconds}
              onChange={(value) => set("initialSeconds", value)}
            />
            <NumberField
              label={t("admin.incrementSeconds")}
              value={form.incrementSeconds}
              step="any"
              max={values.incrementSeconds}
              onChange={(value) => set("incrementSeconds", value)}
            />
          </>
        )}
        <NumberField
          label={t("admin.games")}
          value={form.games}
          min={1}
          max={values.games}
          onChange={(value) => set("games", value)}
        />
      </div>
      <label className="checkbox">
        <input
          type="checkbox"
          checked={form.alternate}
          onChange={(event) => set("alternate", event.target.checked)}
        />
        {t("admin.alternate")}
      </label>
      <StartPositionField value={form.startFen} onChange={(fen) => set("startFen", fen)} />
      <RatedField checked={form.rated} onChange={(rated) => set("rated", rated)} />
      <p className="hint">{t("ownBots.limits", values)}</p>
      <FormError error={error} rules="ownMatchError" values={values} />
      {queued && <QueuedNotice queued={queued} />}
      <button type="submit" className="primary" disabled={pending || opponents.length === 0}>
        {t("admin.enqueue")}
      </button>
    </form>
  );
}
