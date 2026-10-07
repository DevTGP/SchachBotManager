import { useTranslation } from "react-i18next";

export const PASSWORD_MIN = 10;
export const PASSWORD_MAX = 128;

/** A new password, typed twice; the API checks the length again (E84). */
export function PasswordFields({
  password,
  repeat,
  onPassword,
  onRepeat,
}: {
  password: string;
  repeat: string;
  onPassword: (value: string) => void;
  onRepeat: (value: string) => void;
}) {
  const { t } = useTranslation();
  return (
    <>
      <label>
        {t("account.newPassword")}
        <input
          type="password"
          autoComplete="new-password"
          required
          minLength={PASSWORD_MIN}
          maxLength={PASSWORD_MAX}
          value={password}
          onChange={(event) => onPassword(event.target.value)}
        />
        <span className="hint">{t("account.passwordRule", { min: PASSWORD_MIN })}</span>
      </label>
      <label>
        {t("account.repeatPassword")}
        <input
          type="password"
          autoComplete="new-password"
          required
          value={repeat}
          onChange={(event) => onRepeat(event.target.value)}
        />
      </label>
    </>
  );
}
