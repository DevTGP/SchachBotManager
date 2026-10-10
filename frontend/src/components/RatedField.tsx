import { useTranslation } from "react-i18next";

/** The wish for a rated game; the API rates it only where E100 and E103 allow (E158). */
export function RatedField({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  const { t } = useTranslation();
  return (
    <>
      <label className="checkbox">
        <input
          type="checkbox"
          checked={checked}
          onChange={(event) => onChange(event.target.checked)}
        />
        {t("matchForm.rated")}
      </label>
      <p className="hint">{t("disciplines.ratedHint")}</p>
    </>
  );
}
