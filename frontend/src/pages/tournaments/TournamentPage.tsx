import { useParams } from "react-router";

import { fetchTournament } from "../../api/tournaments";
import { ApiContent } from "../../components/ApiContent";
import { useApi } from "../../hooks/useApi";
import { useSession } from "../../session/sessionContext";
import { NextEdition } from "./NextEdition";
import { TournamentEditions } from "./TournamentEditions";
import { TournamentFacts } from "./TournamentFacts";
import { TournamentRegisterForm } from "./TournamentRegisterForm";
import { TournamentRegistrations } from "./TournamentRegistrations";

/** A tournament with its settings, editions and registered bots (E180). */
export function TournamentPage() {
  const { id = "" } = useParams();
  const { user } = useSession();
  const tournament = useApi((signal) => fetchTournament(id, signal), `tournament:${id}`);
  const mayRegister = user?.role === "coder" || user?.role === "admin";
  return (
    <ApiContent state={tournament}>
      {(data) => (
        <>
          <h1>{data.name}</h1>
          <NextEdition tournament={data} />
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
          {mayRegister && !data.archived && (
            <TournamentRegisterForm key={data.id} tournament={data} onChange={tournament.reload} />
          )}
        </>
      )}
    </ApiContent>
  );
}
