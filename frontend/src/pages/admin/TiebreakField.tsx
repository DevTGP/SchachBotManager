import { useTranslation } from "react-i18next";

import type { Tiebreak } from "../../api/types";
import { TIEBREAKS } from "./leagueForm";

const SLOTS = 4;

/** Up to four tiebreaks in order, each once; the lot comes last anyway (E135). */
export function TiebreakField({
  value,
  onChange,
}: {
  value: Tiebreak[];
  onChange: (value: Tiebreak[]) => void;
}) {
  const { t } = useTranslation();

  function set(slot: number, chosen: string) {
    const next = [...value];
    if (chosen) next[slot] = chosen as Tiebreak;
    else next.splice(slot);
    onChange(next.filter((item, index) => next.indexOf(item) === index));
  }

  const shown = Math.min(value.length + 1, SLOTS);
  return (
    <fieldset>
      <legend>{t("leagues.tiebreaks")}</legend>
      <div className="form-row">
        {Array.from({ length: shown }, (_, slot) => (
          <label key={slot}>
            {t("leagues.tiebreakSlot", { slot: slot + 1 })}
            <select value={value[slot] ?? ""} onChange={(event) => set(slot, event.target.value)}>
              <option value="">{t("common.none")}</option>
              {TIEBREAKS.filter(
                (name) => name === value[slot] || !value.slice(0, slot).includes(name),
              ).map((name) => (
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
