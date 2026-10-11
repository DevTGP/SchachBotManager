import { useTranslation } from "react-i18next";

import type { BotDetail } from "../../api/types";
import { useSession } from "../../session/sessionContext";
import { BotChecks } from "./BotChecks";
import { BotDelete } from "./BotDelete";
import { BotStatusSwitch } from "./BotStatusSwitch";

/** The admin's actions on a bot in one place at the end of the page (G14). */
export function BotAdmin({ bot, onChange }: { bot: BotDetail; onChange: () => void }) {
  const { t } = useTranslation();
  const { user } = useSession();
  if (user?.role !== "admin") return null;
  return (
    <section className="admin-zone">
      <h2>{t("bot.admin")}</h2>
      <BotStatusSwitch bot={bot} onChange={onChange} />
      <BotChecks key={`checks-${bot.id}`} bot={bot} onChange={onChange} />
      <BotDelete key={bot.id} bot={bot} />
    </section>
  );
}
