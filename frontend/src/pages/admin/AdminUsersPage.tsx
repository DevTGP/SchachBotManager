import { useState } from "react";
import { useTranslation } from "react-i18next";

import { createPasswordReset, fetchUsers, updateUser } from "../../api/admin";
import type { OneTimeLink, User, UserUpdate } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { FormError } from "../../components/FormError";
import { OneTimeLinkBox } from "../../components/OneTimeLinkBox";
import { formatDateTime } from "../../format/dateTime";
import { useApi } from "../../hooks/useApi";
import { useLocale } from "../../hooks/useLocale";
import { useSubmit } from "../../hooks/useSubmit";
import { useSession } from "../../session/sessionContext";

const ROLES = ["player", "coder", "admin"] as const;

/** Accounts: role, active flag and a one-time link for a new password (E83, E85). */
export function AdminUsersPage() {
  const { t } = useTranslation();
  const locale = useLocale();
  const { user: me } = useSession();
  const users = useApi(fetchUsers, "admin-users");
  const { pending, error, submit } = useSubmit();
  const [reset, setReset] = useState<{ username: string; link: OneTimeLink } | undefined>();

  function change(user: User, update: UserUpdate) {
    void submit(async () => {
      await updateUser(user.id, update);
      users.reload();
    });
  }

  function resetLink(user: User) {
    setReset(undefined);
    void submit(async () => {
      setReset({ username: user.username, link: await createPasswordReset(user.id) });
    });
  }

  return (
    <section>
      <h2>{t("admin.users")}</h2>
      <FormError error={error} />
      {reset && (
        <OneTimeLinkBox
          title={t("admin.resetLinkFor", { username: reset.username })}
          url={reset.link.url}
          expiresAt={reset.link.expires_at}
        />
      )}
      <ApiContent state={users}>
        {(items) => (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>{t("account.username")}</th>
                  <th>{t("admin.role")}</th>
                  <th>{t("admin.status")}</th>
                  <th className="optional">{t("admin.created")}</th>
                  <th className="optional">{t("admin.lastLogin")}</th>
                  <th>{t("admin.actions")}</th>
                </tr>
              </thead>
              <tbody>
                {items.map((user) => {
                  const self = user.id === me?.id;
                  return (
                    <tr key={user.id}>
                      <td>
                        {user.username}
                        {self && <span className="muted"> ({t("admin.you")})</span>}
                      </td>
                      <td>
                        <select
                          aria-label={t("admin.roleOf", { username: user.username })}
                          value={user.role}
                          disabled={self || pending}
                          onChange={(event) =>
                            change(user, { role: event.target.value as User["role"] })
                          }
                        >
                          {ROLES.map((role) => (
                            <option key={role} value={role}>
                              {t(`role.${role}`)}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>{user.active ? t("admin.active") : t("admin.inactive")}</td>
                      <td className="optional">{formatDateTime(user.created_at, locale)}</td>
                      <td className="optional">
                        {user.last_login_at
                          ? formatDateTime(user.last_login_at, locale)
                          : t("common.none")}
                      </td>
                      <td className="inline-actions">
                        <button
                          type="button"
                          disabled={self || pending}
                          onClick={() => change(user, { active: !user.active })}
                        >
                          {user.active ? t("admin.deactivate") : t("admin.activate")}
                        </button>
                        <button
                          type="button"
                          disabled={pending || !user.active}
                          onClick={() => resetLink(user)}
                        >
                          {t("admin.resetLink")}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </ApiContent>
    </section>
  );
}
