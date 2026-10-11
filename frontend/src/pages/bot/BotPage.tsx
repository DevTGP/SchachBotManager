import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router";

import { fetchBot } from "../../api/bots";
import type { BotDetail } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { useApi } from "../../hooks/useApi";
import { POLL_VERIFY_MS } from "../../hooks/polling";
import { useSession } from "../../session/sessionContext";
import { BotActions } from "./BotActions";
import { BotAdmin } from "./BotAdmin";
import { BotDescription } from "./BotDescription";
import { BotFiles } from "./BotFiles";
import { BotHeader } from "./BotHeader";
import { BotLeagues } from "./BotLeagues";
import { BotOpponents } from "./BotOpponents";
import { BotRatingChart } from "./BotRatingChart";
import { BotRechecks } from "./BotRechecks";
import { BotResults } from "./BotResults";
import { BotSeasons } from "./BotSeasons";
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
  const { id = "" } = useParams();
  const bot = useApi(
    (signal) => fetchBot(id, signal),
    `bot:${id}`,
    (data) => (isWaiting(data) ? POLL_VERIFY_MS : undefined),
  );
  return (
    <ApiContent state={bot}>
      {(data) => <BotView key={data.id} bot={data} onChange={bot.reload} />}
    </ApiContent>
  );
}

/**
 * Heading with the facts, the bar of actions, then one section each; the admin's actions come
 * last under their own heading (G6, G14).
 */
function BotView({ bot, onChange }: { bot: BotDetail; onChange: () => void }) {
  const { t } = useTranslation();
  const { user } = useSession();
  const [editing, setEditing] = useState(false);
  const isOwner = !!user && !bot.builtin && bot.details?.owner === user.username;
  const viewer = { isOwner, isAdmin: user?.role === "admin" };
  const play =
    bot.status === "verified" ? (other: string) => playLink(bot.id, other, viewer) : undefined;
  return (
    <>
      <BotHeader bot={bot} />
      <BotDescription
        bot={bot}
        editing={editing}
        onDone={() => setEditing(false)}
        onChange={onChange}
      />
      <BotActions
        bot={bot}
        isOwner={isOwner}
        onEdit={editing ? undefined : () => setEditing(true)}
        onChange={onChange}
      />
      {isVerifying(bot) && (
        <p role="status" className="hint">
          {t("bot.verifying")}
        </p>
      )}
      {bot.details?.recheck_pending && (
        <p role="status" className="hint">
          {t("bot.recheckPending")}
        </p>
      )}
      {bot.status === "retired" && <p className="hint">{t("bot.retiredHint")}</p>}
      <section>
        <h2>{t("bot.details")}</h2>
        <BotSummary bot={bot} />
      </section>
      <BotVersions versions={bot.versions} current={bot.id} play={play} />
      {!bot.builtin && <BotLeagues bot={bot} mayManage={isOwner || viewer.isAdmin} />}
      {!bot.builtin && <BotSeasons botId={bot.id} />}
      <BotRatingChart botId={bot.id} />
      <BotResults botId={bot.id} />
      <BotOpponents botId={bot.id} />
      {bot.details && bot.details.files.length > 0 && (
        <BotFiles botId={bot.id} files={bot.details.files} />
      )}
      {bot.details?.report && <ReportView report={bot.details.report} />}
      {bot.details && <BotRechecks rechecks={bot.details.rechecks} />}
      <BotAdmin bot={bot} onChange={onChange} />
    </>
  );
}
