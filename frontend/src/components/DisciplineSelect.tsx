import { useTranslation } from "react-i18next";

import type { StoredDiscipline } from "../api/types";
import { formatTimeControl } from "../format/timeControl";

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
  return (
    <label>
      {t("disciplines.choose")}
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">{t("disciplines.freeTimes")}</option>
        {disciplines
          .filter((discipline) => !discipline.archived)
          .map((discipline) => (
            <option key={discipline.id} value={discipline.id}>
              {`${discipline.name} (${formatTimeControl(discipline)})`}
            </option>
          ))}
      </select>
    </label>
  );
}
