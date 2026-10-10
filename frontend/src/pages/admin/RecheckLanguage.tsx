import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { recheckLanguage } from "../../api/admin";
import type { BotLanguage } from "../../api/types";
import { FormError } from "../../components/FormError";
import { useSubmit } from "../../hooks/useSubmit";

const LANGUAGES: BotLanguage[] = ["python", "cpp", "java", "csharp", "javascript"];

/**
 * Checks every verified or rejected uploaded bot of a language again, such as after the rules
 * changed; each recheck only adds a report (E153).
 */
export function RecheckLanguage() {
  const { t } = useTranslation();
  const { pending, error, submit } = useSubmit();
  const [language, setLanguage] = useState<BotLanguage>("python");
  const [queued, setQueued] = useState<number | undefined>(undefined);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setQueued(undefined);
    void submit(async () => {
      setQueued(await recheckLanguage(language));
    });
  }

  return (
    <section>
      <h2>{t("admin.recheckTitle")}</h2>
      <form className="form" onSubmit={onSubmit}>
        <p className="hint">{t("admin.recheckHint")}</p>
        <label>
          {t("bots.language")}
          <select
            value={language}
            onChange={(event) => setLanguage(event.target.value as BotLanguage)}
          >
            {LANGUAGES.map((code) => (
              <option key={code} value={code}>
                {t(`language.${code}`)}
              </option>
            ))}
          </select>
        </label>
        <FormError error={error} />
        {queued !== undefined && (
          <p role="status">{t("admin.rechecksQueued", { count: queued })}</p>
        )}
        <button type="submit" className="primary" disabled={pending}>
          {t("admin.recheck")}
        </button>
      </form>
    </section>
  );
}
