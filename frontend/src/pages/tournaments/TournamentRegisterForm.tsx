import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { registerTournamentBot } from "../../api/tournaments";
import type { TournamentDetail } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { BotPicker } from "../../components/BotPicker";
import { FormError } from "../../components/FormError";
import { useRegistrableBots } from "../../hooks/useRegistrableBots";
import { useSubmit } from "../../hooks/useSubmit";

/**
 * Coders register one of their verified bots that is not in the tournament yet (E179), admins
 * any verified bot (E181).
 */
export function TournamentRegisterForm({
  tournament,
  onChange,
}: {
  tournament: TournamentDetail;
  onChange: () => void;
}) {
  const { t } = useTranslation();
  const candidates = useRegistrableBots();
  const { pending, error, submit } = useSubmit();
  const [chosen, setChosen] = useState("");
  const registered = new Set(tournament.registrations.map((entry) => entry.bot.bot_id));

  return (
    <section>
      <h2>{t("leagues.register")}</h2>
      <ApiContent state={candidates}>
        {(bots) => {
          const free = bots.filter((bot) => bot.status === "verified" && !registered.has(bot.id));
          if (free.length === 0) return <p className="muted">{t("tournaments.noFreeBots")}</p>;
          const botId = free.some((bot) => bot.id === chosen) ? chosen : free[0]!.id;
          function onSubmit(event: FormEvent) {
            event.preventDefault();
            void submit(async () => {
              await registerTournamentBot(tournament.id, botId);
              onChange();
            });
          }
          return (
            <form className="form" onSubmit={onSubmit}>
              <BotPicker label={t("leagues.bot")} bots={free} value={botId} onChange={setChosen} />
              <p className="hint">{t("tournaments.registerHint")}</p>
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
