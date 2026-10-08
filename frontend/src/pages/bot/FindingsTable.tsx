import { useTranslation } from "react-i18next";

import type { Finding } from "../../api/types";

export function FindingsTable({ findings }: { findings: Finding[] }) {
  const { t } = useTranslation();
  return (
    <div className="table-scroll">
      <table aria-label={t("bot.findings")}>
        <thead>
          <tr>
            <th>{t("bot.place")}</th>
            <th>{t("bot.rule")}</th>
            <th>{t("bot.message")}</th>
          </tr>
        </thead>
        <tbody>
          {findings.map((finding, index) => (
            <tr key={index}>
              <td className="info-text">
                {finding.line === null ? finding.file : `${finding.file}:${finding.line}`}
              </td>
              <td>{finding.rule}</td>
              <td>{finding.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
