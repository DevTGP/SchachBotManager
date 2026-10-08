import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { fetchPlaySettings, updatePlaySettings } from "../../api/admin";
import type { PlaySettings } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { FormError } from "../../components/FormError";
import { NumberField } from "../../components/NumberField";
import { useApi } from "../../hooks/useApi";
import { useSubmit } from "../../hooks/useSubmit";

const FIELDS = [
  { name: "max_games", min: 1, max: 16 },
  { name: "games_per_client", min: 1, max: 4 },
  { name: "games_per_day", min: 1, max: 1000 },
] as const;

/** The limits of games against people and remote bots (E115). */
export function AdminPlayPage() {
  const settings = useApi((signal) => fetchPlaySettings(signal), "play-settings");
  return <ApiContent state={settings}>{(data) => <PlaySettingsForm initial={data} />}</ApiContent>;
}

function PlaySettingsForm({ initial }: { initial: PlaySettings }) {
  const { t } = useTranslation();
  const { pending, error, submit } = useSubmit();
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState<Record<keyof PlaySettings, string>>({
    max_games: String(initial.max_games),
    games_per_client: String(initial.games_per_client),
    games_per_day: String(initial.games_per_day),
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSaved(false);
    void submit(async () => {
      await updatePlaySettings({
        max_games: Number(form.max_games),
        games_per_client: Number(form.games_per_client),
        games_per_day: Number(form.games_per_day),
      });
      setSaved(true);
    });
  }

  return (
    <form className="form" onSubmit={onSubmit}>
      <p className="hint">{t("adminPlay.intro")}</p>
      <div className="form-row">
        {FIELDS.map(({ name, min, max }) => (
          <NumberField
            key={name}
            label={t(`adminPlay.${name}`)}
            value={form[name]}
            min={min}
            max={max}
            onChange={(value) => setForm((current) => ({ ...current, [name]: value }))}
          />
        ))}
      </div>
      <FormError error={error} />
      {saved && <p role="status">{t("adminPlay.saved")}</p>}
      <button type="submit" className="primary" disabled={pending}>
        {t("adminPlay.save")}
      </button>
    </form>
  );
}
