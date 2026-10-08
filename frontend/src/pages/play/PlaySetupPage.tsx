import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";

import { fetchBots, fetchDisciplines } from "../../api/endpoints";
import { startGame } from "../../api/play";
import type { Bot, PlayRequest, StoredDiscipline } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { DisciplineSelect } from "../../components/DisciplineSelect";
import { FormError } from "../../components/FormError";
import { NumberField } from "../../components/NumberField";
import { botLabel } from "../../format/botLabel";
import { useApi } from "../../hooks/useApi";
import { useSubmit } from "../../hooks/useSubmit";
import { saveSeat } from "../../play/seats";

// Free times up to 30 min + 30 s (E115).
const MAX_MINUTES = 30;
const MAX_INCREMENT_SECONDS = 30;

interface SetupForm {
  bot: string;
  color: PlayRequest["color"];
  discipline: string;
  minutes: string;
  incrementSeconds: string;
}

/** Choose a verified bot, a color and the time, then play in the browser (E11, E114). */
export function PlaySetupPage() {
  const { t } = useTranslation();
  const bots = useApi((signal) => fetchBots(signal), "bots");
  const disciplines = useApi((signal) => fetchDisciplines(signal), "disciplines");
  return (
    <>
      <h1>{t("play.title")}</h1>
      <p>{t("play.intro")}</p>
      <ApiContent state={bots}>
        {(list) => <SetupForm bots={list} disciplines={disciplines.data ?? []} />}
      </ApiContent>
    </>
  );
}

function SetupForm({ bots, disciplines }: { bots: Bot[]; disciplines: StoredDiscipline[] }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { pending, error, submit } = useSubmit();
  const [form, setForm] = useState<SetupForm>({
    bot: bots.find((bot) => bot.builtin)?.id ?? bots[0]?.id ?? "",
    color: "random",
    discipline: "",
    minutes: "5",
    incrementSeconds: "3",
  });

  if (bots.length === 0) return <p className="muted">{t("play.noBots")}</p>;

  function set<K extends keyof SetupForm>(field: K, value: SetupForm[K]) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void submit(async () => {
      const times = form.discipline
        ? { discipline_id: form.discipline }
        : {
            initial_time_ms: Math.round(Number(form.minutes) * 60_000),
            increment_ms: Math.round(Number(form.incrementSeconds) * 1000),
          };
      const seat = await startGame({ bot_id: form.bot, color: form.color, ...times });
      saveSeat(seat.match_id, seat.seat);
      await navigate(`/play/${seat.match_id}`);
    });
  }

  return (
    <form className="form" onSubmit={onSubmit}>
      <div className="form-row">
        <label>
          {t("play.opponent")}
          <select value={form.bot} onChange={(event) => set("bot", event.target.value)}>
            {bots.map((bot) => (
              <option key={bot.id} value={bot.id}>
                {botLabel(bot)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("play.color")}
          <select
            value={form.color}
            onChange={(event) => set("color", event.target.value as SetupForm["color"])}
          >
            <option value="random">{t("play.randomColor")}</option>
            <option value="white">{t("viewer.white")}</option>
            <option value="black">{t("viewer.black")}</option>
          </select>
        </label>
      </div>
      <div className="form-row">
        <DisciplineSelect
          disciplines={disciplines}
          value={form.discipline}
          onChange={(value) => set("discipline", value)}
        />
        {!form.discipline && (
          <>
            <NumberField
              label={t("play.minutes")}
              value={form.minutes}
              step="any"
              min={0.5}
              max={MAX_MINUTES}
              onChange={(value) => set("minutes", value)}
            />
            <NumberField
              label={t("admin.incrementSeconds")}
              value={form.incrementSeconds}
              step="any"
              max={MAX_INCREMENT_SECONDS}
              onChange={(value) => set("incrementSeconds", value)}
            />
          </>
        )}
      </div>
      <p className="hint">{t("play.limits")}</p>
      <FormError error={error} rules="playError" />
      <button type="submit" className="primary" disabled={pending}>
        {t("play.start")}
      </button>
    </form>
  );
}
