import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { fetchMatches } from "../api/endpoints";
import { ApiContent } from "../components/ApiContent";
import { MatchTable } from "../components/MatchTable";
import { useApi } from "../hooks/useApi";
import { POLL_LIST_MS } from "../hooks/polling";

const SHOWN = 10;

export function StartPage() {
  const { t } = useTranslation();
  const running = useApi(
    (signal) => fetchMatches({ status: "running", limit: SHOWN }, signal),
    "running",
    POLL_LIST_MS,
  );
  const recent = useApi(
    (signal) => fetchMatches({ status: "finished", limit: SHOWN }, signal),
    "finished",
    POLL_LIST_MS,
  );
  return (
    <>
      <h1>{t("app.name")}</h1>
      <p>{t("start.intro")}</p>
      <section>
        <h2>{t("start.running")}</h2>
        <ApiContent state={running}>
          {(page) => <MatchTable matches={page.items} empty={t("start.noRunning")} />}
        </ApiContent>
      </section>
      <section>
        <h2>{t("start.recent")}</h2>
        <ApiContent state={recent}>
          {(page) => <MatchTable matches={page.items} empty={t("start.noRecent")} />}
        </ApiContent>
        <p>
          <Link to="/matches">{t("start.allMatches")}</Link>
        </p>
      </section>
    </>
  );
}
