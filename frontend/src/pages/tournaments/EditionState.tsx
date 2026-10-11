import { useTranslation } from "react-i18next";

import type { EditionSummary } from "../../api/types";

/** "Edition 3 (running)" for the latest edition of a tournament; nothing without one. */
export function EditionState({ edition }: { edition: EditionSummary | null }) {
  const { t } = useTranslation();
  if (edition === null) return null;
  return (
    <>
      {t("tournaments.editionState", {
        number: edition.number,
        status: t(`editionStatus.${edition.status}`),
      })}
    </>
  );
}
