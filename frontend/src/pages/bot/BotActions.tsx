import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { botSourceUrl } from "../../api/bots";
import type { BotDetail } from "../../api/types";
import { BotOwnerSwitch } from "./BotOwnerSwitch";

/**
 * One bar of actions under the heading: links lead to other pages or files, buttons change the
 * bot (U10). Its owner edits the description and retires the bot here.
 */
export function BotActions({
  bot,
  isOwner,
  onEdit,
  onChange,
}: {
  bot: BotDetail;
  isOwner: boolean;
  onEdit?: () => void;
  onChange: () => void;
}) {
  const { t } = useTranslation();
  const hasFiles = !!bot.details && bot.details.files.length > 0;
  return (
    <div className="action-bar">
      <Link to={`/matches?bot=${bot.id}`}>{t("bot.matches")}</Link>
      {hasFiles && (
        <a href={botSourceUrl(bot.id)} download>
          {t("bot.downloadZip")}
        </a>
      )}
      {isOwner && onEdit && (
        <button type="button" onClick={onEdit}>
          {t("bot.editDescription")}
        </button>
      )}
      {isOwner && <BotOwnerSwitch bot={bot} onChange={onChange} />}
    </div>
  );
}
