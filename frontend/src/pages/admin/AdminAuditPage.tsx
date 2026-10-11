import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router";

import { fetchAuditEntries } from "../../api/admin";
import { ApiContent } from "../../components/ApiContent";
import { Pager } from "../../components/Pager";
import { useApi } from "../../hooks/useApi";
import { AuditTable } from "./AuditTable";

const PAGE_SIZE = 25;
const FILTERS = ["actor", "action", "target", "since", "until"] as const;
type Filter = (typeof FILTERS)[number];

/**
 * The audit log with filters in the URL, so every view can be linked (E151); the days count in
 * UTC (U12).
 */
export function AdminAuditPage() {
  const { t } = useTranslation();
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
            {t("admin.auditClearTarget")}
          </button>
        )}
      </div>
      <p className="hint">{t("admin.auditDayHint")}</p>
      <ApiContent state={entries}>
        {(page) => (
          <>
            <AuditTable entries={page.items} onTarget={(target) => update("target", target)} />
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
