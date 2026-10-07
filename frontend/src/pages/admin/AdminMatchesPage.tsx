import { useTranslation } from "react-i18next";

import { fetchBots } from "../../api/endpoints";
import { ApiContent } from "../../components/ApiContent";
import { useApi } from "../../hooks/useApi";
import { EnqueueForm } from "./EnqueueForm";
import { QueueControl } from "./QueueControl";

export function AdminMatchesPage() {
  const { t } = useTranslation();
  const bots = useApi(fetchBots, "bots");
  return (
    <>
      <QueueControl />
      <section>
        <h2>{t("admin.enqueueTitle")}</h2>
        <ApiContent state={bots}>{(items) => <EnqueueForm bots={items} />}</ApiContent>
      </section>
    </>
  );
}
