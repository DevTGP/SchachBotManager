import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { changePassword } from "../../api/account";
import { FormError } from "../../components/FormError";
import { PasswordFields } from "../../components/PasswordFields";
import { useSubmit } from "../../hooks/useSubmit";
import { useSession } from "../../session/sessionContext";
import { ApiTokens } from "./ApiTokens";
import { OwnRating } from "./OwnRating";

/**
 * The own account in sections: who is logged in, the own rating (E117, E169), a new password and
 * API tokens (E116). Logging out lives in the account menu (G7).
 */
export function AccountPage() {
  const { t } = useTranslation();
  const { user } = useSession();
  const change = useSubmit();
  const [current, setCurrent] = useState("");
  const [password, setPassword] = useState("");
  const [repeat, setRepeat] = useState("");
  const [changed, setChanged] = useState(false);

  if (!user) return null;
  const coder = user.role !== "player";

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

  return (
    <>
      <h1>{t("account.title")}</h1>
      <p>
        {t("account.loggedInAs", { username: user.username })}{" "}
        <span className="muted">({t(`role.${user.role}`)})</span>
      </p>
      {coder && (
        <p>
          <Link to="/matches?mine=true">{t("account.ownMatches")}</Link>
        </p>
      )}
      <OwnRating />

      <section>
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
      </section>
      {coder && <ApiTokens />}
    </>
  );
}
