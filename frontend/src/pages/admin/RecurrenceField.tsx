import { useTranslation } from "react-i18next";

import type { IntervalUnit } from "../../format/recurrence";
import { type RecurrenceForm, withCalendar } from "./recurrenceForm";
import { NumberField } from "../../components/NumberField";

const UNITS: IntervalUnit[] = ["hours", "days", "weeks"];

/**
 * The calendar of a league or tournament: off, an admin starts each season or edition;
 * on, a first start in local time and an interval (E171, E180).
 */
export function RecurrenceField({
  value,
  onChange,
}: {
  value: RecurrenceForm;
  onChange: (value: RecurrenceForm) => void;
}) {
  const { t } = useTranslation();
  return (
    <fieldset>
      <legend>{t("recurrence.title")}</legend>
      <label className="checkbox">
        <input
          type="checkbox"
          checked={value.enabled}
          onChange={(event) => onChange(withCalendar(value, event.target.checked))}
        />
        {t("recurrence.enabled")}
      </label>
      {value.enabled ? (
        <div className="form-row">
          <label>
            {t("recurrence.firstStart")}
            <input
              type="datetime-local"
              required
              value={value.firstStart}
              onChange={(event) => onChange({ ...value, firstStart: event.target.value })}
            />
          </label>
          <NumberField
            label={t("recurrence.every")}
            value={value.amount}
            min={1}
            onChange={(amount) => onChange({ ...value, amount })}
          />
          <label>
            {t("recurrence.unit")}
            <select
              value={value.unit}
              onChange={(event) => onChange({ ...value, unit: event.target.value as IntervalUnit })}
            >
              {UNITS.map((unit) => (
                <option key={unit} value={unit}>
                  {t(`recurrence.units.${unit}`)}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : (
        <p className="hint">{t("recurrence.manualHint")}</p>
      )}
    </fieldset>
  );
}
