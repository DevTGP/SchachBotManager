import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

import de from "./de.json";
import en from "./en.json";

export const LANGUAGES = ["de", "en"] as const;
export type Language = (typeof LANGUAGES)[number];

/** Where the chosen language is kept, so the choice outlives the visit (E32). */
export const LANGUAGE_KEY = "sbm.language";

i18n.on("languageChanged", (language) => {
  document.documentElement.lang = language;
});

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { de: { translation: de }, en: { translation: en } },
    supportedLngs: LANGUAGES,
    nonExplicitSupportedLngs: true,
    load: "languageOnly",
    fallbackLng: "en",
    interpolation: { escapeValue: false },
    detection: {
      order: ["localStorage", "navigator"],
      lookupLocalStorage: LANGUAGE_KEY,
      caches: ["localStorage"],
    },
  });

/** The supported language in use; the browser may report a regional variant such as de-AT. */
export function currentLanguage(resolved: string | undefined): Language {
  const base = resolved?.split("-")[0];
  return LANGUAGES.find((language) => language === base) ?? "en";
}

export default i18n;
