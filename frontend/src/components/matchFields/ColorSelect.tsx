import { useTranslation } from "react-i18next";

export type Color = "white" | "black";

/** White or black, on /play also a random color. */
export function ColorSelect<T extends Color | "random">({
  label,
  value,
  random = false,
  onChange,
}: {
  label: string;
  value: T;
  random?: boolean;
  onChange: (value: T) => void;
}) {
  const { t } = useTranslation();
  return (
    <label>
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value as T)}>
        {random && <option value="random">{t("play.randomColor")}</option>}
        <option value="white">{t("viewer.white")}</option>
        <option value="black">{t("viewer.black")}</option>
      </select>
    </label>
  );
}
