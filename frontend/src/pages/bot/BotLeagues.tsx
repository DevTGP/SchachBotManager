import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import {
  deregisterParticipant,
  fetchBotLeagues,
  fetchLeagues,
  registerBot,
} from "../../api/leagues";
import type { BotDetail, League, LeagueRegistration } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { FormError } from "../../components/FormError";
import { useApi } from "../../hooks/useApi";
import { useSubmit } from "../../hooks/useSubmit";

/**
 * The leagues of a bot; its owner and admins register it in a league in use or take it out,
 * which loses its waiting games of a running season by forfeit (E136).
 */
export function BotLeagues({ bot, mayManage }: { bot: BotDetail; mayManage: boolean }) {
  const { t } = useTranslation();
  const entries = useApi((signal) => fetchBotLeagues(bot.id, signal), `bot-leagues:${bot.id}`);
  const { pending, error, submit } = useSubmit();

  function deregister(leagueId: string) {
    void submit(async () => {
      await deregisterParticipant(leagueId, bot.id);
      entries.reload();
    });
  }

  return (
    <section>
      <h2>{t("leagues.title")}</h2>
      <FormError error={error} />
      <ApiContent state={entries}>
        {(items) => (
          <>
            {items.length === 0 ? (
              <p className="muted">{t("bot.noLeagues")}</p>
            ) : (
              <ul>
                {items.map((entry) => (
                  <li key={entry.league_id}>
                    <Link to={`/leagues/${entry.league_id}`}>{entry.league_name}</Link>
                    {" – "}
                    {entry.tier === null
                      ? t("leagues.nextSeason")
                      : t("seasons.tier", { tier: entry.tier })}
                    {mayManage && (
                      <>
                        {" "}
                        <button
                          type="button"
                          disabled={pending}
                          onClick={() => deregister(entry.league_id)}
                        >
                          {t("leagues.deregister")}
                        </button>
                      </>
                    )}
                  </li>
                ))}
              </ul>
            )}
            {mayManage && bot.status === "verified" && (
              <LeagueChoice botId={bot.id} entries={items} onChange={entries.reload} />
            )}
          </>
        )}
      </ApiContent>
    </section>
  );
}

function LeagueChoice({
  botId,
  entries,
  onChange,
}: {
  botId: string;
  entries: LeagueRegistration[];
  onChange: () => void;
}) {
  const { t } = useTranslation();
  const leagues = useApi(fetchLeagues, "leagues");
  const { pending, error, submit } = useSubmit();
  const [chosen, setChosen] = useState("");
  const taken = new Set(entries.map((entry) => entry.league_id));
  const open = (leagues.data ?? []).filter(
    (league: League) => !league.archived && !taken.has(league.id),
  );
  if (open.length === 0) return null;
  const leagueId = open.some((league) => league.id === chosen) ? chosen : open[0]!.id;

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void submit(async () => {
      await registerBot(leagueId, botId);
      onChange();
    });
  }

  return (
    <form className="form" onSubmit={onSubmit}>
      <label>
        {t("leagues.league")}
        <select value={leagueId} onChange={(event) => setChosen(event.target.value)}>
          {open.map((league) => (
            <option key={league.id} value={league.id}>
              {league.name}
            </option>
          ))}
        </select>
      </label>
      <p className="hint">{t("leagues.registerHint")}</p>
      <FormError error={error} />
      <div className="inline-actions">
        <button type="submit" className="primary" disabled={pending}>
          {t("leagues.registerButton")}
        </button>
      </div>
    </form>
  );
}
