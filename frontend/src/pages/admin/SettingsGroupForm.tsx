import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { type SettingsGroups, updateSettings } from "../../api/admin";
import type { AdminSettings } from "../../api/types";
import { FormError } from "../../components/FormError";
import { NumberField } from "../../components/NumberField";
import { useSubmit } from "../../hooks/useSubmit";
import { fromForm, SETTINGS_FIELDS, type SettingsField, toForm } from "./settingsFields";

/** One group of /admin/settings; all its values are saved together (E154). */
export function SettingsGroupForm<G extends keyof SettingsGroups>({
  group,
  initial,
  onSaved,
}: {
  group: G;
  initial: SettingsGroups[G];
  onSaved: (settings: AdminSettings) => void;
}) {
  const { t } = useTranslation();
  const { pending, error, submit } = useSubmit();
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState(() => toForm(group, initial));
  const fields: readonly SettingsField<G>[] = SETTINGS_FIELDS[group];

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSaved(false);
    void submit(async () => {
      onSaved(await updateSettings(group, fromForm(group, form)));
      setSaved(true);
    });
  }

  return (
    <section>
      <h2>{t(`adminSettings.${group}`)}</h2>
      <form className="form" onSubmit={onSubmit}>
        <p className="hint">{t(`adminSettings.${group}Hint`)}</p>
        <div className="form-row">
          {fields.map(({ name, min, max, seconds }) => (
            <NumberField
              key={name}
              label={t(`adminSettings.${name}`)}
              value={form[name] ?? ""}
              step={seconds ? "any" : undefined}
              min={min}
              max={max}
              onChange={(value) => setForm((current) => ({ ...current, [name]: value }))}
            />
          ))}
        </div>
        <FormError error={error} rules="settingsError" />
        {saved && <p role="status">{t("adminSettings.saved")}</p>}
        <button type="submit" className="primary" disabled={pending}>
          {t("adminSettings.save")}
        </button>
      </form>
    </section>
  );
}
