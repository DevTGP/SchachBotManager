import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";

import { redeemInvite } from "../../api/account";
import { FormError } from "../../components/FormError";
import { PasswordFields } from "../../components/PasswordFields";
import { useSubmit } from "../../hooks/useSubmit";
import { useOneTimeToken } from "../../session/oneTimeToken";
import { useSession } from "../../session/sessionContext";

/** The rule of the API (E83); the browser checks it before sending. */
const USERNAME_PATTERN = "[A-Za-z0-9][A-Za-z0-9_.\\-]{2,31}";

/** /invite#token: the invited person picks name and password and is logged in (E83). */
export function InvitePage() {
  const { t } = useTranslation();
  const { setUser } = useSession();
  const navigate = useNavigate();
  const token = useOneTimeToken();
  const { pending, error, submit, fail } = useSubmit();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [repeat, setRepeat] = useState("");

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (password !== repeat) return fail("account.mismatch");
    void submit(async () => {
      setUser(await redeemInvite(token, username, password));
      void navigate("/account", { replace: true });
    });
  }

  return (
    <>
      <h1>{t("invite.title")}</h1>
      {token ? (
        <form className="form" onSubmit={onSubmit}>
          <p>{t("invite.intro")}</p>
          <label>
            {t("account.username")}
            <input
              autoComplete="username"
              required
              pattern={USERNAME_PATTERN}
              maxLength={32}
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
            <span className="hint">{t("account.usernameRule")}</span>
          </label>
          <PasswordFields
            password={password}
            repeat={repeat}
            onPassword={setPassword}
            onRepeat={setRepeat}
          />
          <FormError error={error} />
          <button type="submit" className="primary" disabled={pending}>
            {t("invite.submit")}
          </button>
        </form>
      ) : (
        <p className="error" role="alert">
          {t("error.invalid_token")}
        </p>
      )}
    </>
  );
}
