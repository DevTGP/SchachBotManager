import { useState } from "react";
import { useTranslation } from "react-i18next";

import type { BotFile } from "../../api/types";
import { useLocale } from "../../hooks/useLocale";
import { FileView } from "./FileView";

/** The files for owner and admins, each one to read (E97); the ZIP is in the bar of actions. */
export function BotFiles({ botId, files }: { botId: string; files: BotFile[] }) {
  const { t } = useTranslation();
  const locale = useLocale();
  const [shown, setShown] = useState<string | undefined>(undefined);
  return (
    <section>
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
    </section>
  );
}
