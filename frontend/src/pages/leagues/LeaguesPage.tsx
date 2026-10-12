import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { fetchLeagues } from "../../api/leagues";
import { ApiContent } from "../../components/ApiContent";
import { TableShell } from "../../components/TableShell";
import { useApi } from "../../hooks/useApi";
import { SeasonState } from "./SeasonState";

/** Every league by name with its latest season (E137). */
export function LeaguesPage() {
  const { t } = useTranslation();
  const leagues = useApi(fetchLeagues, "leagues");
  return (
    <>
      <h1>{t("leagues.title")}</h1>
      <p className="muted">{t("leagues.intro")}</p>
      <ApiContent state={leagues}>
        {(items) => (
          <TableShell rows={items.length} empty={t("leagues.empty")}>
            <thead>
              <tr>
                <th>{t("leagues.name")}</th>
                <th>{t("leagues.discipline")}</th>
                <th className="number">{t("leagues.tiers")}</th>
                <th className="number">{t("leagues.registered")}</th>
                <th>{t("leagues.season")}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((league) => (
                <tr key={league.id}>
                  <td>
                    <Link to={`/leagues/${league.id}`}>{league.name}</Link>
                    {league.archived && ` (${t("leagues.archived")})`}
                  </td>
                  <td>{league.discipline_name}</td>
                  <td className="number">{league.tiers}</td>
                  <td className="number">{league.registered}</td>
                  <td>
                    <SeasonState season={league.season} />
                  </td>
                </tr>
              ))}
            </tbody>
          </TableShell>
        )}
      </ApiContent>
    </>
  );
}
