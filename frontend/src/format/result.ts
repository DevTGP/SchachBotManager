import type { MatchSummary } from "../api/types";

// "0-0": a league or tournament game neither account was ready for (E184).
const RESULTS: Record<string, string> = {
  "1-0": "1–0",
  "0-1": "0–1",
  "1/2-1/2": "½–½",
  "0-0": "0–0",
  "*": "*",
};

export function formatResult(result: MatchSummary["result"]): string {
  return result === null ? "" : (RESULTS[result] ?? result);
}
