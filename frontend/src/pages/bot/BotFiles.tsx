import { useTranslation } from "react-i18next";

import type { BotFile } from "../../api/types";
import { useLocale } from "../../hooks/useLocale";

export function BotFiles({ files }: { files: BotFile[] }) {
  const { t } = useTranslation();
  const locale = useLocale();
  return (
    <>
      <h2>{t("bot.files")}</h2>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>{t("bot.path")}</th>
              <th>{t("bot.kind")}</th>
              <th>{t("bot.size")}</th>
            </tr>
          </thead>
          <tbody>
            {files.map((file) => (
              <tr key={file.path}>
                <td className="info-text">{file.path}</td>
                <td>{t(`upload.${file.kind}`)}</td>
                <td>{t("bot.bytes", { size: file.size.toLocaleString(locale) })}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
