import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router";

import { fetchLimits } from "../../api/account";
import { fetchOwnBots } from "../../api/bots";
import { fetchBots, fetchDisciplines, fetchMatches } from "../../api/endpoints";
import { ApiContent } from "../../components/ApiContent";
import { useApi } from "../../hooks/useApi";
import { POLL_LIST_MS } from "../../hooks/polling";
import { OwnBotGroups } from "./OwnBotGroups";
import { OwnMatchForm } from "./OwnMatchForm";
import { OwnWaitingMatches } from "./OwnWaitingMatches";

const WAITING_SHOWN = 100;

/**
 * "My bots": every own version, the upload, games for own bots and the games still waiting
 * (E95, E98, E154, E157). ?own= and ?opponent= preset the form, e.g. from a bot page (E160).
 */
export function OwnBotsPage() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const preset = {
    own: params.get("own") ?? undefined,
    opponent: params.get("opponent") ?? undefined,
  };
  const ownBots = useApi(fetchOwnBots, "own-bots");
  const bots = useApi(fetchBots, "bots");
  // Without the list only free times are offered.
  const disciplines = useApi(fetchDisciplines, "disciplines");
  const limits = useApi(fetchLimits, "own-limits");
  const waiting = useApi(
    (signal) => fetchMatches({ mine: true, status: "queued", limit: WAITING_SHOWN }, signal),
    "own-waiting",
    (data) => (data?.items.length ? POLL_LIST_MS : undefined),
  );
  return (
    <>
      <h1>{t("ownBots.title")}</h1>
      <p>
        <Link to="/bots/new">{t("nav.upload")}</Link>
      </p>
      <ApiContent state={ownBots}>{(items) => <OwnBotGroups bots={items} />}</ApiContent>
      <section>
        <h2>{t("ownBots.enqueueTitle")}</h2>
        <ApiContent state={ownBots}>
          {(own) => (
            <ApiContent state={bots}>
              {(opponents) => (
                <ApiContent state={limits}>
                  {(coderLimits) => (
                    <OwnMatchForm
                      own={own.filter((bot) => bot.status === "verified")}
                      opponents={opponents}
                      disciplines={disciplines.data ?? []}
                      limits={coderLimits}
                      preset={preset}
                      onQueued={waiting.reload}
                    />
                  )}
                </ApiContent>
              )}
            </ApiContent>
          )}
        </ApiContent>
      </section>
      <section>
        <h2>{t("ownBots.waitingTitle")}</h2>
        <ApiContent state={waiting}>
          {(page) => <OwnWaitingMatches matches={page.items} onChange={waiting.reload} />}
        </ApiContent>
      </section>
    </>
  );
}
