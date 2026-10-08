import type { DisciplineRequest, StoredDiscipline } from "../../api/types";
import { secondsToMs } from "./matchOrder";

/** The discipline form as typed: times in seconds, the tolerance in milliseconds (E100). */
export interface DisciplineForm {
  name: string;
  initialSeconds: string;
  incrementSeconds: string;
  startupSeconds: string;
  toleranceMs: string;
  maxMoves: string;
}

export const DEFAULT_DISCIPLINE_FORM: DisciplineForm = {
  name: "",
  initialSeconds: "180",
  incrementSeconds: "2",
  startupSeconds: "10",
  toleranceMs: "20",
  maxMoves: "500",
};

export function disciplineForm(discipline: StoredDiscipline): DisciplineForm {
  return {
    name: discipline.name,
    initialSeconds: String(discipline.initial_time_ms / 1000),
    incrementSeconds: String(discipline.increment_ms / 1000),
    startupSeconds: String(discipline.startup_ms / 1000),
    toleranceMs: String(discipline.tolerance_ms),
    maxMoves: String(discipline.max_moves),
  };
}

/** The request body; the API trims the name and checks the ranges. */
export function disciplineRequest(form: DisciplineForm): DisciplineRequest {
  return {
    name: form.name,
    initial_time_ms: secondsToMs(form.initialSeconds),
    increment_ms: secondsToMs(form.incrementSeconds),
    startup_ms: secondsToMs(form.startupSeconds),
    tolerance_ms: Number(form.toleranceMs),
    max_moves: Number(form.maxMoves),
  };
}
