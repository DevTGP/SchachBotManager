import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { createTournament, startTournament, updateTournament } from "../../api/adminTournaments";
import { fetchDisciplines } from "../../api/endpoints";
import { fetchTournaments } from "../../api/tournaments";
import type { Tournament, TournamentRequest, TournamentUpdate } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { FormError } from "../../components/FormError";
import { TableShell } from "../../components/TableShell";
import { EditionState } from "../tournaments/EditionState";
import { useApi } from "../../hooks/useApi";
import { useSubmit } from "../../hooks/useSubmit";
import { startable } from "../../components/start/startable";
import { TournamentEditor } from "./TournamentEditor";
import { DEFAULT_TOURNAMENT_FORM, tournamentForm } from "./tournamentForm";

/** Tournaments: create, change, start the planned edition, archive; never deleted (E172, E171). */
export function AdminTournamentsPage() {
  const { t } = useTranslation();
  const tournaments = useApi(fetchTournaments, "tournaments");
  const disciplines = useApi(fetchDisciplines, "disciplines");
  const { pending, error, submit } = useSubmit();
  const [editing, setEditing] = useState<Tournament | undefined>();
  // A new key empties the form for the next tournament after a create.
  const [created, setCreated] = useState(0);

  async function create(request: TournamentRequest) {
    await createTournament(request);
    setCreated((count) => count + 1);
    tournaments.reload();
  }

  async function save(request: TournamentRequest) {
    if (!editing) return;
    const change: TournamentUpdate = { ...request };
    // The format is fixed once the tournament exists (E172).
    delete (change as Partial<TournamentRequest>).format;
    // Archived disciplines may stay, but not be set again.
    if (change.discipline_id === editing.discipline_id) delete change.discipline_id;
    if (change.tiebreak_discipline_id === editing.tiebreak_discipline_id) {
      delete change.tiebreak_discipline_id;
    }
    await updateTournament(editing.id, change);
    setEditing(undefined);
    tournaments.reload();
  }

  function act(action: () => Promise<unknown>) {
    void submit(async () => {
      await action();
      tournaments.reload();
    });
  }

  return (
    <section>
      <ApiContent state={disciplines}>
        {(items) =>
          editing ? (
            <>
              <h2>{t("tournaments.edit", { name: editing.name })}</h2>
              <p className="hint">{t("tournaments.editHint")}</p>
              <TournamentEditor
                key={editing.id}
                initial={tournamentForm(editing)}
                disciplines={items}
                submitLabel={t("bot.save")}
                formatFixed
                onSave={save}
                onCancel={() => setEditing(undefined)}
              />
            </>
          ) : (
            <>
              <h2>{t("tournaments.new")}</h2>
              <TournamentEditor
                key={created}
                initial={DEFAULT_TOURNAMENT_FORM}
                disciplines={items}
                submitLabel={t("tournaments.create")}
                onSave={create}
              />
            </>
          )
        }
      </ApiContent>

      <h2>{t("tournaments.title")}</h2>
      <FormError error={error} />
      <ApiContent state={tournaments}>
        {(items) => (
          <TableShell rows={items.length} empty={t("tournaments.empty")}>
            <thead>
              <tr>
                <th>{t("tournaments.name")}</th>
                <th>{t("tournaments.format")}</th>
                <th className="number">{t("tournaments.registered")}</th>
                <th>{t("tournaments.edition")}</th>
                <th>{t("admin.actions")}</th>
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
                  <td className="number">{tournament.registered}</td>
                  <td>
                    <EditionState edition={tournament.edition} />
                  </td>
                  <td className="inline-actions">
                    <button type="button" disabled={pending} onClick={() => setEditing(tournament)}>
                      {t("disciplines.editButton")}
                    </button>
                    {startable(tournament) && (
                      <button
                        type="button"
                        className="primary"
                        disabled={pending}
                        onClick={() => act(() => startTournament(tournament.id))}
                      >
                        {t("leagues.startNow")}
                      </button>
                    )}
                    <button
                      type="button"
                      disabled={pending}
                      onClick={() =>
                        act(() =>
                          updateTournament(tournament.id, { archived: !tournament.archived }),
                        )
                      }
                    >
                      {tournament.archived ? t("disciplines.restore") : t("disciplines.archive")}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </TableShell>
        )}
      </ApiContent>
    </section>
  );
}
