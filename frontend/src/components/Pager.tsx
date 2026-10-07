import { useTranslation } from "react-i18next";

export function Pager({
  offset,
  limit,
  total,
  onChange,
}: {
  offset: number;
  limit: number;
  total: number;
  onChange: (offset: number) => void;
}) {
  const { t } = useTranslation();
  if (total <= limit && offset === 0) return null;
  return (
    <nav className="pager" aria-label="pages">
      <button
        type="button"
        disabled={offset === 0}
        onClick={() => onChange(Math.max(0, offset - limit))}
      >
        {t("common.previous")}
      </button>
      <span>
        {t("common.page", {
          from: Math.min(offset + 1, total),
          to: Math.min(offset + limit, total),
          total,
        })}
      </span>
      <button
        type="button"
        disabled={offset + limit >= total}
        onClick={() => onChange(offset + limit)}
      >
        {t("common.next")}
      </button>
    </nav>
  );
}
