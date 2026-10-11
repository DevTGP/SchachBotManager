import { useTranslation } from "react-i18next";

import { ExploreLinks } from "../components/ExploreLinks";

/** An address without a page: what may have happened and where to go on (G11). */
export function NotFoundPage() {
  const { t } = useTranslation();
  return (
    <>
      <h1>{t("notFound.title")}</h1>
      <p>{t("notFound.text")}</p>
      <ExploreLinks />
    </>
  );
}
