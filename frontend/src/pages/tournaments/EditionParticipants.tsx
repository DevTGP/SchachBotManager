import { useTranslation } from "react-i18next";

import type { EditionParticipant } from "../../api/types";
import { SideName } from "../../components/SideName";

/** The participants by seed with the rating they were seeded by (E173). */
export function EditionParticipants({ participants }: { participants: EditionParticipant[] }) {
  const { t } = useTranslation();
  if (participants.length === 0) return null;
  return (
    <section>
      <h2>{t("editions.participants")}</h2>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th className="number">{t("editions.seed")}</th>
              <th>{t("bots.name")}</th>
              <th>{t("bots.version")}</th>
              <th className="number">{t("editions.rating")}</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {participants.map((entry) => (
              <tr key={entry.bot.bot_id}>
                <td className="number">{entry.seed}</td>
                <td>
                  <SideName side={entry.bot} />
                </td>
                <td>{entry.bot.version ?? "–"}</td>
                <td className="number">{Math.round(entry.rating)}</td>
                <td>{entry.withdrawn ? t("outcome.withdrawn") : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
