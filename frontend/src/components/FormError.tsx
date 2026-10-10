import { useTranslation } from "react-i18next";

import type { ApiError } from "../api/client";

/**
 * A failed change: for an invalid field the rule of that field, otherwise the error code. A
 * broken upload rule also shows the API's message and the file to blame. A form with its own
 * rules names them under `rules`; fields missing there fall back to fieldError. Rules with
 * numbers from the settings get them through `values` (E154).
 */
export function FormError({
  error,
  rules = "fieldError",
  values,
}: {
  error: ApiError | string | undefined;
  rules?: string;
  values?: Record<string, number>;
}) {
  const { t } = useTranslation();
  if (error === undefined) return null;
  let text: string;
  let detail: string | undefined;
  if (typeof error === "string") text = t(error);
  else if (error.code === "invalid_parameter" && error.field)
    text = t(
      [`${rules}.${error.field}`, `fieldError.${error.field}`, "error.invalid_parameter"],
      values,
    );
  else text = t(`error.${error.code}`);
  if (typeof error !== "string" && error.code === "invalid_upload") {
    detail = error.path ? `${error.path}: ${error.message}` : error.message;
  }
  return (
    <p className="error" role="alert">
      {text}
      {detail && (
        <>
          <br />
          <span className="info-text">{detail}</span>
        </>
      )}
    </p>
  );
}
