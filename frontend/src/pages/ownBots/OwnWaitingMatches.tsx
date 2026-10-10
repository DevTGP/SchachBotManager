import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { withdrawOwnMatch } from "../../api/bots";
import type { MatchSummary } from "../../api/types";
import { FormError } from "../../components/FormError";
import { playersLabel } from "../../format/botLabel";
import { formatTimeControl } from "../../format/timeControl";
import { useSubmit } from "../../hooks/useSubmit";

/** The account's games that still wait; each can be taken back until it starts (E157). */
export function OwnWaitingMatches({
  matches,
  onChange,
}: {
  matches: MatchSummary[];
  onChange: () => void;
}) {
  const { t } = useTranslation();
  const { pending, error, submit } = useSubmit();
  if (matches.length === 0) return <p className="muted">{t("ownBots.noWaiting")}</p>;

  function withdraw(matchId: string) {
    void submit(async () => {
      await withdrawOwnMatch(matchId);
      onChange();
    });
  }

  return (
    <>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>{t("matchTable.players")}</th>
              <th>{t("matchTable.timeControl")}</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {matches.map((match) => (
              <tr key={match.id}>
                <td>
                  <Link to={`/matches/${match.id}`}>{playersLabel(match)}</Link>
                </td>
                <td>{formatTimeControl(match.discipline)}</td>
                <td>
                  <button type="button" disabled={pending} onClick={() => withdraw(match.id)}>
                    {t("ownBots.withdraw")}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <FormError error={error} />
    </>
  );
}
