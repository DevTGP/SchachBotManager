import { useState } from "react";
import { useTranslation } from "react-i18next";

import { botSourceUrl } from "../../api/bots";
import type { BotFile } from "../../api/types";
import { useLocale } from "../../hooks/useLocale";
import { FileView } from "./FileView";

/** The files for owner and admins: each one to read, all of them as a ZIP file (E97). */
export function BotFiles({ botId, files }: { botId: string; files: BotFile[] }) {
  const { t } = useTranslation();
  const locale = useLocale();
  const [shown, setShown] = useState<string | undefined>(undefined);
  return (
    <>
      <h2>{t("bot.files")}</h2>
      <p>
        <a className="button" href={botSourceUrl(botId)} download>
          {t("bot.downloadZip")}
        </a>
      </p>
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
                <td>
                  <button
                    type="button"
                    className="info-text"
                    aria-pressed={shown === file.path}
                    onClick={() => setShown(shown === file.path ? undefined : file.path)}
                  >
                    {file.path}
                  </button>
                </td>
                <td>{t(`upload.${file.kind}`)}</td>
                <td>{t("bot.bytes", { size: file.size.toLocaleString(locale) })}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {shown !== undefined && <FileView key={shown} botId={botId} path={shown} />}
    </>
  );
}
