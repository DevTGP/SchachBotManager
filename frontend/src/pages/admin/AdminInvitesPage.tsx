import { useTranslation } from "react-i18next";

import { fetchInvites, fetchSettings, revokeInvite } from "../../api/admin";
import { ApiContent } from "../../components/ApiContent";
import { FormError } from "../../components/FormError";
import { formatDateTime } from "../../format/dateTime";
import { useApi } from "../../hooks/useApi";
import { useLocale } from "../../hooks/useLocale";
import { useSubmit } from "../../hooks/useSubmit";
import { InviteForm } from "./InviteForm";

/** Invite links: create one, see the open ones, revoke unused ones (E4, E83). */
export function AdminInvitesPage() {
  const { t } = useTranslation();
  const locale = useLocale();
  const invites = useApi(fetchInvites, "admin-invites");
  const settings = useApi(fetchSettings, "admin-settings");
  const { pending, error, submit } = useSubmit();

  function revoke(id: string) {
    void submit(async () => {
      await revokeInvite(id);
      invites.reload();
    });
  }

  return (
    <section>
      <h2>{t("admin.newInvite")}</h2>
      <ApiContent state={settings}>
        {(data) => <InviteForm settings={data.accounts} onCreated={invites.reload} />}
      </ApiContent>

      <h2>{t("admin.openInvites")}</h2>
      <FormError error={error} />
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
