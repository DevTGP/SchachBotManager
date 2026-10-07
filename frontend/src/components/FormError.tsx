import { useTranslation } from "react-i18next";

import type { ApiError } from "../api/client";

/** A failed change: for an invalid field the rule of that field, otherwise the error code. */
export function FormError({ error }: { error: ApiError | string | undefined }) {
  const { t } = useTranslation();
  if (error === undefined) return null;
  let text: string;
  if (typeof error === "string") text = t(error);
  else if (error.code === "invalid_parameter" && error.field)
    text = t(`fieldError.${error.field}`, { defaultValue: t("error.invalid_parameter") });
  else text = t(`error.${error.code}`);
  return (
    <p className="error" role="alert">
      {text}
    </p>
  );
}
