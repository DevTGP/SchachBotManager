import { useTranslation } from "react-i18next";

import type { KnockoutPlacement } from "../../api/types";
import { SideName } from "../../components/SideName";

/** The participants of a knockout edition by place; those still in have none yet (E177). */
export function KnockoutPlacements({ placements }: { placements: KnockoutPlacement[] }) {
  const { t } = useTranslation();
  if (placements.length === 0) return null;
  return (
    <section>
      <h2>{t("editions.placements")}</h2>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>{t("editions.place")}</th>
              <th>{t("bots.name")}</th>
              <th>{t("bots.version")}</th>
            </tr>
          </thead>
          <tbody>
            {placements.map((entry) => (
              <tr key={entry.bot.bot_id}>
                <td>
                  {entry.place ??
                    (entry.withdrawn ? t("outcome.withdrawn") : t("editions.stillIn"))}
                </td>
                <td>
                  <SideName side={entry.bot} />
                </td>
                <td>{entry.bot.version ?? "–"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
