import { useTranslation } from "react-i18next";
import { useParams } from "react-router";

import { fetchLeague, registerAccount } from "../../api/leagues";
import { ApiContent } from "../../components/ApiContent";
import { AccountRegistration } from "../../components/registration/AccountRegistration";
import { SelfRegistration } from "../../components/registration/SelfRegistration";
import { useApi } from "../../hooks/useApi";
import { useSession } from "../../session/sessionContext";
import { LeagueFacts } from "./LeagueFacts";
import { LeagueRegisterForm } from "./LeagueRegisterForm";
import { LeagueRegistrations } from "./LeagueRegistrations";
import { LeagueSeasons } from "./LeagueSeasons";
import { NextSeason } from "./NextSeason";
import { SeasonState } from "./SeasonState";

/**
 * A league with its settings, seasons and registered bots and accounts (E137, E182); the latest
 * season is a link under the name (E188).
 */
export function LeaguePage() {
  const { t } = useTranslation();
  const { id = "" } = useParams();
  const { user } = useSession();
  const league = useApi((signal) => fetchLeague(id, signal), `league:${id}`);
  const mayRegister = user?.role === "coder" || user?.role === "admin";
  const isAdmin = user?.role === "admin";
  return (
    <ApiContent state={league}>
      {(data) => {
        const participants = data.registrations.map((entry) => entry.bot);
        return (
          <>
            <h1>{data.name}</h1>
            {data.season && (
              <p>
                {t("leagues.currentSeason")} <SeasonState season={data.season} />
              </p>
            )}
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
            {!data.archived && (
              <SelfRegistration
                registered={participants}
                readyHours={data.ready_hours}
                register={(userId) => registerAccount(data.id, userId)}
                onChange={league.reload}
              />
            )}
            {mayRegister && !data.archived && (
              <LeagueRegisterForm key={data.id} league={data} onChange={league.reload} />
            )}
            {isAdmin && !data.archived && (
              <AccountRegistration
                registered={participants}
                register={(userId) => registerAccount(data.id, userId)}
                onChange={league.reload}
              />
            )}
          </>
        );
      }}
    </ApiContent>
  );
}
