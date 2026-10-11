import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import type { StoredDiscipline, TournamentFormat, TournamentRequest } from "../../api/types";
import { FormError } from "../../components/FormError";
import { NumberField } from "../../components/NumberField";
import { disciplineLabel } from "../../format/timeControl";
import { useLocale } from "../../hooks/useLocale";
import { useSubmit } from "../../hooks/useSubmit";
import { RecurrenceField } from "./RecurrenceField";
import { TiebreakField } from "./TiebreakField";
import {
  FORMATS,
  TOURNAMENT_TIEBREAKS,
  type TournamentForm,
  tournamentRequest,
  withFormat,
} from "./tournamentForm";

const MAX_NAME = 40;

type NumberKey =
  "gamesPerPairing" | "rounds" | "tiebreakPairs" | "minParticipants" | "priority" | "readyHours";

/**
 * Creates a tournament or changes one; changes apply from the next edition start, the format
 * only on create (E172). Only the fields of the chosen format are shown.
 */
export function TournamentEditor({
  initial,
  disciplines,
  submitLabel,
  formatFixed = false,
  onSave,
  onCancel,
}: {
  initial: TournamentForm;
  disciplines: StoredDiscipline[];
  submitLabel: string;
  formatFixed?: boolean;
  onSave: (request: TournamentRequest) => Promise<void>;
  onCancel?: () => void;
}) {
  const { t } = useTranslation();
  const locale = useLocale();
  const { pending, error, submit } = useSubmit();
  const usable = (keep: string) =>
    disciplines.filter((discipline) => !discipline.archived || discipline.id === keep);
  const main = usable(initial.disciplineId);
  const tiebreakOptions = usable(initial.tiebreakDisciplineId);
  const [form, setForm] = useState<TournamentForm>(() => ({
    ...initial,
    disciplineId: initial.disciplineId || (main[0]?.id ?? ""),
  }));

  function update(change: Partial<TournamentForm>) {
    setForm((current) => ({ ...current, ...change }));
  }

  function number(field: NumberKey, label: string, min?: number) {
    return (
      <NumberField
        label={t(label)}
        value={form[field]}
        min={min}
        onChange={(value) => update({ [field]: value })}
      />
    );
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void submit(() => onSave(tournamentRequest(form)));
  }

  const knockout = form.format === "knockout";
  const shown =
    typeof error !== "string" && error?.code === "name_taken" ? "tournaments.nameTaken" : error;
  return (
    <form className="form" onSubmit={onSubmit}>
      <label>
        {t("tournaments.name")}
        <input
          required
          maxLength={MAX_NAME}
          value={form.name}
          onChange={(event) => update({ name: event.target.value })}
        />
      </label>
      <div className="form-row">
        <label>
          {t("tournaments.format")}
          <select
            value={form.format}
            disabled={formatFixed}
            onChange={(event) =>
              setForm((current) => withFormat(current, event.target.value as TournamentFormat))
            }
          >
            {FORMATS.map((format) => (
              <option key={format} value={format}>
                {t(`tournamentFormat.${format}`)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("tournaments.discipline")}
          <select
            required
            value={form.disciplineId}
            onChange={(event) => update({ disciplineId: event.target.value })}
          >
            {main.map((discipline) => (
              <option key={discipline.id} value={discipline.id}>
                {disciplineLabel(discipline, locale)}
              </option>
            ))}
          </select>
        </label>
      </div>
      {formatFixed && <p className="hint">{t("tournaments.formatFixed")}</p>}
      <div className="form-row">
        {form.format === "swiss"
          ? number("rounds", "tournaments.rounds", 1)
          : number(
              "gamesPerPairing",
              knockout ? "tournaments.gamesPerDuel" : "tournaments.gamesPerPairing",
              1,
            )}
        {knockout && number("tiebreakPairs", "tournaments.tiebreakPairs")}
      </div>
      {knockout ? (
        <>
          <label>
            {t("tournaments.tiebreakDiscipline")}
            <select
              value={form.tiebreakDisciplineId}
              onChange={(event) => update({ tiebreakDisciplineId: event.target.value })}
            >
              <option value="">{t("tournaments.sameDiscipline")}</option>
              {tiebreakOptions.map((discipline) => (
                <option key={discipline.id} value={discipline.id}>
                  {disciplineLabel(discipline, locale)}
                </option>
              ))}
            </select>
          </label>
          <p className="hint">{t("tournaments.knockoutHint")}</p>
        </>
      ) : (
        <TiebreakField
          options={TOURNAMENT_TIEBREAKS}
          value={form.tiebreaks}
          onChange={(tiebreaks) => update({ tiebreaks })}
        />
      )}
      <div className="form-row">
        {number("minParticipants", "tournaments.minParticipants", 2)}
        {number("priority", "admin.priority")}
        {number("readyHours", "registration.readyHours", 1)}
      </div>
      <RecurrenceField value={form.recurrence} onChange={(recurrence) => update({ recurrence })} />
      <FormError error={shown} rules="tournamentError" />
      <div className="inline-actions">
        <button type="submit" className="primary" disabled={pending || main.length === 0}>
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
