import { useTranslation } from "react-i18next";

import { botFileUrl, fetchBotFile } from "../../api/bots";
import { ApiContent } from "../../components/ApiContent";
import { useApi } from "../../hooks/useApi";

/** UTF-8 text, or undefined for anything else such as a binary data file. */
function decodeText(bytes: ArrayBuffer): string | undefined {
  try {
    return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    return undefined;
  }
}

/** One file of the bot as plain text; React escapes it, so nothing in it runs (E97). */
export function FileView({ botId, path }: { botId: string; path: string }) {
  const { t } = useTranslation();
  const file = useApi((signal) => fetchBotFile(botId, path, signal), `file:${botId}:${path}`);
  return (
    <section aria-label={path}>
      <h3 className="info-text">{path}</h3>
      <ApiContent state={file}>
        {(bytes) => {
          const text = decodeText(bytes);
          return text === undefined ? (
            <p className="muted">{t("bot.binary")}</p>
          ) : (
            <pre className="source-view">{text}</pre>
          );
        }}
      </ApiContent>
      <p>
        <a href={botFileUrl(botId, path)} download>
          {t("bot.downloadFile")}
        </a>
      </p>
    </section>
  );
}
