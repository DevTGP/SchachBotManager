import { useTranslation } from "react-i18next";

import type { SettingsGroups } from "../../api/admin";
import type { ApiError } from "../../api/client";
import { FormError } from "../../components/FormError";
import { NumberField } from "../../components/NumberField";
import { SETTINGS_FIELDS, type SettingsField } from "./settingsFields";

/** The fields of one group of /admin/settings, marked while they differ from the saved values. */
export function SettingsGroupFields<G extends keyof SettingsGroups>({
  group,
  form,
  changed,
  error,
  onChange,
}: {
  group: G;
  form: Record<string, string>;
  changed: boolean;
  error: ApiError | string | undefined;
  onChange: (name: string, value: string) => void;
}) {
  const { t } = useTranslation();
  const fields: readonly SettingsField<G>[] = SETTINGS_FIELDS[group];
  return (
    <section className="settings-group">
      <h2>
        {t(`adminSettings.${group}`)}
        {changed && <span className="badge changed">{t("adminSettings.changed")}</span>}
      </h2>
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
            onChange={(value) => onChange(name, value)}
          />
        ))}
      </div>
      <FormError error={error} rules="settingsError" />
    </section>
  );
}
