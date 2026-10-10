import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router";

import { fetchAuditEntries } from "../../api/admin";
import type { AuditEntry } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { Pager } from "../../components/Pager";
import { formatDateTime } from "../../format/dateTime";
import { useApi } from "../../hooks/useApi";
import { useLocale } from "../../hooks/useLocale";

const PAGE_SIZE = 25;
const FILTERS = ["actor", "action", "target", "since", "until"] as const;
type Filter = (typeof FILTERS)[number];

/** The audit log with filters in the URL, so every view can be linked (E151). */
export function AdminAuditPage() {
  const { t } = useTranslation();
  const locale = useLocale();
  const [params, setParams] = useSearchParams();
  const filters = Object.fromEntries(
    FILTERS.map((name) => [name, params.get(name) || undefined]),
  ) as Record<Filter, string | undefined>;
  const offset = Math.max(0, Number.parseInt(params.get("offset") ?? "0", 10) || 0);

  const entries = useApi(
    (signal) => fetchAuditEntries({ ...filters, limit: PAGE_SIZE, offset }, signal),
    `${FILTERS.map((name) => filters[name]).join("/")}/${offset}`,
  );

  function update(name: Filter | "offset", value: string | undefined) {
    const next = new URLSearchParams(params);
    if (value) next.set(name, value);
    else next.delete(name);
    if (name !== "offset") next.delete("offset");
    setParams(next);
  }

  const choices = entries.data ?? { actors: [], actions: [] };
  return (
    <section>
      <h2>{t("admin.audit")}</h2>
      <div className="filters">
        <label>
          {t("admin.auditActor")}
          <select
            value={filters.actor ?? ""}
            onChange={(event) => update("actor", event.target.value || undefined)}
          >
            <option value="">{t("admin.auditAll")}</option>
            {withCurrent(choices.actors, filters.actor).map((actor) => (
              <option key={actor} value={actor}>
                {actor}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("admin.auditAction")}
          <select
            value={filters.action ?? ""}
            onChange={(event) => update("action", event.target.value || undefined)}
          >
            <option value="">{t("admin.auditAll")}</option>
            {withCurrent(choices.actions, filters.action).map((action) => (
              <option key={action} value={action}>
                {action}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("admin.auditSince")}
          <input
            type="date"
            value={filters.since ?? ""}
            onChange={(event) => update("since", event.target.value || undefined)}
          />
        </label>
        <label>
          {t("admin.auditUntil")}
          <input
            type="date"
            value={filters.until ?? ""}
            onChange={(event) => update("until", event.target.value || undefined)}
          />
        </label>
        {filters.target && (
          <button type="button" onClick={() => update("target", undefined)}>
            {t("admin.auditClearTarget", { target: filters.target })}
          </button>
        )}
      </div>
      <ApiContent state={entries}>
        {(page) => (
          <>
            {page.items.length === 0 ? (
              <p className="muted">{t("admin.auditEmpty")}</p>
            ) : (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>{t("admin.auditAt")}</th>
                      <th>{t("admin.auditActor")}</th>
                      <th>{t("admin.auditAction")}</th>
                      <th>{t("admin.auditTarget")}</th>
                      <th>{t("admin.auditDetails")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {page.items.map((entry) => (
                      <tr key={entry.id}>
                        <td>{formatDateTime(entry.at, locale)}</td>
                        <td>{entry.actor}</td>
                        <td>
                          <code>{entry.action}</code>
                        </td>
                        <td>
                          {entry.target && (
                            <button
                              type="button"
                              className="link"
                              title={t("admin.auditFilterTarget")}
                              onClick={() => update("target", entry.target ?? undefined)}
                            >
                              {entry.target}
                            </button>
                          )}
                        </td>
                        <td>
                          <code>{detailsText(entry)}</code>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <Pager
              offset={offset}
              limit={PAGE_SIZE}
              total={page.total}
              onChange={(value) => update("offset", value > 0 ? String(value) : undefined)}
            />
          </>
        )}
      </ApiContent>
    </section>
  );
}

/** A filter from a link stays selectable even if the log no longer lists it. */
function withCurrent(values: string[], current: string | undefined): string[] {
  return current && !values.includes(current) ? [...values, current] : values;
}

function detailsText(entry: AuditEntry): string {
  return Object.entries(entry.details)
    .map(([key, value]) => `${key}=${typeof value === "string" ? value : JSON.stringify(value)}`)
    .join(", ");
}
