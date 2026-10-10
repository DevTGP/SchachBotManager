import { useTranslation } from "react-i18next";

import type { VerificationReport } from "../../api/types";
import { useLocale } from "../../hooks/useLocale";
import { ReportStages } from "./ReportStages";
import { reportFacts } from "./reportFacts";

/** What the runner found at the upload, stage by stage; its texts are English (verifikation.md). */
export function ReportView({ report }: { report: VerificationReport }) {
  const { t } = useTranslation();
  const locale = useLocale();
  return (
    <section>
      <h2>{t("bot.report")}</h2>
      <p>{reportFacts(report, t, locale)}</p>
      <ReportStages report={report} />
    </section>
  );
}
