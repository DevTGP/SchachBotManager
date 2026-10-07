import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";

import { redeemPasswordReset } from "../../api/account";
import { FormError } from "../../components/FormError";
import { PasswordFields } from "../../components/PasswordFields";
import { useSubmit } from "../../hooks/useSubmit";
import { useOneTimeToken } from "../../session/oneTimeToken";
import { useSession } from "../../session/sessionContext";

/** /reset-password#token: a new password from the one-time link of an admin (E83). */
export function ResetPasswordPage() {
  const { t } = useTranslation();
  const { setUser } = useSession();
  const navigate = useNavigate();
  const token = useOneTimeToken();
  const { pending, error, submit, fail } = useSubmit();
  const [password, setPassword] = useState("");
  const [repeat, setRepeat] = useState("");

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (password !== repeat) return fail("account.mismatch");
    void submit(async () => {
      setUser(await redeemPasswordReset(token, password));
      void navigate("/account", { replace: true });
    });
  }

  return (
    <>
      <h1>{t("reset.title")}</h1>
      {token ? (
        <form className="form" onSubmit={onSubmit}>
          <p>{t("reset.intro")}</p>
          <PasswordFields
            password={password}
            repeat={repeat}
            onPassword={setPassword}
            onRepeat={setRepeat}
          />
          <FormError error={error} />
          <button type="submit" className="primary" disabled={pending}>
            {t("reset.submit")}
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
