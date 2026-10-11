import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import type { MatchSummary } from "../api/types";
import { formatDateTime, formatTime } from "../format/dateTime";
import { formatTimeControl } from "../format/timeControl";
import { useLocale } from "../hooks/useLocale";
import { ActionsHeader, OpenCell } from "./OpenCell";
import { PairingCells, PairingHeader } from "./Pairing";
import { TableShell } from "./TableShell";

/** A game in the queue; the own waiting games of a coder come without place and estimates. */
export interface QueueRow {
  match: MatchSummary;
  position?: number;
  estimated_start?: string;
  estimated_end?: string;
  priority?: number;
}

/**
 * Who looks at the queue (E167): the public sees place and estimated times, admins also change
 * the priority and cancel, coders see when they set their games and take them back.
 */
export type QueueView = "public" | "admin" | "own";

/**
 * The one queue table for every role (E167). Running games have no place; their start is the
 * real one. actions adds the buttons of the role after "Open".
 */
export function QueueTable({
  rows,
  view,
  empty,
  actions,
}: {
  rows: QueueRow[];
  view: QueueView;
  empty: string;
  actions?: (row: QueueRow) => ReactNode;
}) {
  const { t } = useTranslation();
  const locale = useLocale();
  const waiting = rows.filter((row) => row.match.status === "queued").length;
  const placed = view !== "own" && waiting > 0;
  const startHeader =
    waiting === 0
      ? "queue.started"
      : waiting === rows.length
        ? "queue.estimatedStart"
        : "queue.start";
  const estimated = view !== "own";
  return (
    <TableShell rows={rows.length} empty={empty} className={`queue-table queue-${view}`}>
      <thead>
        <tr>
          {placed && <th className="number">{t("queue.position")}</th>}
          <PairingHeader />
          <th>{t("matchTable.timeControl")}</th>
          {estimated && <th>{t(startHeader)}</th>}
          {view === "public" && <th className="optional">{t("queue.estimatedEnd")}</th>}
          {view === "own" && <th className="optional">{t("matchTable.discipline")}</th>}
          {view === "own" && <th>{t("matchTable.date")}</th>}
          <ActionsHeader />
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.match.id}>
            {placed && <td className="number">{row.position || t("queue.runningShort")}</td>}
            <PairingCells match={row.match} />
            <td>{formatTimeControl(row.match.discipline, locale)}</td>
            {estimated && <td>{row.estimated_start && formatTime(row.estimated_start, locale)}</td>}
            {view === "public" && (
              <td className="optional">
                {row.estimated_end && formatTime(row.estimated_end, locale)}
              </td>
            )}
            {view === "own" && (
              <td className="optional">
                {row.match.discipline.discipline_id
                  ? row.match.discipline.name
                  : t("disciplines.freeTimes")}
              </td>
            )}
            {view === "own" && <td>{formatDateTime(row.match.created_at, locale)}</td>}
            <OpenCell matchId={row.match.id}>{actions?.(row)}</OpenCell>
          </tr>
        ))}
      </tbody>
    </TableShell>
  );
}
