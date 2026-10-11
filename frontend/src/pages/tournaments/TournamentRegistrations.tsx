import { useTranslation } from "react-i18next";

import { deregisterTournamentParticipant } from "../../api/tournaments";
import { participantId } from "../../api/participants";
import type { TournamentRegistration } from "../../api/types";
import { FormError } from "../../components/FormError";
import { SideName } from "../../components/SideName";
import { TableShell } from "../../components/TableShell";
import { formatDateTime } from "../../format/dateTime";
import { useLocale } from "../../hooks/useLocale";
import { useSubmit } from "../../hooks/useSubmit";
import { useSession } from "../../session/sessionContext";

/**
 * The registered bots and accounts in the order they came and whether each plays in the
 * running edition; admins may take any of them out, an account itself, owners do it on the page
 * of their bot (E179, E182).
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
  // Admins take anyone out, an account itself as well (E182); owners do it on the bot page.
  const mayDeregister = (entry: { bot: { user_id: string | null } }) =>
    isAdmin || (user != null && entry.bot.user_id === user.id);
  const actions = isAdmin || registrations.some(mayDeregister);

  function deregister(participant: string) {
    void submit(async () => {
      await deregisterTournamentParticipant(tournamentId, participant);
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
            {actions && <th>{t("admin.actions")}</th>}
          </tr>
        </thead>
        <tbody>
          {registrations.map((entry) => (
            <tr key={participantId(entry.bot)}>
              <td>
                <SideName side={entry.bot} />
              </td>
              <td>{entry.bot.version ?? "–"}</td>
              <td>{entry.playing ? t("tournaments.inEdition") : t("tournaments.nextEdition")}</td>
              <td>{formatDateTime(entry.created_at, locale)}</td>
              {actions && (
                <td>
                  {mayDeregister(entry) && (
                    <button
                      type="button"
                      disabled={pending}
                      onClick={() => deregister(participantId(entry.bot))}
                    >
                      {t("leagues.deregister")}
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </TableShell>
    </section>
  );
}
