import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import type { DisciplineRequest } from "../../api/types";
import { FormError } from "../../components/FormError";
import { NumberField } from "../../components/NumberField";
import { useSubmit } from "../../hooks/useSubmit";
import { type DisciplineForm, disciplineRequest } from "./disciplineForm";

const MAX_NAME = 40;

/** Creates a discipline or changes one; changes apply to games queued afterwards (E100). */
export function DisciplineEditor({
  initial,
  submitLabel,
  onSave,
  onCancel,
}: {
  initial: DisciplineForm;
  submitLabel: string;
  onSave: (request: DisciplineRequest) => Promise<void>;
  onCancel?: () => void;
}) {
  const { t } = useTranslation();
  const { pending, error, submit } = useSubmit();
  const [form, setForm] = useState(initial);

  function set(field: keyof DisciplineForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void submit(() => onSave(disciplineRequest(form)));
  }

  const shown =
    typeof error !== "string" && error?.code === "name_taken" ? "disciplines.nameTaken" : error;
  return (
    <form className="form" onSubmit={onSubmit}>
      <label>
        {t("disciplines.name")}
        <input
          required
          maxLength={MAX_NAME}
          value={form.name}
          onChange={(event) => set("name", event.target.value)}
        />
      </label>
      <div className="form-row">
        <NumberField
          label={t("admin.initialSeconds")}
          value={form.initialSeconds}
          step="any"
          min={1}
          onChange={(value) => set("initialSeconds", value)}
        />
        <NumberField
          label={t("admin.incrementSeconds")}
          value={form.incrementSeconds}
          step="any"
          onChange={(value) => set("incrementSeconds", value)}
        />
        <NumberField
          label={t("disciplines.startupSeconds")}
          value={form.startupSeconds}
          step="any"
          min={1}
          onChange={(value) => set("startupSeconds", value)}
        />
        <NumberField
          label={t("disciplines.toleranceMs")}
          value={form.toleranceMs}
          onChange={(value) => set("toleranceMs", value)}
        />
        <NumberField
          label={t("admin.maxMoves")}
          value={form.maxMoves}
          min={1}
          onChange={(value) => set("maxMoves", value)}
        />
      </div>
      <FormError error={shown} rules="disciplineError" />
      <div className="inline-actions">
        <button type="submit" className="primary" disabled={pending}>
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
