import { useTranslation } from "react-i18next";
import { Link } from "react-router";

/** Anything that names a bot or a player: sides of games, table rows, registrations. */
export interface Named {
  bot_id: string | null;
  name: string;
  version: string | null;
}

/**
 * A side by name, linked to its bot if it has one; the version only as a tooltip, since games
 * show no versions (E165). The dot gives the color when there is one.
 */
export function SideName({ side, color }: { side: Named; color?: "w" | "b" }) {
  const { t } = useTranslation();
  const title = side.version ? t("pairing.version", { version: side.version }) : undefined;
  return (
    <span className="side-name">
      {color && (
        <span
          className={`piece-dot ${color}`}
          role="img"
          aria-label={t(color === "w" ? "viewer.white" : "viewer.black")}
        />
      )}
      {side.bot_id ? (
        <Link className="quiet" to={`/bots/${side.bot_id}`} title={title}>
          {side.name}
        </Link>
      ) : (
        <span title={title}>{side.name}</span>
      )}
    </span>
  );
}
