import { type FormEvent, startTransition, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";

import { changePassword, logout } from "../../api/account";
import { FormError } from "../../components/FormError";
import { PasswordFields } from "../../components/PasswordFields";
import { useSubmit } from "../../hooks/useSubmit";
import { useSession } from "../../session/sessionContext";
import { ApiTokens } from "./ApiTokens";

/** The own account: who is logged in, a new password, logging out (E83), API tokens (E116). */
export function AccountPage() {
  const { t } = useTranslation();
  const { user, setUser } = useSession();
  const navigate = useNavigate();
  const change = useSubmit();
  const leave = useSubmit();
  const [current, setCurrent] = useState("");
  const [password, setPassword] = useState("");
  const [repeat, setRepeat] = useState("");
  const [changed, setChanged] = useState(false);

  if (!user) return null;

  function onChange(event: FormEvent) {
    event.preventDefault();
    setChanged(false);
    if (password !== repeat) return change.fail("account.mismatch");
    void change.submit(async () => {
      await changePassword(current, password);
      setCurrent("");
      setPassword("");
      setRepeat("");
      setChanged(true);
    });
  }

  function onLogout() {
    void leave.submit(async () => {
      await logout();
      // The router renders navigations as transitions; clearing the user in one as well
      // keeps this page from seeing a guest and sending them to the login first.
      await navigate("/", { replace: true });
      startTransition(() => setUser(null));
    });
  }

  return (
    <>
      <h1>{t("account.title")}</h1>
      <p>
        {t("account.loggedInAs", { username: user.username })}{" "}
        <span className="muted">({t(`role.${user.role}`)})</span>
      </p>
      <p>
        <button type="button" onClick={onLogout} disabled={leave.pending}>
          {t("account.logout")}
        </button>
      </p>
      <FormError error={leave.error} />

      <h2>{t("account.changePassword")}</h2>
      <form className="form" onSubmit={onChange}>
        <label>
          {t("account.currentPassword")}
          <input
            type="password"
            autoComplete="current-password"
            required
            value={current}
            onChange={(event) => setCurrent(event.target.value)}
          />
        </label>
        <PasswordFields
          password={password}
          repeat={repeat}
          onPassword={setPassword}
          onRepeat={setRepeat}
        />
        <FormError error={change.error} />
        {changed && <p role="status">{t("account.passwordChanged")}</p>}
        <button type="submit" className="primary" disabled={change.pending}>
          {t("account.savePassword")}
        </button>
      </form>
      {user.role !== "player" && <ApiTokens />}
    </>
  );
}
