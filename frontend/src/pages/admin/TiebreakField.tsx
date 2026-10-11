import { useTranslation } from "react-i18next";

/** Tiebreaks in order, each option at most once; the lot comes last anyway (E135, E177). */
export function TiebreakField<T extends string>({
  options,
  value,
  onChange,
}: {
  options: readonly T[];
  value: T[];
  onChange: (value: T[]) => void;
}) {
  const { t } = useTranslation();

  function set(slot: number, chosen: string) {
    const next = [...value];
    if (chosen) next[slot] = chosen as T;
    else next.splice(slot);
    onChange(next.filter((item, index) => next.indexOf(item) === index));
  }

  const shown = Math.min(value.length + 1, options.length);
  return (
    <fieldset>
      <legend>{t("leagues.tiebreaks")}</legend>
      <div className="form-row">
        {Array.from({ length: shown }, (_, slot) => (
          <label key={slot}>
            {t("leagues.tiebreakSlot", { slot: slot + 1 })}
            <select value={value[slot] ?? ""} onChange={(event) => set(slot, event.target.value)}>
              <option value="">{t("common.none")}</option>
              {options
                .filter((name) => name === value[slot] || !value.slice(0, slot).includes(name))
                .map((name) => (
                  <option key={name} value={name}>
                    {t(`tiebreak.${name}`)}
                  </option>
                ))}
            </select>
          </label>
        ))}
      </div>
      <p className="hint">{t("leagues.lotHint")}</p>
    </fieldset>
  );
}
