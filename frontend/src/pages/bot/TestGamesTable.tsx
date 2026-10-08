import { useTranslation } from "react-i18next";

import type { TestGame } from "../../api/types";
import { formatResult } from "../../format/result";

/** The minimum tests against Random, up to the first that failed. */
export function TestGamesTable({ tests }: { tests: TestGame[] }) {
  const { t } = useTranslation();
  return (
    <div className="table-scroll">
      <table aria-label={t("bot.stage.tests")}>
        <thead>
          <tr>
            <th>{t("bot.test")}</th>
            <th>{t("bot.color")}</th>
            <th>{t("bot.result")}</th>
            <th>{t("bot.plies")}</th>
            <th>{t("bot.outcome")}</th>
          </tr>
        </thead>
        <tbody>
          {tests.map((test) => (
            <tr key={test.name}>
              <td>{test.name}</td>
              <td>{test.color === "white" ? t("viewer.white") : t("viewer.black")}</td>
              <td>
                {formatResult(test.result)} ({t(`termination.${test.termination}`)})
              </td>
              <td>{test.plies}</td>
              <td>{test.passed ? t("bot.passed") : (test.problem ?? t("bot.failed"))}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
