import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { createInvite } from "../../api/admin";
import type { AccountSettings, CreatedInvite, Role } from "../../api/types";
import { FormError } from "../../components/FormError";
import { OneTimeLinkBox } from "../../components/OneTimeLinkBox";
import { useSubmit } from "../../hooks/useSubmit";

/** A new invite link; validity by default and at most as in the settings (E83, E154). */
export function InviteForm({
  settings,
  onCreated,
}: {
  settings: AccountSettings;
  onCreated: () => void;
}) {
  const { t } = useTranslation();
  const { pending, error, submit } = useSubmit();
  const [role, setRole] = useState<Role>("coder");
  const [validDays, setValidDays] = useState(String(settings.invite_days));
  const [created, setCreated] = useState<CreatedInvite | undefined>();

  function onCreate(event: FormEvent) {
    event.preventDefault();
    setCreated(undefined);
    void submit(async () => {
      setCreated(await createInvite(role, Number(validDays)));
      onCreated();
    });
  }

  return (
    <>
      <form className="form" onSubmit={onCreate}>
        <div className="form-row">
          <label>
            {t("admin.role")}
            <select value={role} onChange={(event) => setRole(event.target.value as Role)}>
              <option value="player">{t("role.player")}</option>
              <option value="coder">{t("role.coder")}</option>
              <option value="admin">{t("role.admin")}</option>
            </select>
          </label>
          <label>
            {t("admin.validDays")}
            <input
              type="number"
              required
              min={1}
              max={settings.invite_max_days}
              value={validDays}
              onChange={(event) => setValidDays(event.target.value)}
            />
          </label>
        </div>
        <FormError error={error} values={{ max: settings.invite_max_days }} />
        <button type="submit" className="primary" disabled={pending}>
          {t("admin.createInvite")}
        </button>
      </form>
      {created && (
        <OneTimeLinkBox
          title={t("admin.inviteLink", { role: t(`role.${created.invite.role}`) })}
          url={created.url}
          expiresAt={created.invite.expires_at}
        />
      )}
    </>
  );
}
