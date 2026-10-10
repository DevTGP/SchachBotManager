import { useState } from "react";
import { useTranslation } from "react-i18next";

import { fetchSettings } from "../../api/admin";
import type { AdminSettings } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { useApi } from "../../hooks/useApi";
import { SettingsGroupForm } from "./SettingsGroupForm";
import { SETTINGS_GROUPS } from "./settingsFields";

/** Limits of coders, invitations and logins, the rating rule and the queue estimate (E154). */
export function AdminSettingsPage() {
  const settings = useApi(fetchSettings, "admin-settings");
  return <ApiContent state={settings}>{(data) => <SettingsForms initial={data} />}</ApiContent>;
}

function SettingsForms({ initial }: { initial: AdminSettings }) {
  const { t } = useTranslation();
  const [recountPending, setRecountPending] = useState(initial.rating_recount_pending);
  return (
    <>
      {recountPending && <p role="status">{t("adminSettings.recountPending")}</p>}
      {SETTINGS_GROUPS.map((group) => (
        <SettingsGroupForm
          key={group}
          group={group}
          initial={initial[group]}
          onSaved={(saved) => setRecountPending(saved.rating_recount_pending)}
        />
      ))}
    </>
  );
}
