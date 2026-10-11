import { useTranslation } from "react-i18next";

import type { StoredDiscipline } from "../api/types";
import { disciplineLabel } from "../format/timeControl";
import { useLocale } from "../hooks/useLocale";

/** A discipline in use, or "" for free times; only discipline games count for the rating (E100). */
export function DisciplineSelect({
  disciplines,
  value,
  onChange,
}: {
  disciplines: StoredDiscipline[];
  value: string;
  onChange: (value: string) => void;
}) {
  const { t } = useTranslation();
  const locale = useLocale();
  return (
    <label>
      {t("disciplines.choose")}
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">{t("disciplines.freeTimes")}</option>
        {disciplines
          .filter((discipline) => !discipline.archived)
          .map((discipline) => (
            <option key={discipline.id} value={discipline.id}>
              {disciplineLabel(discipline, locale)}
            </option>
          ))}
      </select>
    </label>
  );
}
