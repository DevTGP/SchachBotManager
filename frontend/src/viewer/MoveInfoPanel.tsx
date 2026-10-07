import { useTranslation } from "react-i18next";

import type { MoveInfo } from "../api/types";
import type { Color } from "../chess/fen";
import { formatScore } from "../format/score";
import { useLocale } from "../hooks/useLocale";

/** What the bot reported about the shown move (E33); display only. */
export function MoveInfoPanel({ info, mover }: { info: MoveInfo | null; mover: Color }) {
  const { t } = useTranslation();
  const locale = useLocale();
  if (info === null) return <p className="muted">{t("viewer.noInfo")}</p>;
  const score = formatScore(info, mover);
  const depth =
    info.depth === undefined
      ? undefined
      : `${info.depth}${info.seldepth === undefined ? "" : `/${info.seldepth}`}`;
  const rows: [string, string | undefined][] = [
    [t("viewer.score"), score],
    [t("viewer.depth"), depth],
    [t("viewer.nodes"), info.nodes?.toLocaleString(locale)],
    [t("viewer.pv"), info.pv?.join(" ")],
  ];
  const shown = rows.filter((row): row is [string, string] => row[1] !== undefined);
  return (
    <>
      {shown.length > 0 && (
        <dl className="details">
          {shown.map(([term, value]) => (
            <div key={term}>
              <dt>{term}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      )}
      {info.text && <p className="info-text">{info.text}</p>}
    </>
  );
}
