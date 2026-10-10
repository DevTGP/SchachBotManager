import type { TFunction } from "i18next";

import type { VerificationReport } from "../../api/types";
import { formatDateTime } from "../../format/dateTime";

/** Result, time and rule set of a report in one line. */
export function reportFacts(report: VerificationReport, t: TFunction, locale: string): string {
  const facts = [
    report.result === "passed" ? t("bot.passed") : t("bot.failed"),
    formatDateTime(report.finished_at, locale),
  ];
  if (report.ruleset) facts.push(`${t("bot.ruleset")} ${report.ruleset}`);
  return facts.join(" · ");
}
