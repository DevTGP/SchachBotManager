import { useState } from "react";
import { useTranslation } from "react-i18next";

import { createDiscipline, updateDiscipline } from "../../api/admin";
import { fetchDisciplines } from "../../api/endpoints";
import type { DisciplineRequest, StoredDiscipline } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { FormError } from "../../components/FormError";
import { formatTimeControl } from "../../format/timeControl";
import { useApi } from "../../hooks/useApi";
import { useSubmit } from "../../hooks/useSubmit";
import { DisciplineEditor } from "./DisciplineEditor";
import { DEFAULT_DISCIPLINE_FORM, disciplineForm } from "./disciplineForm";

/** Disciplines: create, change, archive; they are never deleted (E100). */
export function AdminDisciplinesPage() {
  const { t } = useTranslation();
  const disciplines = useApi(fetchDisciplines, "disciplines");
  const { pending, error, submit } = useSubmit();
  const [editing, setEditing] = useState<StoredDiscipline | undefined>();
  // A new key empties the form for the next discipline after a create.
  const [created, setCreated] = useState(0);

  async function create(request: DisciplineRequest) {
    await createDiscipline(request);
    setCreated((count) => count + 1);
    disciplines.reload();
  }

  async function save(request: DisciplineRequest) {
    if (!editing) return;
    await updateDiscipline(editing.id, request);
    setEditing(undefined);
    disciplines.reload();
  }

  function setArchived(discipline: StoredDiscipline, archived: boolean) {
    void submit(async () => {
      await updateDiscipline(discipline.id, { archived });
      disciplines.reload();
    });
  }

  return (
    <section>
      {editing ? (
        <>
          <h2>{t("disciplines.edit", { name: editing.name })}</h2>
          <p className="hint">{t("disciplines.editHint")}</p>
          <DisciplineEditor
            key={editing.id}
            initial={disciplineForm(editing)}
            submitLabel={t("bot.save")}
            onSave={save}
            onCancel={() => setEditing(undefined)}
          />
        </>
      ) : (
        <>
          <h2>{t("disciplines.new")}</h2>
          <DisciplineEditor
            key={created}
            initial={DEFAULT_DISCIPLINE_FORM}
            submitLabel={t("disciplines.create")}
            onSave={create}
          />
        </>
      )}

      <h2>{t("disciplines.title")}</h2>
      <FormError error={error} />
      <ApiContent state={disciplines}>
        {(items) =>
          items.length === 0 ? (
            <p className="muted">{t("disciplines.empty")}</p>
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>{t("disciplines.name")}</th>
                    <th>{t("matchTable.timeControl")}</th>
                    <th className="optional">{t("disciplines.startupSeconds")}</th>
                    <th className="optional">{t("disciplines.toleranceMs")}</th>
                    <th className="optional">{t("admin.maxMoves")}</th>
                    <th>{t("admin.status")}</th>
                    <th>{t("admin.actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((discipline) => (
                    <tr key={discipline.id}>
                      <td>{discipline.name}</td>
                      <td>{formatTimeControl(discipline)}</td>
                      <td className="optional">{discipline.startup_ms / 1000}</td>
                      <td className="optional">{discipline.tolerance_ms}</td>
                      <td className="optional">{discipline.max_moves}</td>
                      <td>
                        {discipline.archived ? t("disciplines.archived") : t("disciplines.inUse")}
                      </td>
                      <td className="inline-actions">
                        <button
                          type="button"
                          disabled={pending}
                          onClick={() => setEditing(discipline)}
                        >
                          {t("disciplines.editButton")}
                        </button>
                        <button
                          type="button"
                          disabled={pending}
                          onClick={() => setArchived(discipline, !discipline.archived)}
                        >
                          {discipline.archived
                            ? t("disciplines.restore")
                            : t("disciplines.archive")}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        }
      </ApiContent>
    </section>
  );
}
