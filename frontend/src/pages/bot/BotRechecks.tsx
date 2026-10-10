import { useTranslation } from "react-i18next";

import type { VerificationReport } from "../../api/types";
import { useLocale } from "../../hooks/useLocale";
import { ReportStages } from "./ReportStages";
import { reportFacts } from "./reportFacts";

/** The reports of the rechecks an admin started, newest first; they never change the status (E153). */
export function BotRechecks({ rechecks }: { rechecks: VerificationReport[] }) {
  const { t } = useTranslation();
  const locale = useLocale();
  if (rechecks.length === 0) return null;
  return (
    <section>
      <h2>{t("bot.rechecks")}</h2>
      {rechecks.map((report, index) => (
        <details key={`${report.finished_at}-${index}`}>
          <summary>{reportFacts(report, t, locale)}</summary>
          <ReportStages report={report} />
        </details>
      ))}
    </section>
  );
}
