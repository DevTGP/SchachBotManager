import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import {
  deregisterTournamentBot,
  fetchBotTournaments,
  fetchTournaments,
  registerTournamentBot,
} from "../../api/tournaments";
import type { BotDetail, Tournament, TournamentRegistration } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { FormError } from "../../components/FormError";
import { useApi } from "../../hooks/useApi";
import { useSubmit } from "../../hooks/useSubmit";

/**
 * The tournaments of a bot; its owner and admins register it in a tournament in use or take it
 * out, which loses its waiting games of a running edition by forfeit (E179).
 */
export function BotTournaments({ bot, mayManage }: { bot: BotDetail; mayManage: boolean }) {
  const { t } = useTranslation();
  const entries = useApi(
    (signal) => fetchBotTournaments(bot.id, signal),
    `bot-tournaments:${bot.id}`,
  );
  const { pending, error, submit } = useSubmit();

  function deregister(tournamentId: string) {
    void submit(async () => {
      await deregisterTournamentBot(tournamentId, bot.id);
      entries.reload();
    });
  }

  return (
    <section>
      <h2>{t("tournaments.title")}</h2>
      <FormError error={error} />
      <ApiContent state={entries}>
        {(items) => (
          <>
            {items.length === 0 ? (
              <p className="muted">{t("bot.noTournaments")}</p>
            ) : (
              <ul>
                {items.map((entry) => (
                  <li key={entry.tournament_id}>
                    <Link to={`/tournaments/${entry.tournament_id}`}>{entry.tournament_name}</Link>
                    {" – "}
                    {entry.playing ? t("tournaments.inEdition") : t("tournaments.nextEdition")}
                    {mayManage && (
                      <>
                        {" "}
                        <button
                          type="button"
                          disabled={pending}
                          onClick={() => deregister(entry.tournament_id)}
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
              <TournamentChoice botId={bot.id} entries={items} onChange={entries.reload} />
            )}
          </>
        )}
      </ApiContent>
    </section>
  );
}

function TournamentChoice({
  botId,
  entries,
  onChange,
}: {
  botId: string;
  entries: TournamentRegistration[];
  onChange: () => void;
}) {
  const { t } = useTranslation();
  const tournaments = useApi(fetchTournaments, "tournaments");
  const { pending, error, submit } = useSubmit();
  const [chosen, setChosen] = useState("");
  const taken = new Set(entries.map((entry) => entry.tournament_id));
  const open = (tournaments.data ?? []).filter(
    (tournament: Tournament) => !tournament.archived && !taken.has(tournament.id),
  );
  if (open.length === 0) return null;
  const tournamentId = open.some((tournament) => tournament.id === chosen) ? chosen : open[0]!.id;

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void submit(async () => {
      await registerTournamentBot(tournamentId, botId);
      onChange();
    });
  }

  return (
    <form className="form" onSubmit={onSubmit}>
      <label>
        {t("tournaments.tournament")}
        <select value={tournamentId} onChange={(event) => setChosen(event.target.value)}>
          {open.map((tournament) => (
            <option key={tournament.id} value={tournament.id}>
              {tournament.name}
            </option>
          ))}
        </select>
      </label>
      <p className="hint">{t("tournaments.registerHint")}</p>
      <FormError error={error} />
      <div className="inline-actions">
        <button type="submit" className="primary" disabled={pending}>
          {t("leagues.registerButton")}
        </button>
      </div>
    </form>
  );
}
