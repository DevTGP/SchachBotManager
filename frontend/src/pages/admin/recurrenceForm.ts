import type { Recurrence } from "../../api/types";
import {
  fromLocalInput,
  type IntervalUnit,
  intervalHours,
  nextFullHour,
  splitInterval,
  toLocalInput,
} from "../../format/recurrence";

/** The calendar as typed: first start in local time, interval as amount and unit (E171, E180). */
export interface RecurrenceForm {
  enabled: boolean;
  firstStart: string;
  amount: string;
  unit: IntervalUnit;
}

export const DEFAULT_RECURRENCE_FORM: RecurrenceForm = {
  enabled: false,
  firstStart: "",
  amount: "1",
  unit: "days",
};

export function recurrenceForm(recurrence: Recurrence | null): RecurrenceForm {
  if (recurrence === null) return DEFAULT_RECURRENCE_FORM;
  const { amount, unit } = splitInterval(recurrence.interval_hours);
  return {
    enabled: true,
    firstStart: toLocalInput(recurrence.first_start),
    amount: String(amount),
    unit,
  };
}

/** Switching the calendar on suggests the next full hour as first start. */
export function withCalendar(form: RecurrenceForm, enabled: boolean): RecurrenceForm {
  return { ...form, enabled, firstStart: form.firstStart || nextFullHour() };
}

export function recurrenceRequest(form: RecurrenceForm): Recurrence | null {
  if (!form.enabled) return null;
  return {
    first_start: fromLocalInput(form.firstStart),
    interval_hours: intervalHours(Number(form.amount), form.unit),
  };
}
