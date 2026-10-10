import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { fetchLimits } from "../../api/account";
import { fetchOwnBots } from "../../api/bots";
import { fetchBots, fetchDisciplines } from "../../api/endpoints";
import { ApiContent } from "../../components/ApiContent";
import { useApi } from "../../hooks/useApi";
import { OwnBotGroups } from "./OwnBotGroups";
import { OwnMatchForm } from "./OwnMatchForm";

/** "My bots": every own version, the upload and games for own bots (E95, E98, E154). */
export function OwnBotsPage() {
  const { t } = useTranslation();
  const ownBots = useApi(fetchOwnBots, "own-bots");
  const bots = useApi(fetchBots, "bots");
  // Without the list only free times are offered.
  const disciplines = useApi(fetchDisciplines, "disciplines");
  const limits = useApi(fetchLimits, "own-limits");
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
                    />
                  )}
                </ApiContent>
              )}
            </ApiContent>
          )}
        </ApiContent>
      </section>
    </>
  );
}
