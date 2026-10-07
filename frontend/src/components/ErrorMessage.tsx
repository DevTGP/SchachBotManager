import { useTranslation } from "react-i18next";

import type { ApiError } from "../api/client";

/** The API's error codes in the interface language; its English message is for logs only. */
export function ErrorMessage({ error }: { error: ApiError }) {
  const { t } = useTranslation();
  return (
    <p className="error" role="alert">
      {t(`error.${error.code}`)}
    </p>
  );
}
