import { useParams } from "react-router";

import { fetchLeague } from "../../api/leagues";
import { ApiContent } from "../../components/ApiContent";
import { useApi } from "../../hooks/useApi";
import { useSession } from "../../session/sessionContext";
import { LeagueFacts } from "./LeagueFacts";
import { LeagueRegisterForm } from "./LeagueRegisterForm";
import { LeagueRegistrations } from "./LeagueRegistrations";
import { LeagueSeasons } from "./LeagueSeasons";
import { NextSeason } from "./NextSeason";

/** A league with its settings, seasons and registered bots (E137). */
export function LeaguePage() {
  const { id = "" } = useParams();
  const { user } = useSession();
  const league = useApi((signal) => fetchLeague(id, signal), `league:${id}`);
  const mayRegister = user?.role === "coder" || user?.role === "admin";
  return (
    <ApiContent state={league}>
      {(data) => (
        <>
          <h1>{data.name}</h1>
          <NextSeason league={data} />
          <LeagueFacts
            settings={data}
            discipline={data.discipline_name}
            recurrence={data.recurrence}
          />
          {data.seasons.length > 0 && <LeagueSeasons seasons={data.seasons} />}
          <LeagueRegistrations
            leagueId={data.id}
            registrations={data.registrations}
            onChange={league.reload}
          />
          {mayRegister && !data.archived && (
            <LeagueRegisterForm key={data.id} league={data} onChange={league.reload} />
          )}
        </>
      )}
    </ApiContent>
  );
}
