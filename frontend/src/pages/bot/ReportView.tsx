import { useTranslation } from "react-i18next";

import type { VerificationReport } from "../../api/types";
import { formatDateTime } from "../../format/dateTime";
import { useLocale } from "../../hooks/useLocale";
import { FindingsTable } from "./FindingsTable";
import { TestGamesTable } from "./TestGamesTable";

/** What the runner found, stage by stage; its texts are English (verifikation.md). */
export function ReportView({ report }: { report: VerificationReport }) {
  const { t } = useTranslation();
  const locale = useLocale();
  const outcome = (status: "passed" | "failed") =>
    status === "passed" ? t("bot.passed") : t("bot.failed");
  const facts = [outcome(report.result), formatDateTime(report.finished_at, locale)];
  if (report.ruleset) facts.push(`${t("bot.ruleset")} ${report.ruleset}`);
  return (
    <section>
      <h2>{t("bot.report")}</h2>
      <p>{facts.join(" · ")}</p>
      {report.stages.map((stage) => (
        <section key={stage.stage}>
          <h3>
            {t(`bot.stage.${stage.stage}`)}: {outcome(stage.status)}{" "}
            <span className="muted">
              ({t("bot.duration", { seconds: (stage.duration_ms / 1000).toFixed(1) })})
            </span>
          </h3>
          {stage.problem && <p className="info-text">{stage.problem}</p>}
          {stage.findings && stage.findings.length > 0 && (
            <FindingsTable findings={stage.findings} />
          )}
          {stage.truncated && <p className="hint">{t("bot.truncated")}</p>}
          {stage.tests && stage.tests.length > 0 && <TestGamesTable tests={stage.tests} />}
        </section>
      ))}
    </section>
  );
}
