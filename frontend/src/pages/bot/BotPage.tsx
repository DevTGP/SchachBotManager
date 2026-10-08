import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";

import { fetchBot } from "../../api/bots";
import type { BotDetail } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { botLabel } from "../../format/botLabel";
import { useApi } from "../../hooks/useApi";
import { POLL_VERIFY_MS } from "../../hooks/polling";
import { BotFiles } from "./BotFiles";
import { BotStatusSwitch } from "./BotStatusSwitch";
import { BotSummary } from "./BotSummary";
import { ReportView } from "./ReportView";

/** Its verification is still running (E92); only then the page asks again. */
function isVerifying(bot: BotDetail | undefined): boolean {
  return bot?.status === "uploaded" || bot?.status === "analyzing" || bot?.status === "testing";
}

/** One bot; owner and admins also see its files and the verification report. */
export function BotPage() {
  const { t } = useTranslation();
  const { id = "" } = useParams();
  const bot = useApi(
    (signal) => fetchBot(id, signal),
    `bot:${id}`,
    (data) => (isVerifying(data) ? POLL_VERIFY_MS : undefined),
  );
  return (
    <ApiContent state={bot}>
      {(data) => (
        <>
          <h1>{botLabel(data)}</h1>
          <BotSummary bot={data} />
          {isVerifying(data) && (
            <p role="status" className="hint">
              {t("bot.verifying")}
            </p>
          )}
          <BotStatusSwitch bot={data} onChange={bot.reload} />
          <p>
            <Link to={`/matches?bot=${data.id}`}>{t("bot.matches")}</Link>
          </p>
          {data.details && data.details.files.length > 0 && <BotFiles files={data.details.files} />}
          {data.details?.report && <ReportView report={data.details.report} />}
        </>
      )}
    </ApiContent>
  );
}
