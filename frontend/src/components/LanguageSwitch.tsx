import { useTranslation } from "react-i18next";

import { LANGUAGES } from "../i18n";
import { useLocale } from "../hooks/useLocale";

export function LanguageSwitch() {
  const { t, i18n } = useTranslation();
  const language = useLocale();
  return (
    <div className="language-switch" role="group" aria-label={t("app.language")}>
      {LANGUAGES.map((code) => (
        <button
          key={code}
          type="button"
          lang={code}
          aria-pressed={code === language}
          onClick={() => void i18n.changeLanguage(code)}
        >
          {code.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
