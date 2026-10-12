import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { createLeague, startLeague, updateLeague } from "../../api/admin";
import { fetchDisciplines } from "../../api/endpoints";
import { fetchLeagues } from "../../api/leagues";
import type { League, LeagueRequest, LeagueUpdate } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { FormError } from "../../components/FormError";
import { TableShell } from "../../components/TableShell";
import { useApi } from "../../hooks/useApi";
import { useSubmit } from "../../hooks/useSubmit";
import { SeasonState } from "../leagues/SeasonState";
import { DEFAULT_LEAGUE_FORM, leagueForm } from "./leagueForm";
import { startable } from "./startable";
import { LeagueEditor } from "./LeagueEditor";

/** Leagues: create, change, start the planned season, archive; never deleted (E131, E171). */
export function AdminLeaguesPage() {
  const { t } = useTranslation();
  const leagues = useApi(fetchLeagues, "leagues");
  const disciplines = useApi(fetchDisciplines, "disciplines");
  const { pending, error, submit } = useSubmit();
  const [editing, setEditing] = useState<League | undefined>();
  // A new key empties the form for the next league after a create.
  const [created, setCreated] = useState(0);

  async function create(request: LeagueRequest) {
    await createLeague(request);
    setCreated((count) => count + 1);
    leagues.reload();
  }

  async function save(request: LeagueRequest) {
    if (!editing) return;
    const change: LeagueUpdate = { ...request };
    // An archived discipline may stay, but not be set again.
    if (change.discipline_id === editing.discipline_id) delete change.discipline_id;
    await updateLeague(editing.id, change);
    setEditing(undefined);
    leagues.reload();
  }

  function act(action: () => Promise<unknown>) {
    void submit(async () => {
      await action();
      leagues.reload();
    });
  }

  return (
    <section>
      <ApiContent state={disciplines}>
        {(items) =>
          editing ? (
            <>
              <h2>{t("leagues.edit", { name: editing.name })}</h2>
              <p className="hint">{t("leagues.editHint")}</p>
              <LeagueEditor
                key={editing.id}
                initial={leagueForm(editing)}
                disciplines={items}
                submitLabel={t("bot.save")}
                onSave={save}
                onCancel={() => setEditing(undefined)}
              />
            </>
          ) : (
            <>
              <h2>{t("leagues.new")}</h2>
              <LeagueEditor
                key={created}
                initial={DEFAULT_LEAGUE_FORM}
                disciplines={items}
                submitLabel={t("leagues.create")}
                onSave={create}
              />
            </>
          )
        }
      </ApiContent>

      <h2>{t("leagues.title")}</h2>
      <FormError error={error} />
      <ApiContent state={leagues}>
        {(items) => (
          <TableShell rows={items.length} empty={t("leagues.empty")}>
            <thead>
              <tr>
                <th>{t("leagues.name")}</th>
                <th>{t("leagues.discipline")}</th>
                <th className="number">{t("leagues.registered")}</th>
                <th>{t("leagues.season")}</th>
                <th>{t("admin.actions")}</th>
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
                  <td className="number">{league.registered}</td>
                  <td>
                    <SeasonState season={league.season} />
                  </td>
                  <td className="inline-actions">
                    <button type="button" disabled={pending} onClick={() => setEditing(league)}>
                      {t("disciplines.editButton")}
                    </button>
                    {startable(league) && (
                      <button
                        type="button"
                        className="primary"
                        disabled={pending}
                        onClick={() => act(() => startLeague(league.id))}
                      >
                        {t("leagues.startNow")}
                      </button>
                    )}
                    <button
                      type="button"
                      disabled={pending}
                      onClick={() =>
                        act(() => updateLeague(league.id, { archived: !league.archived }))
                      }
                    >
                      {league.archived ? t("disciplines.restore") : t("disciplines.archive")}
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
