import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { Bot } from "../../api/types";
import { formatDateTime } from "../../format/dateTime";
import { useLocale } from "../../hooks/useLocale";

/**
 * The versions of the name the viewer may see, newest first; the shown one is marked (E95).
 * With play, each other verified version gets a link to set games against it, and the next
 * older one is offered above the table (E160).
 */
export function BotVersions({
  versions,
  current,
  play,
}: {
  versions: Bot[];
  current: string;
  play?: (other: string) => string | null;
}) {
  const { t } = useTranslation();
  const locale = useLocale();
  if (versions.length < 2) return null;
  const link = (bot: Bot) =>
    play && bot.id !== current && bot.status === "verified" ? play(bot.id) : null;
  const older = versions.slice(versions.findIndex((bot) => bot.id === current) + 1);
  const predecessor = older.map(link).find((target) => target !== null);
  return (
    <>
      <h2>{t("bot.versions")}</h2>
      {predecessor && (
        <p>
          <Link to={predecessor}>{t("bot.playPredecessor")}</Link>
        </p>
      )}
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>{t("bots.version")}</th>
              <th>{t("bots.status")}</th>
              <th>{t("bots.created")}</th>
              {play && <th />}
            </tr>
          </thead>
          <tbody>
            {versions.map((bot) => {
              const target = link(bot);
              return (
                <tr key={bot.id}>
                  <td>
                    {bot.id === current ? (
                      <strong aria-current="page">{bot.version}</strong>
                    ) : (
                      <Link to={`/bots/${bot.id}`}>{bot.version}</Link>
                    )}
                  </td>
                  <td>{t(`botStatus.${bot.status}`)}</td>
                  <td>{formatDateTime(bot.created_at, locale)}</td>
                  {play && <td>{target && <Link to={target}>{t("bot.play")}</Link>}</td>}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
