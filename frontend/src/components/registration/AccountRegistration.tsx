import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { fetchUsers } from "../../api/admin";
import type { LeagueBot } from "../../api/types";
import { useApi } from "../../hooks/useApi";
import { useSubmit } from "../../hooks/useSubmit";
import { ApiContent } from "../ApiContent";
import { FormError } from "../FormError";

/** Admins register any active account that is not in the league or tournament yet (E182). */
export function AccountRegistration({
  registered,
  register,
  onChange,
}: {
  registered: LeagueBot[];
  register: (userId: string) => Promise<unknown>;
  onChange: () => void;
}) {
  const { t } = useTranslation();
  const users = useApi(fetchUsers, "admin/users");
  const { pending, error, submit } = useSubmit();
  const [chosen, setChosen] = useState("");
  const taken = new Set(registered.map((entry) => entry.user_id));

  return (
    <section>
      <h2>{t("registration.account")}</h2>
      <ApiContent state={users}>
        {(list) => {
          const free = list
            .filter((user) => user.active && !taken.has(user.id))
            .sort((a, b) => a.username.localeCompare(b.username));
          if (free.length === 0) return <p className="muted">{t("registration.noFreeAccounts")}</p>;
          const userId = free.some((user) => user.id === chosen) ? chosen : free[0]!.id;
          function onSubmit(event: FormEvent) {
            event.preventDefault();
            void submit(async () => {
              await register(userId);
              onChange();
            });
          }
          return (
            <form className="form" onSubmit={onSubmit}>
              <label>
                {t("registration.accountLabel")}
                <select value={userId} onChange={(event) => setChosen(event.target.value)}>
                  {free.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.username}
                    </option>
                  ))}
                </select>
              </label>
              <FormError error={error} />
              <div className="inline-actions">
                <button type="submit" className="primary" disabled={pending}>
                  {t("leagues.registerButton")}
                </button>
              </div>
            </form>
          );
        }}
      </ApiContent>
    </section>
  );
}
