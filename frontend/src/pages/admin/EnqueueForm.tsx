import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { enqueueMatches } from "../../api/admin";
import type { Bot } from "../../api/types";
import { FormError } from "../../components/FormError";
import { useSubmit } from "../../hooks/useSubmit";
import { DEFAULT_FORM, type MatchForm, matchOrder } from "./matchOrder";

/** Puts games between two bots into the queue (E71, E85). */
export function EnqueueForm({ bots }: { bots: Bot[] }) {
  const { t } = useTranslation();
  const { pending, error, submit } = useSubmit();
  const [queued, setQueued] = useState<number | undefined>(undefined);
  const [form, setForm] = useState<MatchForm>({
    ...DEFAULT_FORM,
    white: bots[0]?.id ?? "",
    black: bots[1]?.id ?? bots[0]?.id ?? "",
  });

  function set<K extends keyof MatchForm>(field: K, value: MatchForm[K]) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setQueued(undefined);
    void submit(async () => {
      const ids = await enqueueMatches(matchOrder(form));
      setQueued(ids.length);
    });
  }

  const botOptions = bots.map((bot) => (
    <option key={bot.id} value={bot.id}>
      {bot.name}
    </option>
  ));

  return (
    <form className="form" onSubmit={onSubmit}>
      <div className="form-row">
        <label>
          {t("viewer.white")}
          <select value={form.white} onChange={(event) => set("white", event.target.value)}>
            {botOptions}
          </select>
        </label>
        <label>
          {t("viewer.black")}
          <select value={form.black} onChange={(event) => set("black", event.target.value)}>
            {botOptions}
          </select>
        </label>
      </div>
      <div className="form-row">
        <NumberField
          label={t("admin.initialSeconds")}
          value={form.initialSeconds}
          step="any"
          onChange={(value) => set("initialSeconds", value)}
        />
        <NumberField
          label={t("admin.incrementSeconds")}
          value={form.incrementSeconds}
          step="any"
          onChange={(value) => set("incrementSeconds", value)}
        />
        <NumberField
          label={t("admin.games")}
          value={form.games}
          onChange={(value) => set("games", value)}
        />
        <NumberField
          label={t("admin.priority")}
          value={form.priority}
          onChange={(value) => set("priority", value)}
        />
        <NumberField
          label={t("admin.maxMoves")}
          value={form.maxMoves}
          onChange={(value) => set("maxMoves", value)}
        />
      </div>
      <label className="checkbox">
        <input
          type="checkbox"
          checked={form.alternate}
          onChange={(event) => set("alternate", event.target.checked)}
        />
        {t("admin.alternate")}
      </label>
      <label>
        {t("admin.startFen")}
        <input
          value={form.startFen}
          placeholder={t("admin.startFenHint")}
          onChange={(event) => set("startFen", event.target.value)}
        />
      </label>
      <FormError error={error} />
      {queued !== undefined && (
        <p role="status">
          {t("admin.queued", { count: queued })} <Link to="/queue">{t("nav.queue")}</Link>
        </p>
      )}
      <button type="submit" className="primary" disabled={pending || bots.length === 0}>
        {t("admin.enqueue")}
      </button>
    </form>
  );
}

function NumberField({
  label,
  value,
  step,
  onChange,
}: {
  label: string;
  value: string;
  step?: string;
  onChange: (value: string) => void;
}) {
  return (
    <label>
      {label}
      <input
        type="number"
        required
        min={0}
        step={step}
        inputMode="decimal"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}
