import { useTranslation } from "react-i18next";

import { fetchOwnRating } from "../../api/account";
import { ApiContent } from "../../components/ApiContent";
import { useApi } from "../../hooks/useApi";

/** The rating of the logged-in account (E117); the public ranking shows it too (E118). */
export function OwnRating() {
  const { t } = useTranslation();
  const rating = useApi((signal) => fetchOwnRating(signal), "own-rating");

  return (
    <section>
      <h2>{t("account.rating")}</h2>
      <ApiContent state={rating}>
        {(data) => <p>{t("account.ratingValue", { value: data.value, count: data.games })}</p>}
      </ApiContent>
      <p className="hint">{t("account.ratingHint")}</p>
    </section>
  );
}
