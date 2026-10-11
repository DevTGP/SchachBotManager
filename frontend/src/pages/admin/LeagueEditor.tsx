import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import type { LeagueRequest, StoredDiscipline } from "../../api/types";
import { FormError } from "../../components/FormError";
import { NumberField } from "../../components/NumberField";
import { disciplineLabel } from "../../format/timeControl";
import { useLocale } from "../../hooks/useLocale";
import { useSubmit } from "../../hooks/useSubmit";
import { type LeagueForm, leagueRequest, TIEBREAKS } from "./leagueForm";
import { RecurrenceField } from "./RecurrenceField";
import { TiebreakField } from "./TiebreakField";

const MAX_NAME = 40;

type NumberKey = {
  [Key in keyof LeagueForm]: LeagueForm[Key] extends string ? Key : never;
}[keyof LeagueForm];

/** Creates a league or changes one; changes apply from the next season start (E131). */
export function LeagueEditor({
  initial,
  disciplines,
  submitLabel,
  onSave,
  onCancel,
}: {
  initial: LeagueForm;
  disciplines: StoredDiscipline[];
  submitLabel: string;
  onSave: (request: LeagueRequest) => Promise<void>;
  onCancel?: () => void;
}) {
  const { t } = useTranslation();
  const locale = useLocale();
  const { pending, error, submit } = useSubmit();
  const usable = disciplines.filter(
    (discipline) => !discipline.archived || discipline.id === initial.disciplineId,
  );
  const [form, setForm] = useState<LeagueForm>(() => ({
    ...initial,
    disciplineId: initial.disciplineId || (usable[0]?.id ?? ""),
  }));

  function set(field: NumberKey, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function number(field: NumberKey, label: string, step?: string) {
    return (
      <NumberField
        label={t(label)}
        value={form[field]}
        step={step}
        onChange={(value) => set(field, value)}
      />
    );
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void submit(() => onSave(leagueRequest(form)));
  }

  const shown =
    typeof error !== "string" && error?.code === "name_taken" ? "leagues.nameTaken" : error;
  return (
    <form className="form" onSubmit={onSubmit}>
      <label>
        {t("leagues.name")}
        <input
          required
          maxLength={MAX_NAME}
          value={form.name}
          onChange={(event) => set("name", event.target.value)}
        />
      </label>
      <label>
        {t("leagues.discipline")}
        <select
          required
          value={form.disciplineId}
          onChange={(event) => set("disciplineId", event.target.value)}
        >
          {usable.map((discipline) => (
            <option key={discipline.id} value={discipline.id}>
              {disciplineLabel(discipline, locale)}
            </option>
          ))}
        </select>
      </label>
      <div className="form-row">
        {number("tiers", "leagues.tiers")}
        {number("tierSize", "leagues.tierSize")}
        {number("gamesPerPairing", "leagues.gamesPerPairing")}
        {number("promotions", "leagues.promotions")}
      </div>
      <div className="form-row">
        {number("win", "leagues.win", "0.5")}
        {number("draw", "leagues.draw", "0.5")}
        {number("loss", "leagues.loss", "0.5")}
      </div>
      <TiebreakField
        options={TIEBREAKS}
        value={form.tiebreaks}
        onChange={(tiebreaks) => setForm((current) => ({ ...current, tiebreaks }))}
      />
      <div className="form-row">
        {number("minParticipants", "leagues.minParticipants")}
        {number("priority", "admin.priority")}
        {number("readyHours", "registration.readyHours")}
      </div>
      <RecurrenceField
        value={form.recurrence}
        onChange={(recurrence) => setForm((current) => ({ ...current, recurrence }))}
      />
      <FormError error={shown} rules="leagueError" />
      <div className="inline-actions">
        <button type="submit" className="primary" disabled={pending || usable.length === 0}>
          {submitLabel}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel}>
            {t("bot.cancel")}
          </button>
        )}
      </div>
    </form>
  );
}
