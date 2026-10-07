import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { createInvite, fetchInvites, revokeInvite } from "../../api/admin";
import type { CreatedInvite, Role } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { FormError } from "../../components/FormError";
import { OneTimeLinkBox } from "../../components/OneTimeLinkBox";
import { formatDateTime } from "../../format/dateTime";
import { useApi } from "../../hooks/useApi";
import { useLocale } from "../../hooks/useLocale";
import { useSubmit } from "../../hooks/useSubmit";

const DEFAULT_VALID_DAYS = 7;
const MAX_VALID_DAYS = 30;

/** Invite links: create one, see the open ones, revoke unused ones (E4, E83). */
export function AdminInvitesPage() {
  const { t } = useTranslation();
  const locale = useLocale();
  const invites = useApi(fetchInvites, "admin-invites");
  const { pending, error, submit } = useSubmit();
  const [role, setRole] = useState<Role>("coder");
  const [validDays, setValidDays] = useState(String(DEFAULT_VALID_DAYS));
  const [created, setCreated] = useState<CreatedInvite | undefined>();

  function onCreate(event: FormEvent) {
    event.preventDefault();
    setCreated(undefined);
    void submit(async () => {
      setCreated(await createInvite(role, Number(validDays)));
      invites.reload();
    });
  }

  function revoke(id: string) {
    void submit(async () => {
      await revokeInvite(id);
      invites.reload();
    });
  }

  return (
    <section>
      <h2>{t("admin.newInvite")}</h2>
      <form className="form" onSubmit={onCreate}>
        <div className="form-row">
          <label>
            {t("admin.role")}
            <select value={role} onChange={(event) => setRole(event.target.value as Role)}>
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
              max={MAX_VALID_DAYS}
              value={validDays}
              onChange={(event) => setValidDays(event.target.value)}
            />
          </label>
        </div>
        <FormError error={error} />
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

      <h2>{t("admin.openInvites")}</h2>
      <ApiContent state={invites}>
        {(items) =>
          items.length === 0 ? (
            <p className="muted">{t("admin.noInvites")}</p>
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>{t("admin.role")}</th>
                    <th>{t("admin.createdBy")}</th>
                    <th className="optional">{t("admin.created")}</th>
                    <th>{t("admin.expires")}</th>
                    <th>{t("admin.actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((invite) => (
                    <tr key={invite.id}>
                      <td>{t(`role.${invite.role}`)}</td>
                      <td>{invite.created_by ?? t("admin.commandLine")}</td>
                      <td className="optional">{formatDateTime(invite.created_at, locale)}</td>
                      <td>{formatDateTime(invite.expires_at, locale)}</td>
                      <td>
                        <button type="button" disabled={pending} onClick={() => revoke(invite.id)}>
                          {t("admin.revoke")}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        }
      </ApiContent>
    </section>
  );
}
