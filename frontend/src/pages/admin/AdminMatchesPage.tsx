import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router";

import { fetchBots, fetchDisciplines } from "../../api/endpoints";
import { ApiContent } from "../../components/ApiContent";
import { useApi } from "../../hooks/useApi";
import { EnqueueForm } from "./EnqueueForm";
import { QueueControl } from "./QueueControl";
import { RecheckLanguage } from "./RecheckLanguage";

export function AdminMatchesPage() {
  const { t } = useTranslation();
  // ?white= and ?black= preset the form, e.g. from a bot page (E160).
  const [params] = useSearchParams();
  const bots = useApi(fetchBots, "bots");
  // Without the list only free times are offered.
  const disciplines = useApi(fetchDisciplines, "disciplines");
  return (
    <>
      <QueueControl />
      <section>
        <h2>{t("admin.enqueueTitle")}</h2>
        <ApiContent state={bots}>
          {(items) => (
            <EnqueueForm
              bots={items}
              disciplines={disciplines.data ?? []}
              white={params.get("white") ?? undefined}
              black={params.get("black") ?? undefined}
            />
          )}
        </ApiContent>
      </section>
      <RecheckLanguage />
    </>
  );
}
