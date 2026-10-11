import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { fetchOwnBots } from "../../api/bots";
import { registerBot } from "../../api/leagues";
import type { LeagueDetail } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { BotPicker } from "../../components/BotPicker";
import { FormError } from "../../components/FormError";
import { useApi } from "../../hooks/useApi";
import { useSubmit } from "../../hooks/useSubmit";

/** Coders register one of their verified bots that is not in the league yet (E136). */
export function LeagueRegisterForm({
  league,
  onChange,
}: {
  league: LeagueDetail;
  onChange: () => void;
}) {
  const { t } = useTranslation();
  const own = useApi(fetchOwnBots, "account/bots");
  const { pending, error, submit } = useSubmit();
  const [chosen, setChosen] = useState("");
  const registered = new Set(league.registrations.map((entry) => entry.bot.bot_id));

  return (
    <section>
      <h2>{t("leagues.register")}</h2>
      <ApiContent state={own}>
        {(bots) => {
          const free = bots.filter((bot) => bot.status === "verified" && !registered.has(bot.id));
          if (free.length === 0) return <p className="muted">{t("leagues.noFreeBots")}</p>;
          const botId = free.some((bot) => bot.id === chosen) ? chosen : free[0]!.id;
          function onSubmit(event: FormEvent) {
            event.preventDefault();
            void submit(async () => {
              await registerBot(league.id, botId);
              onChange();
            });
          }
          return (
            <form className="form" onSubmit={onSubmit}>
              <BotPicker label={t("leagues.bot")} bots={free} value={botId} onChange={setChosen} />
              <p className="hint">{t("leagues.registerHint")}</p>
              <FormError error={error} />
              <div className="inline-actions">
                <button type="submit" className="primary" disabled={pending}>
                  {t("leagues.registerButton")}
                </button>
              </div>
            </form>
          );
        }}
      </ApiContent>
    </section>
  );
}
