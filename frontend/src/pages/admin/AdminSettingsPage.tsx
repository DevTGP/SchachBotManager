import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { fetchSettings, type SettingsGroups, updateSettings } from "../../api/admin";
import type { AdminSettings } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { useApi } from "../../hooks/useApi";
import { useSubmit } from "../../hooks/useSubmit";
import { SettingsGroupFields } from "./SettingsGroupFields";
import { fromForm, SETTINGS_GROUPS, toForm } from "./settingsFields";

type Group = keyof SettingsGroups;
type Forms = Record<Group, Record<string, string>>;

function formsOf(settings: AdminSettings): Forms {
  return Object.fromEntries(
    SETTINGS_GROUPS.map((group) => [group, toForm(group, settings[group])]),
  ) as Forms;
}

function sameForm(a: Record<string, string>, b: Record<string, string>): boolean {
  return Object.keys(a).every((name) => a[name] === b[name]);
}

/** Limits of coders, invitations and logins, the rating rule and the queue estimate (E154). */
export function AdminSettingsPage() {
  const settings = useApi(fetchSettings, "admin-settings");
  return <ApiContent state={settings}>{(data) => <SettingsForm initial={data} />}</ApiContent>;
}

/**
 * All groups in one form with one button (U14): it saves the changed groups one after another,
 * each with its own request, and stops at the first the API refuses.
 */
function SettingsForm({ initial }: { initial: AdminSettings }) {
  const { t } = useTranslation();
  const { pending, error, submit } = useSubmit();
  const [saved, setSaved] = useState(() => formsOf(initial));
  const [form, setForm] = useState(saved);
  const [failed, setFailed] = useState<Group>();
  const [done, setDone] = useState(false);
  const [recountPending, setRecountPending] = useState(initial.rating_recount_pending);
  const changed = SETTINGS_GROUPS.filter((group) => !sameForm(form[group], saved[group]));

  function onChange(group: Group, name: string, value: string) {
    setDone(false);
    setForm((current) => ({ ...current, [group]: { ...current[group], [name]: value } }));
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setDone(false);
    void submit(async () => {
      for (const group of changed) {
        setFailed(group);
        const result = await updateSettings(group, fromForm(group, form[group]));
        setSaved((current) => ({ ...current, [group]: form[group] }));
        setRecountPending(result.rating_recount_pending);
      }
      setFailed(undefined);
      setDone(true);
    });
  }

  return (
    <form className="form settings-form" onSubmit={onSubmit}>
      {recountPending && <p role="status">{t("adminSettings.recountPending")}</p>}
      {SETTINGS_GROUPS.map((group) => (
        <SettingsGroupFields
          key={group}
          group={group}
          form={form[group]}
          changed={changed.includes(group)}
          error={failed === group ? error : undefined}
          onChange={(name, value) => onChange(group, name, value)}
        />
      ))}
      <div className="save-bar">
        <button type="submit" className="primary" disabled={pending || changed.length === 0}>
          {t("adminSettings.save")}
        </button>
        <span role="status">
          {changed.length > 0
            ? t("adminSettings.unsaved", { count: changed.length })
            : done && t("adminSettings.saved")}
        </span>
      </div>
    </form>
  );
}
