import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";

import type { Match } from "../api/types";
import { formatSpent } from "../format/clock";
import { useLocale } from "../hooks/useLocale";
import { moveRows, type MoveCell } from "./game";

/** SAN with the time spent on each move; a click shows the position after it. */
export function MoveList({
  match,
  ply,
  goTo,
}: {
  match: Match;
  ply: number;
  goTo: (ply: number) => void;
}) {
  const { t } = useTranslation();
  const list = useRef<HTMLDivElement>(null);
  const current = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (list.current && current.current) revealWithin(list.current, current.current);
  }, [ply]);

  function cell(entry: MoveCell | undefined) {
    if (entry === undefined) return <td />;
    const active = entry.ply === ply;
    return (
      <td>
        <MoveButton entry={entry} active={active} goTo={goTo} buttonRef={active ? current : null} />
      </td>
    );
  }

  return (
    <div className="move-list" ref={list}>
      <button
        type="button"
        className="move start"
        aria-current={ply === 0 ? "step" : undefined}
        ref={ply === 0 ? current : null}
        onClick={() => goTo(0)}
      >
        {t("viewer.startPosition")}
      </button>
      {match.moves.length === 0 ? (
        <p className="muted">{t("viewer.noMoves")}</p>
      ) : (
        <table aria-label={t("viewer.moves")}>
          <tbody>
            {moveRows(match).map((row) => (
              <tr key={row.white?.ply ?? row.black?.ply}>
                <th scope="row">{row.number}.</th>
                {cell(row.white)}
                {cell(row.black)}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

/** Scrolls only the list, never the page, so the board stays in view on small screens. */
function revealWithin(container: HTMLElement, item: HTMLElement) {
  const box = container.getBoundingClientRect();
  const rect = item.getBoundingClientRect();
  if (rect.top < box.top) {
    container.scrollTop -= box.top - rect.top;
  } else if (rect.bottom > box.bottom) {
    container.scrollTop += rect.bottom - box.bottom;
  }
}

function MoveButton({
  entry,
  active,
  goTo,
  buttonRef,
}: {
  entry: MoveCell;
  active: boolean;
  goTo: (ply: number) => void;
  buttonRef: React.Ref<HTMLButtonElement> | null;
}) {
  const locale = useLocale();
  return (
    <button
      type="button"
      className="move"
      aria-current={active ? "step" : undefined}
      ref={buttonRef}
      onClick={() => goTo(entry.ply)}
    >
      <span className="san">{entry.move.san}</span>
      <span className="spent">{formatSpent(entry.move.spent_ms, locale)}</span>
    </button>
  );
}
