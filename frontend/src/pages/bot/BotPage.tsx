import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";

import { fetchBot } from "../../api/bots";
import type { BotDetail } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { botLabel } from "../../format/botLabel";
import { useApi } from "../../hooks/useApi";
import { POLL_VERIFY_MS } from "../../hooks/polling";
import { useSession } from "../../session/sessionContext";
import { BotChecks } from "./BotChecks";
import { BotDelete } from "./BotDelete";
import { BotDescription } from "./BotDescription";
import { BotFiles } from "./BotFiles";
import { BotOpponents } from "./BotOpponents";
import { BotOwnerSwitch } from "./BotOwnerSwitch";
import { BotRechecks } from "./BotRechecks";
import { BotStatusSwitch } from "./BotStatusSwitch";
import { BotSummary } from "./BotSummary";
import { BotVersions } from "./BotVersions";
import { playLink } from "./playLink";
import { ReportView } from "./ReportView";

/** Its verification is still running (E92). */
function isVerifying(bot: BotDetail | undefined): boolean {
  return bot?.status === "uploaded" || bot?.status === "analyzing" || bot?.status === "testing";
}

/** Only while a verification or a recheck (E153) is pending the page asks again. */
function isWaiting(bot: BotDetail | undefined): boolean {
  return isVerifying(bot) || !!bot?.details?.recheck_pending;
}

/** One bot with its versions; owner and admins also see its files, the report and the rechecks. */
export function BotPage() {
  const { t } = useTranslation();
  const { id = "" } = useParams();
  const { user } = useSession();
  const bot = useApi(
    (signal) => fetchBot(id, signal),
    `bot:${id}`,
    (data) => (isWaiting(data) ? POLL_VERIFY_MS : undefined),
  );
  return (
    <ApiContent state={bot}>
      {(data) => {
        const isOwner = !!user && !data.builtin && data.details?.owner === user.username;
        const viewer = { isOwner, isAdmin: user?.role === "admin" };
        const play =
          data.status === "verified"
            ? (other: string) => playLink(data.id, other, viewer)
            : undefined;
        return (
          <>
            <h1>{botLabel(data)}</h1>
            <BotDescription key={data.id} bot={data} isOwner={isOwner} onChange={bot.reload} />
            <BotSummary bot={data} />
            {isVerifying(data) && (
              <p role="status" className="hint">
                {t("bot.verifying")}
              </p>
            )}
            {data.details?.recheck_pending && (
              <p role="status" className="hint">
                {t("bot.recheckPending")}
              </p>
            )}
            {isOwner && <BotOwnerSwitch bot={data} onChange={bot.reload} />}
            <BotStatusSwitch bot={data} onChange={bot.reload} />
            <BotChecks key={`checks-${data.id}`} bot={data} onChange={bot.reload} />
            <BotDelete key={data.id} bot={data} />
            <p>
              <Link to={`/matches?bot=${data.id}`}>{t("bot.matches")}</Link>
            </p>
            <BotVersions versions={data.versions} current={data.id} play={play} />
            <BotOpponents key={`opponents-${data.id}`} botId={data.id} />
            {data.details && data.details.files.length > 0 && (
              <BotFiles key={data.id} botId={data.id} files={data.details.files} />
            )}
            {data.details?.report && <ReportView report={data.details.report} />}
            {data.details && <BotRechecks rechecks={data.details.rechecks} />}
          </>
        );
      }}
    </ApiContent>
  );
}
