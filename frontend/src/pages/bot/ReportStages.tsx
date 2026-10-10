import { useTranslation } from "react-i18next";

import type { VerificationReport } from "../../api/types";
import { FindingsTable } from "./FindingsTable";
import { TestGamesTable } from "./TestGamesTable";

/** The stages of a report with their findings and test games. */
export function ReportStages({ report }: { report: VerificationReport }) {
  const { t } = useTranslation();
  return report.stages.map((stage) => (
    <section key={stage.stage}>
      <h3>
        {t(`bot.stage.${stage.stage}`)}:{" "}
        {stage.status === "passed" ? t("bot.passed") : t("bot.failed")}{" "}
        <span className="muted">
          ({t("bot.duration", { seconds: (stage.duration_ms / 1000).toFixed(1) })})
        </span>
      </h3>
      {stage.problem && <p className="info-text">{stage.problem}</p>}
      {stage.findings && stage.findings.length > 0 && <FindingsTable findings={stage.findings} />}
      {stage.truncated && <p className="hint">{t("bot.truncated")}</p>}
      {stage.tests && stage.tests.length > 0 && <TestGamesTable tests={stage.tests} />}
    </section>
  ));
}
