import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { fetchTournaments } from "../../api/tournaments";
import { ApiContent } from "../../components/ApiContent";
import { TableShell } from "../../components/TableShell";
import { useApi } from "../../hooks/useApi";
import { EditionState } from "./EditionState";

/** Every tournament by name with its latest edition (E180). */
export function TournamentsPage() {
  const { t } = useTranslation();
  const tournaments = useApi(fetchTournaments, "tournaments");
  return (
    <>
      <h1>{t("tournaments.title")}</h1>
      <p className="muted">{t("tournaments.intro")}</p>
      <ApiContent state={tournaments}>
        {(items) => (
          <TableShell rows={items.length} empty={t("tournaments.empty")}>
            <thead>
              <tr>
                <th>{t("tournaments.name")}</th>
                <th>{t("tournaments.format")}</th>
                <th>{t("tournaments.discipline")}</th>
                <th className="number">{t("tournaments.registered")}</th>
                <th>{t("tournaments.edition")}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((tournament) => (
                <tr key={tournament.id}>
                  <td>
                    <Link to={`/tournaments/${tournament.id}`}>{tournament.name}</Link>
                    {tournament.archived && ` (${t("tournaments.archived")})`}
                  </td>
                  <td>{t(`tournamentFormat.${tournament.format}`)}</td>
                  <td>{tournament.discipline_name}</td>
                  <td className="number">{tournament.registered}</td>
                  <td>
                    <EditionState edition={tournament.edition} />
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
