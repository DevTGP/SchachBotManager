import { useTranslation } from "react-i18next";

import type { StoredDiscipline } from "../../api/types";
import { DisciplineSelect } from "../DisciplineSelect";
import { NumberField } from "../NumberField";
import { RatedField } from "../RatedField";
import { StartPositionField } from "../StartPositionField";
import type { MatchConditions, MatchFieldsVariant } from "./conditions";

/** Upper bounds the form shows; the API checks them anyway. */
export interface MatchFieldLimits {
  initial?: number;
  incrementSeconds?: number;
  games?: number;
}

const MIN_INITIAL: Record<MatchFieldsVariant, number> = { admin: 0, coder: 1, play: 0.5 };

/**
 * The fields after the choice of bots, shared by the admin queue, the coder form and /play
 * (E167): discipline or free times, then games, priority, start position and rating as the
 * variant allows.
 */
export function MatchFields({
  variant,
  disciplines,
  form,
  limits = {},
  onChange,
}: {
  variant: MatchFieldsVariant;
  disciplines: StoredDiscipline[];
  form: MatchConditions;
  limits?: MatchFieldLimits;
  onChange: (patch: Partial<MatchConditions>) => void;
}) {
  const { t } = useTranslation();
  const series = variant !== "play";
  return (
    <>
      <div className="form-row">
        <DisciplineSelect
          disciplines={disciplines}
          value={form.discipline}
          onChange={(discipline) => onChange({ discipline })}
        />
        {!form.discipline && (
          <>
            <NumberField
              label={t(variant === "play" ? "play.minutes" : "admin.initialSeconds")}
              value={form.initial}
              step="any"
              min={MIN_INITIAL[variant]}
              max={limits.initial}
              onChange={(initial) => onChange({ initial })}
            />
            <NumberField
              label={t("admin.incrementSeconds")}
              value={form.incrementSeconds}
              step="any"
              max={limits.incrementSeconds}
              onChange={(incrementSeconds) => onChange({ incrementSeconds })}
            />
            {variant === "admin" && (
              <NumberField
                label={t("admin.maxMoves")}
                value={form.maxMoves}
                onChange={(maxMoves) => onChange({ maxMoves })}
              />
            )}
          </>
        )}
      </div>
      {series && (
        <div className="form-row">
          <NumberField
            label={t("admin.games")}
            value={form.games}
            min={1}
            max={limits.games}
            onChange={(games) => onChange({ games })}
          />
          {variant === "admin" && (
            <NumberField
              label={t("admin.priority")}
              value={form.priority}
              onChange={(priority) => onChange({ priority })}
            />
          )}
        </div>
      )}
      {series && (
        <label className="checkbox">
          <input
            type="checkbox"
            checked={form.alternate}
            onChange={(event) => onChange({ alternate: event.target.checked })}
          />
          {t("admin.alternate")}
        </label>
      )}
      {series && (
        <StartPositionField value={form.startFen} onChange={(startFen) => onChange({ startFen })} />
      )}
      {series && <RatedField checked={form.rated} onChange={(rated) => onChange({ rated })} />}
    </>
  );
}
