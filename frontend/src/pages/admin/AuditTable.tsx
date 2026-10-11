import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { AuditEntry } from "../../api/types";
import { TableShell } from "../../components/TableShell";
import { formatDateTime } from "../../format/dateTime";
import { useLocale } from "../../hooks/useLocale";

/** Kinds of targets with a page of their own. */
const PAGES: Partial<Record<NonNullable<AuditEntry["target_kind"]>, string>> = {
  bot: "/bots",
  match: "/matches",
  league: "/leagues",
};

/** The entries of the audit log: targets by name, details as a list (U13, E169). */
export function AuditTable({
  entries,
  onTarget,
}: {
  entries: AuditEntry[];
  onTarget: (target: string) => void;
}) {
  const { t } = useTranslation();
  const locale = useLocale();
  return (
    <TableShell rows={entries.length} empty={t("admin.auditEmpty")}>
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
        {entries.map((entry) => (
          <tr key={entry.id}>
            <td>{formatDateTime(entry.at, locale)}</td>
            <td>{entry.actor}</td>
            <td>
              <code>{entry.action}</code>
            </td>
            <td>
              <AuditTarget entry={entry} onTarget={onTarget} />
            </td>
            <td>
              <AuditDetails details={entry.details} />
            </td>
          </tr>
        ))}
      </tbody>
    </TableShell>
  );
}

function AuditTarget({
  entry,
  onTarget,
}: {
  entry: AuditEntry;
  onTarget: (target: string) => void;
}) {
  const { t } = useTranslation();
  const { target, target_kind: kind, target_label: label } = entry;
  if (target === null) return null;
  const page = kind ? PAGES[kind] : undefined;
  const name = label ?? <code className="info-text">{target}</code>;
  return (
    <span className="audit-target">
      {kind && <span className="muted small">{t(`admin.auditKind.${kind}`)}</span>}
      {page && label ? <Link to={`${page}/${target}`}>{label}</Link> : <span>{name}</span>}
      <button
        type="button"
        className="small"
        title={t("admin.auditFilterTarget")}
        onClick={() => onTarget(target)}
      >
        {t("admin.auditFilter")}
      </button>
    </span>
  );
}

function AuditDetails({ details }: { details: AuditEntry["details"] }) {
  const fields = Object.entries(details);
  if (fields.length === 0) return null;
  return (
    <dl className="details small">
      {fields.map(([key, value]) => (
        <div key={key}>
          <dt>{key}</dt>
          <dd>{typeof value === "string" ? value : JSON.stringify(value)}</dd>
        </div>
      ))}
    </dl>
  );
}
