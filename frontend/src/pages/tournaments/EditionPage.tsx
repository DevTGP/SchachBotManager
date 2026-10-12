import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";

import { fetchEdition } from "../../api/tournaments";
import type { Edition } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { formatDateTime } from "../../format/dateTime";
import { disciplineLabel } from "../../format/timeControl";
import { POLL_LIST_MS } from "../../hooks/polling";
import { useApi } from "../../hooks/useApi";
import { useLocale } from "../../hooks/useLocale";
import { EditionNeighbours } from "./EditionNeighbours";
import { EditionParticipants } from "./EditionParticipants";
import { EditionRoundsSection } from "./EditionRoundsSection";
import { EditionTable } from "./EditionTable";
import { KnockoutBracket } from "./KnockoutBracket";
import { KnockoutPlacements } from "./KnockoutPlacements";
import { TournamentFacts } from "./TournamentFacts";

/**
 * An edition with the settings of its start and its table and rounds or its bracket (E180), with
 * the editions before and after it (E188).
 */
export function EditionPage() {
  const { t } = useTranslation();
  const locale = useLocale();
  const { id = "" } = useParams();
  const edition = useApi(
    (signal) => fetchEdition(id, signal),
    `edition:${id}`,
    (data: Edition | undefined) => (data?.status === "running" ? POLL_LIST_MS : undefined),
  );
  return (
    <ApiContent state={edition}>
      {(data) => {
        const running = data.status === "running";
        const knockout = data.settings?.format === "knockout";
        return (
          <>
            <h1>
              {t("editions.title", { tournament: data.tournament_name, number: data.number })}
            </h1>
            <p>
              <Link to={`/tournaments/${data.tournament_id}`}>{t("editions.toTournament")}</Link>
            </p>
            <EditionNeighbours tournamentId={data.tournament_id} number={data.number} />
            <p className="muted">
              {t(`editionStatus.${data.status}`)}
              {data.started_at &&
                ` · ${t("seasons.started", { at: formatDateTime(data.started_at, locale) })}`}
              {data.finished_at &&
                ` · ${t("seasons.finished", { at: formatDateTime(data.finished_at, locale) })}`}
            </p>
            {data.settings && data.discipline ? (
              <TournamentFacts
                settings={data.settings}
                discipline={disciplineLabel(data.discipline, locale)}
                tiebreakDiscipline={
                  data.tiebreak_discipline && disciplineLabel(data.tiebreak_discipline, locale)
                }
              />
            ) : (
              <p className="muted">{t("editions.notStarted")}</p>
            )}
            {data.settings && (
              <p className="muted">
                {t("seasons.progress", { finished: data.finished, games: data.games })}{" "}
                <Link to={`/matches?edition=${data.id}`}>{t("editions.games")}</Link>
              </p>
            )}
            {knockout ? (
              <>
                <KnockoutPlacements placements={data.placements} />
                <KnockoutBracket duels={data.bracket} />
              </>
            ) : (
              data.settings && (
                <>
                  <EditionTable
                    rows={data.table}
                    swiss={data.settings.format === "swiss"}
                    buchholz={data.settings.tiebreaks.includes("buchholz")}
                  />
                  <EditionRoundsSection editionId={data.id} running={running} />
                </>
              )
            )}
            <EditionParticipants participants={data.participants} />
          </>
        );
      }}
    </ApiContent>
  );
}
