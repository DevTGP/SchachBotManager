import { useTranslation } from "react-i18next";
import { useParams } from "react-router";

import { startTournament } from "../../api/adminTournaments";
import { fetchTournament, registerTournamentAccount } from "../../api/tournaments";
import { ApiContent } from "../../components/ApiContent";
import { AccountRegistration } from "../../components/registration/AccountRegistration";
import { SelfRegistration } from "../../components/registration/SelfRegistration";
import { StartNow } from "../../components/start/StartNow";
import { useApi } from "../../hooks/useApi";
import { useSession } from "../../session/sessionContext";
import { EditionState } from "./EditionState";
import { NextEdition } from "./NextEdition";
import { TournamentEditions } from "./TournamentEditions";
import { TournamentFacts } from "./TournamentFacts";
import { TournamentRegisterForm } from "./TournamentRegisterForm";
import { TournamentRegistrations } from "./TournamentRegistrations";

/**
 * A tournament with its settings, editions and registered bots and accounts (E180, E182); the
 * latest edition is a link under the name (E188), with "Start now" for an admin while it is planned
 * (E191).
 */
export function TournamentPage() {
  const { t } = useTranslation();
  const { id = "" } = useParams();
  const { user } = useSession();
  const tournament = useApi((signal) => fetchTournament(id, signal), `tournament:${id}`);
  const mayRegister = user?.role === "coder" || user?.role === "admin";
  const isAdmin = user?.role === "admin";
  return (
    <ApiContent state={tournament}>
      {(data) => {
        const participants = data.registrations.map((entry) => entry.bot);
        return (
          <>
            <h1>{data.name}</h1>
            {data.edition && (
              <p>
                {t("tournaments.currentEdition")} <EditionState edition={data.edition} />
              </p>
            )}
            <NextEdition tournament={data} />
            <StartNow
              competition={data}
              start={() => startTournament(data.id)}
              onStarted={tournament.reload}
            />
            <TournamentFacts
              settings={data}
              discipline={data.discipline_name}
              tiebreakDiscipline={data.tiebreak_discipline_name}
              recurrence={data.recurrence}
            />
            {data.editions.length > 0 && <TournamentEditions editions={data.editions} />}
            <TournamentRegistrations
              tournamentId={data.id}
              registrations={data.registrations}
              onChange={tournament.reload}
            />
            {!data.archived && (
              <SelfRegistration
                registered={participants}
                readyHours={data.ready_hours}
                register={(userId) => registerTournamentAccount(data.id, userId)}
                onChange={tournament.reload}
              />
            )}
            {mayRegister && !data.archived && (
              <TournamentRegisterForm
                key={data.id}
                tournament={data}
                onChange={tournament.reload}
              />
            )}
            {isAdmin && !data.archived && (
              <AccountRegistration
                registered={participants}
                register={(userId) => registerTournamentAccount(data.id, userId)}
                onChange={tournament.reload}
              />
            )}
          </>
        );
      }}
    </ApiContent>
  );
}
