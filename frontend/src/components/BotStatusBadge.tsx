import { useTranslation } from "react-i18next";

import type { BotStatus } from "../api/types";

const TONE: Partial<Record<BotStatus, string>> = {
  verified: "ok",
  rejected: "bad",
  disabled: "bad",
};

/** The state of a bot as a badge: verified in the accent colour, rejected and blocked in red. */
export function BotStatusBadge({ status }: { status: BotStatus }) {
  const { t } = useTranslation();
  const tone = TONE[status];
  return <span className={tone ? `badge ${tone}` : "badge"}>{t(`botStatus.${status}`)}</span>;
}
