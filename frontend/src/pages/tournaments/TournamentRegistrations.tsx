import { useTranslation } from "react-i18next";

import { deregisterTournamentBot } from "../../api/tournaments";
import type { TournamentRegistration } from "../../api/types";
import { FormError } from "../../components/FormError";
import { SideName } from "../../components/SideName";
import { TableShell } from "../../components/TableShell";
import { formatDateTime } from "../../format/dateTime";
import { useLocale } from "../../hooks/useLocale";
import { useSubmit } from "../../hooks/useSubmit";
import { useSession } from "../../session/sessionContext";

/**
 * The registered bots in the order they came and whether each plays in the running edition;
 * admins may take any of them out, owners do it on the page of their bot (E179).
 */
export function TournamentRegistrations({
  tournamentId,
  registrations,
  onChange,
}: {
  tournamentId: string;
  registrations: TournamentRegistration[];
  onChange: () => void;
}) {
  const { t } = useTranslation();
  const locale = useLocale();
  const { user } = useSession();
  const { pending, error, submit } = useSubmit();
  const isAdmin = user?.role === "admin";

  function deregister(botId: string) {
    void submit(async () => {
      await deregisterTournamentBot(tournamentId, botId);
      onChange();
    });
  }

  return (
    <section>
      <h2>{t("tournaments.registrations")}</h2>
      <FormError error={error} />
      <TableShell rows={registrations.length} empty={t("tournaments.noRegistrations")}>
        <thead>
          <tr>
            <th>{t("bots.name")}</th>
            <th>{t("bots.version")}</th>
            <th>{t("tournaments.playing")}</th>
            <th>{t("leagues.since")}</th>
            {isAdmin && <th>{t("admin.actions")}</th>}
          </tr>
        </thead>
        <tbody>
          {registrations.map((entry) => (
            <tr key={entry.bot.bot_id}>
              <td>
                <SideName side={entry.bot} />
              </td>
              <td>{entry.bot.version ?? "–"}</td>
              <td>{entry.playing ? t("tournaments.inEdition") : t("tournaments.nextEdition")}</td>
              <td>{formatDateTime(entry.created_at, locale)}</td>
              {isAdmin && (
                <td>
                  <button
                    type="button"
                    disabled={pending}
                    onClick={() => deregister(entry.bot.bot_id)}
                  >
                    {t("leagues.deregister")}
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </TableShell>
    </section>
  );
}
