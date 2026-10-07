import { useTranslation } from "react-i18next";

import { formatDateTime } from "../format/dateTime";
import { useLocale } from "../hooks/useLocale";
import { CopyButton } from "./CopyButton";

/** A link that is shown only once; the server keeps nothing but its hash (E83). */
export function OneTimeLinkBox({
  title,
  url,
  expiresAt,
}: {
  title: string;
  url: string;
  expiresAt: string;
}) {
  const { t } = useTranslation();
  const locale = useLocale();
  return (
    <section className="link-box" role="status">
      <p>
        <strong>{title}</strong>
      </p>
      <div className="link-row">
        <input readOnly value={url} aria-label={t("oneTimeLink.url")} onFocus={select} />
        <CopyButton text={url} label={t("oneTimeLink.copy")} />
      </div>
      <p className="muted small">
        {t("oneTimeLink.note", { expires: formatDateTime(expiresAt, locale) })}
      </p>
    </section>
  );
}

function select(event: React.FocusEvent<HTMLInputElement>) {
  event.currentTarget.select();
}
