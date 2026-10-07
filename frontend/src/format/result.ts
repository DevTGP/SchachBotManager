import type { MatchSummary } from "../api/types";

const RESULTS: Record<string, string> = { "1-0": "1–0", "0-1": "0–1", "1/2-1/2": "½–½", "*": "*" };

export function formatResult(result: MatchSummary["result"]): string {
  return result === null ? "" : (RESULTS[result] ?? result);
}
