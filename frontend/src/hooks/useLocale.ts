import { useTranslation } from "react-i18next";

import { currentLanguage, type Language } from "../i18n";

/** The interface language, also used for dates and numbers. */
export function useLocale(): Language {
  const { i18n } = useTranslation();
  return currentLanguage(i18n.resolvedLanguage);
}
