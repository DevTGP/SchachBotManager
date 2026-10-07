import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Navigate, useLocation } from "react-router";

import { login } from "../../api/account";
import { FormError } from "../../components/FormError";
import { useSubmit } from "../../hooks/useSubmit";
import { nextPath } from "../../session/nextPath";
import { useSession } from "../../session/sessionContext";

export function LoginPage() {
  const { t } = useTranslation();
  const { user, setUser } = useSession();
  const location = useLocation();
  const { pending, error, submit } = useSubmit();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  if (user) return <Navigate to={nextPath(location.search)} replace />;

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void submit(async () => setUser(await login(username, password)));
  }

  return (
    <>
      <h1>{t("login.title")}</h1>
      <form className="form" onSubmit={onSubmit}>
        <label>
          {t("account.username")}
          <input
            autoComplete="username"
            required
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />
        </label>
        <label>
          {t("account.password")}
          <input
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        <FormError error={error} />
        <button type="submit" className="primary" disabled={pending}>
          {t("login.submit")}
        </button>
      </form>
      <p className="muted small">{t("login.inviteOnly")}</p>
    </>
  );
}
