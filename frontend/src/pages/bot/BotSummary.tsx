import { useTranslation } from "react-i18next";

import type { BotDetail } from "../../api/types";
import { formatDateTime } from "../../format/dateTime";
import { useLocale } from "../../hooks/useLocale";

export function BotSummary({ bot }: { bot: BotDetail }) {
  const { t } = useTranslation();
  const locale = useLocale();
  const rows: [string, string][] = [
    [t("bots.status"), t(`botStatus.${bot.status}`)],
    [t("bots.language"), t(`language.${bot.language}`)],
    [t("bots.kind"), bot.builtin ? t("bots.builtin") : t("bots.uploaded")],
    [t("bots.rating"), String(bot.rating.value)],
    [t("bots.ratedGames"), String(bot.rating.games)],
    [t("bots.created"), formatDateTime(bot.created_at, locale)],
  ];
  const details = bot.details;
  if (details?.owner) rows.push([t("bot.owner"), details.owner]);
  if (details?.entry) rows.push([t("bot.entry"), details.entry]);
  if (details?.sdk_version) rows.push([t("bot.sdk"), details.sdk_version]);
  if (details?.runtime_version) rows.push([t("bot.runtime"), details.runtime_version]);
  if (details?.verified_at) {
    rows.push([t("bot.verifiedAt"), formatDateTime(details.verified_at, locale)]);
  }
  if (details?.rejected_at) {
    rows.push([t("bot.rejectedAt"), formatDateTime(details.rejected_at, locale)]);
  }
  if (details?.rejection) {
    const { stage, reason } = details.rejection;
    rows.push([t("bot.rejection"), `${t(`bot.stage.${stage}`)}: ${reason}`]);
  }
  return (
    <dl className="details">
      {rows.map(([term, value]) => (
        <div key={term}>
          <dt>{term}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
